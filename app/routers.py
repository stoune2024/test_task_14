from fastapi import APIRouter
from app.repository import init_db

"""
Слой маршрутизатора сервиса
"""


crm_router = APIRouter(tags=["Роутер CRM сервиса"])


@crm_router.on_event("startup")
async def startup_event():
    await init_db()
