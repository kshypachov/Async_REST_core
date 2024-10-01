# constants.py
from enum import Enum

# Перечисления для статусов заявок
class RequestStatusEnum(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"

# Перечисления для пола
class GenderEnum(str, Enum):
    male = "male"
    female = "female"

# Конфигурация для длины полей и других числовых значений
class Definitions:
    name_len = 50
    surname_len = 50
    patronym_len = 50
    rnokpp_len = 12
    passport_number_len = 20
    unzr_len = 10
    comment_len = 500  # Длина для поля comment
    uuid_len = 36  # Длина для UUID