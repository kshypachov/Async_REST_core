import uuid
from urllib.request import Request

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey, String, JSON, MetaData, bindparam
from sqlalchemy.dialects.mysql import CHAR, insert
from datetime import datetime, date
from enum import Enum
from pydantic import BaseModel, Field, constr, validator
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, query_expression
from datetime import date
from fastapi import FastAPI, Request, HTTPException, Depends, Header
from sqlalchemy import insert, exc
import databases


# Настройка базы данных
DATABASE_URL = "mysql+aiomysql://async:async@10.0.20.242/async"
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
metadata = sqlalchemy.MetaData()
Base = declarative_base()



# Конфигурация для длины полей
class Definitions:
    name_len = 50
    surname_len = 50
    patronym_len = 50
    rnokpp_len = 12
    passport_number_len = 20
    unzr_len = 10

definitions = Definitions()

# Перечисление для пола
class GenderEnum(str, Enum):
    male = "male"
    female = "female"

# Таблица для хранения заявок на поиск
class RequestStatusEnum(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"

request_table = sqlalchemy.Table(
    "requests",
    metadata,
sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("person_data", JSON, nullable=False),  # Используем JSON для MySQL/MariaDB
    sqlalchemy.Column("status", sqlalchemy.Enum(RequestStatusEnum), default=RequestStatusEnum.pending, nullable=False),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime, server_default=sqlalchemy.func.now(), nullable=False),
    sqlalchemy.Column("updated_at", sqlalchemy.DateTime, server_default=sqlalchemy.func.now(),onupdate=sqlalchemy.func.now(), nullable=False),
    sqlalchemy.Column("found_person_id", sqlalchemy.Integer, ForeignKey("person.id"), nullable=True),  # Ссылка на найденную запись
    sqlalchemy.Column("comment", sqlalchemy.String(500)),
    sqlalchemy.Column("downloaded", sqlalchemy.Boolean, nullable=False, default=False),  # Поле для отметки скачанных заявок
    sqlalchemy.Column("UUID", CHAR(36), default=lambda: str(uuid.uuid4())),  # UUID в виде строки
)

# Таблица для хранения полной информации о найденном человеке
person_table = sqlalchemy.Table(
    "person",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String(definitions.name_len), nullable=True),
    sqlalchemy.Column("surname", sqlalchemy.String(definitions.surname_len), nullable=True),
    sqlalchemy.Column("patronym", sqlalchemy.String(definitions.patronym_len)),
    sqlalchemy.Column("dateOfBirth", sqlalchemy.Date, nullable=True),
    sqlalchemy.Column("gender", sqlalchemy.Enum(GenderEnum), nullable=True),
    sqlalchemy.Column("rnokpp", sqlalchemy.String(definitions.rnokpp_len), unique=True, nullable=True, index=True),
    sqlalchemy.Column("passportNumber", sqlalchemy.String(definitions.passport_number_len), unique=True, nullable=True),
    sqlalchemy.Column("unzr", sqlalchemy.String(definitions.unzr_len), unique=True, nullable=True)
)

# Асинхронная функция для взаимодействия с базой данных
async def get_db():
    async with SessionLocal() as session:
        yield session

# Pydantic модели для валидации данных
class PersonPartial(BaseModel):
    name: Optional[constr(min_length=1, max_length=definitions.name_len)]
    surname: Optional[constr(min_length=1, max_length=definitions.surname_len)]
    patronym: Optional[constr(min_length=1, max_length=definitions.patronym_len)]
    dateOfBirth: Optional[date]
    gender: Optional[GenderEnum]
    rnokpp: Optional[constr(min_length=definitions.rnokpp_len, max_length=definitions.rnokpp_len)]
    passportNumber: Optional[constr(min_length=definitions.passport_number_len, max_length=definitions.passport_number_len)]
    unzr: Optional[constr(min_length=definitions.unzr_len, max_length=definitions.unzr_len)]

class RequestCreate(BaseModel):
    person_data: PersonPartial
    comment: Optional[str] = Field(max_length=500)
    #UUID: Optional[constr(min_length=36, max_length=36)]

    @validator('person_data')
    def check_at_least_one_field(cls, v):
        if not any(v.dict().values()):
            raise ValueError('At least one field in person_data must be provided.')
        return v

class RequestUpdate(BaseModel):
    status: RequestStatusEnum
    comment: Optional[str] = None  # Делаем поле необязательным

# Модель для записи найденной полной информации о человеке
class PersonInfoUpdate(BaseModel):
    name: Optional[str]
    surname: Optional[str]
    patronym: Optional[str]
    dateOfBirth: Optional[date]
    gender: Optional[GenderEnum]
    rnokpp: Optional[str]
    passportNumber: Optional[str]
    unzr: Optional[str]
#    UUID: Optional[str]
#    downloaded: Optional[bool]

# Инициализация FastAPI
app = FastAPI()


# Эндпоинты для внешних пользователей
external = FastAPI(docs_url="/docs", openapi_url="/openapi.json")


# Создание новой заявки на поиск
from sqlalchemy import insert
from datetime import date

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

# Эндпоинты для служащих архива (внутренние)
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

# Включение приложения внутренней службы в основное приложение с префиксом
app.mount("/internal", internal)
app.mount("/external", external)

# Запуск приложения
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)