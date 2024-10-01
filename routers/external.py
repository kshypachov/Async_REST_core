# routers/external.py
import sqlalchemy
from fastapi import APIRouter, Depends, HTTPException, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from models.models import request_table, person_table
from schemas.schemas import RequestCreate, RequestUpdate, PersonInfoUpdate, RequestStatusEnum
from database.database import get_db
from typing import Optional
from sqlalchemy import insert
from datetime import date
import uuid

#router = APIRouter()
# Приложение FastAPI для внешних пользователей с документацией по адресу /external/docs
external = FastAPI(docs_url="/docs", openapi_url="/openapi.json")

@external.post("/request/")
async def create_request(person: RequestCreate, db: AsyncSession = Depends(get_db)):
    request_id = str(uuid.uuid4())

    # Преобразование данных Pydantic модели в словарь
    person_data_dict = person.dict(exclude_unset=True)

    # Преобразуем объекты date в строку формата 'YYYY-MM-DD'
    for key, value in person_data_dict.get('person_data', {}).items():
        if isinstance(value, date):
            person_data_dict['person_data'][key] = value.isoformat()

    # Создание заявки с преобразованными данными
    query = insert(request_table).values(
        UUID=request_id,
        person_data=person_data_dict['person_data'],  # Преобразованные данные
        comment=person_data_dict.get('comment', "")
    )

    await db.execute(query)
    await db.commit()
    return {"request UUID": request_id}

# Получение статуса заявки
@external.get("/request/{request_id}", response_model=dict)
async def get_request_status(request_id: str, db: AsyncSession = Depends(get_db)):
    query = sqlalchemy.select(request_table.c.status, request_table.c.UUID).where(request_table.c.UUID == request_id)
    result = await db.execute(query)
    request_data = result.fetchone()

    if request_data is None:
        raise HTTPException(status_code=404, detail="Request not found")

    # Преобразуем объект Row в словарь с помощью ._mapping
    return dict(request_data._mapping)

# Получение найденной информации о человеке по заявке
@external.get("/request/{request_id}/found_person", response_model=dict)
async def get_found_person(request_id: str, db: AsyncSession = Depends(get_db)):
    # Ищем заявку с указанным UUID и статусом "completed"
    query = request_table.select().where(
        (request_table.c.UUID == request_id) &
        (request_table.c.status == RequestStatusEnum.completed)
    )
    result = await db.execute(query)
    request_data = result.fetchone()

    # Если заявка не найдена или статус не "completed"
    if request_data is None:
        raise HTTPException(status_code=404, detail="Request not found")

    # Если заявка уже была загружена (поле downloaded == True)
    if request_data._mapping["downloaded"]:
        raise HTTPException(status_code=409, detail="Request already downloaded")

    # Ищем данные о персоне, связанные с заявкой
    person_query = person_table.select().where(person_table.c.id == request_data._mapping["found_person_id"])
    person_result = await db.execute(person_query)
    person_data = person_result.fetchone()

    # Если данные о персоне не найдены
    if person_data is None:
        raise HTTPException(status_code=404, detail="Person not found")

    # Обновляем поле downloaded, помечаем как загруженную
    update_query = request_table.update().where(request_table.c.UUID == request_id).values(downloaded=True)
    await db.execute(update_query)
    await db.commit()

    # Преобразуем данные о персоне в словарь и исключаем поле "id"
    person_dict = dict(person_data._mapping)
    person_dict.pop("id", None)

    # Возвращаем данные о персоне
    return person_dict
