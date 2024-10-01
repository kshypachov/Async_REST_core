# routers/internal.py
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
# Приложение FastAPI для внутренних пользователей с документацией по адресу /internal/docs
internal = FastAPI(docs_url="/docs", openapi_url="/openapi.json")

# Обновление статуса заявки
@internal.put("/request/{request_id}", response_model=dict)
async def update_request(request_id: str, request_update: RequestUpdate, db: AsyncSession = Depends(get_db)):
    # Преобразуем данные модели в словарь, исключая unset поля
    update_data = request_update.dict(exclude_unset=True)

    # Выполняем обновление только с переданными полями
    query = request_table.update().where(request_table.c.UUID == request_id).values(**update_data)
    await db.execute(query)
    await db.commit()

    return {"message": "Request updated"}

# Ввод найденной информации о человеке по заявке
@internal.post("/request/{request_id}/found_person", response_model=dict)
async def add_found_person(request_id: str, person_info: PersonInfoUpdate, db: AsyncSession = Depends(get_db)):
    query = request_table.select().where(request_table.c.UUID == request_id)
    result = await db.execute(query)
    request_exists = result.fetchone()
    if not request_exists:
        raise HTTPException(status_code=404, detail="Request not found")

    person_query = person_table.insert().values(**person_info.dict(exclude_unset=True))
    result = await db.execute(person_query)
    person_id = result.inserted_primary_key[0]

    update_query = request_table.update().where(request_table.c.UUID == request_id).values(found_person_id=person_id)
    await db.execute(update_query)
    await db.commit()
    return {"person_id": person_id}

# Получение всех заявок на поиск информации
@internal.get("/requests/", response_model=list)
async def get_all_requests(
    status: Optional[RequestStatusEnum] = None,
    comment: Optional[str] = None,
    downloaded: Optional[bool] = None,
    UUID: Optional[str] = None,
    person_data: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    # Базовый запрос
    query = request_table.select()

    # Добавляем фильтрацию по каждому параметру, если он передан
    if status is not None:
        query = query.where(request_table.c.status == status)
    if comment is not None:
        query = query.where(request_table.c.comment.ilike(f"%{comment}%"))  # Поиск по части комментария
    if downloaded is not None:
        query = query.where(request_table.c.downloaded == downloaded)
    if UUID is not None:
        query = query.where(request_table.c.UUID == UUID)
    if person_data is not None:
        query = query.where(request_table.c.person_data.contains(person_data))  # Поиск по JSON-полю

    result = await db.execute(query)
    requests = result.fetchall()

    # Преобразуем каждую строку в словарь
    return [dict(row._mapping) for row in requests]
