import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr

"""
Слой Pydantic моделей БД
"""


class OperatorCreate(BaseModel):
    """
    Модель для создания объекта таблицы operators
    """

    name: str
    is_active: Optional[bool] = True
    max_concurrent: Optional[int] = 5


class OperatorUpdate(BaseModel):
    """
    Модель для обновления объекта таблицы operators
    """

    name: Optional[str]
    is_active: Optional[bool]
    max_concurrent: Optional[int]


class OperatorOut(BaseModel):
    """
    Модель для вывода объекта таблицы operators
    """

    id: int | None
    name: str | None
    is_active: bool | None
    max_concurrent: int | None

    class Config:
        orm_mode = True


class SourceCreate(BaseModel):
    """
    Модель для создания объекта таблицы sources
    """

    code: str = Field(..., min_length=1)
    name: str
    description: Optional[str] = None


class SourceOut(BaseModel):
    """
    Модель для вывода объекта таблицы sources
    """

    id: int
    code: str
    name: str
    description: Optional[str]

    class Config:
        orm_mode = True


class LeadOut(BaseModel):
    """
    Модель для вывода объекта таблицы leads
    """

    id: int
    external_id: Optional[str]
    phone: Optional[str]
    email: Optional[str]

    class Config:
        orm_mode = True


class Status(Enum):
    NEW = "new"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


class ContactCreate(BaseModel):
    """
    Модель для создания обращения
    При создании обращения происходит поиск клиента в БД по телефону или эл. почте, или по источнику (external_id)
    """

    external_id: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    status: Optional[Status] = Status.NEW
    payload: Optional[Dict[str, Any]] = None


class ContactOut(BaseModel):
    """
    Модель для вывода объекта таблицы contacts
    """

    id: int | None
    lead_id: int | None
    source_id: int | None
    operator_id: int | None
    status: Status | None
    payload: Optional[Dict[str, Any]]
    created_at: datetime.datetime | None = Field(default=datetime.datetime.utcnow())

    class Config:
        orm_mode = True


class OperatorSourceWeightCreate(BaseModel):
    """
    Модель для создания объекта таблицы operator_source_weights
    """

    operator_id: Optional[int]
    source_id: Optional[int]
    weight: Optional[float]


class LeadsAndContactsOut(BaseModel):
    """
    Модель для отображения списка лидов и их обращений
    """

    lead_phone: str
    lead_id: int
    contact_id: int
