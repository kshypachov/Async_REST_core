# schemas.py
from pydantic import BaseModel, Field, constr
from typing import Optional
from datetime import date
from constants.constants import RequestStatusEnum, GenderEnum, Definitions

class PersonPartial(BaseModel):
    name: Optional[constr(min_length=1, max_length=Definitions.name_len)]
    surname: Optional[constr(min_length=1, max_length=Definitions.surname_len)]
    patronym: Optional[constr(min_length=1, max_length=Definitions.patronym_len)]
    dateOfBirth: Optional[date]
    gender: Optional[GenderEnum]
    rnokpp: Optional[constr(min_length=Definitions.rnokpp_len, max_length=Definitions.rnokpp_len)]
    passportNumber: Optional[constr(min_length=Definitions.passport_number_len, max_length=Definitions.passport_number_len)]
    unzr: Optional[constr(min_length=Definitions.unzr_len, max_length=Definitions.unzr_len)]

class RequestCreate(BaseModel):
    person_data: PersonPartial
    comment: Optional[str] = Field(max_length=Definitions.comment_len)

class RequestUpdate(BaseModel):
    status: RequestStatusEnum
    comment: Optional[str] = None

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