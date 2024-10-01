# models.py
import sqlalchemy
from sqlalchemy import Table, Column, Integer, JSON, String, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.dialects.mysql import CHAR
from constants.constants import RequestStatusEnum, GenderEnum, Definitions
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

# Таблица заявок
request_table = Table(
    "requests",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("person_data", JSON, nullable=False),
    Column("status", Enum(RequestStatusEnum), default=RequestStatusEnum.pending, nullable=False),
    Column("created_at", DateTime, server_default=sqlalchemy.func.now(), nullable=False),
    Column("updated_at", DateTime, server_default=sqlalchemy.func.now(), onupdate=sqlalchemy.func.now(), nullable=False),
    Column("found_person_id", Integer, ForeignKey("person.id"), nullable=True),
    Column("comment", String(Definitions.comment_len)),
    Column("downloaded", Boolean, nullable=False, default=False),
    Column("UUID", CHAR(Definitions.uuid_len), default=lambda: str(uuid.uuid4())),
)

# Таблица данных о персоне
person_table = Table(
    "person",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(Definitions.name_len), nullable=True),
    Column("surname", String(Definitions.surname_len), nullable=True),
    Column("patronym", String(Definitions.patronym_len)),
    Column("dateOfBirth", DateTime, nullable=True),
    Column("gender", Enum(GenderEnum), nullable=True),
    Column("rnokpp", String(Definitions.rnokpp_len), unique=True, nullable=True, index=True),
    Column("passportNumber", String(Definitions.passport_number_len), unique=True, nullable=True),
    Column("unzr", String(Definitions.unzr_len), unique=True, nullable=True)
)