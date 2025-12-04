from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    DATABASE_URL: str

    model_config = SettingsConfigDict(
        env_file=f"{os.path.dirname(os.path.abspath(__file__))}/.env"
    )


settings = Settings()


@lru_cache()
def get_settings():
    return settings


# Аннотированный тип для эндпоинтов
SettingsDep = Annotated[Settings, Depends(get_settings)]
