from fastapi import APIRouter
# from app.repository import init_db


crm_router = APIRouter(tags=["Роутер CRM сервиса"])


# @opencv_app_router.on_event("startup")
# async def startup_event():
#     await init_db()
