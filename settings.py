from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    DOCKER_POSTGRES_HOST: str

    @property
    def system_db_url(self):
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.DOCKER_POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_USER}"
        )

    @property
    def db_url(self):
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.DOCKER_POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(
        env_file=f"{os.path.dirname(os.path.abspath(__file__))}/.env"
    )


settings = Settings()


@lru_cache()
def get_settings():
    return settings


# Аннотированный тип для эндпоинтов
SettingsDep = Annotated[Settings, Depends(get_settings)]
