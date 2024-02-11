import os
from logging import config as logging_config

from pydantic import BaseSettings

from .logger import LOGGING


class Settings(BaseSettings):
    PROJECT_NAME: str = "My app"
    PROJECT_HOST: str = "0.0.0.0"
    PROJECT_PORT: int = 8000
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "example"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "mydatabase"
    ECHO_DB: bool = False

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"


settings = Settings()

logging_config.dictConfig(LOGGING)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
