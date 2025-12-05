from fastapi import FastAPI
from uvicorn import run
from app.controllers import crm_router

"""
Слой запуска приложения
"""


app = FastAPI(title="FastAPI CRM")

app.include_router(crm_router)


# Для локального запуска сервиса без Docker/Docker Compose
if __name__ == "__main__":
    run(
        app="main:app",
        reload=True,
        log_level="debug",
        host="localhost",
        port=8000,
    )
