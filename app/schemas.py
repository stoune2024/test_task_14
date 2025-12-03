from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr


# Operator schemas
class OperatorCreate(BaseModel):
    name: str
    is_active: Optional[bool] = True
    max_concurrent: Optional[int] = 5


class OperatorUpdate(BaseModel):
    name: Optional[str]
    is_active: Optional[bool]
    max_concurrent: Optional[int]


class OperatorOut(BaseModel):
    id: int
    name: str
    is_active: bool
    max_concurrent: int

    class Config:
        orm_mode = True


# Source schemas
class SourceCreate(BaseModel):
    code: str = Field(..., min_length=1)
    name: str
    description: Optional[str] = None


class SourceOut(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str]

    class Config:
        orm_mode = True


# Lead schemas
class LeadCreate(BaseModel):
    external_id: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


class LeadOut(BaseModel):
    id: int
    external_id: Optional[str]
    phone: Optional[str]
    email: Optional[str]

    class Config:
        orm_mode = True


# Contact (обращение) schemas
class ContactCreate(BaseModel):
    # вход при создании обращения
    # минимум: либо external_id or phone or email should be present to match lead
    external_id: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None

    source_code: str  # идентификатор источника/бота
    payload: Optional[Dict[str, Any]] = None


class ContactOut(BaseModel):
    id: int
    lead: LeadOut
    source: SourceOut
    operator: Optional[OperatorOut]
    status: str
    payload: Optional[Dict[str, Any]]

    class Config:
        orm_mode = True


# For updating weights per source
class SourceWeightsUpdate(BaseModel):
    weights: Dict[int, float]  # operator_id -> weight
