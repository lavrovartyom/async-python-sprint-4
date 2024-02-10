import os
from logging import config as logging_config

from .logger import LOGGING

logging_config.dictConfig(LOGGING)

PROJECT_NAME = os.getenv("PROJECT_NAME", "Проектное задание 4 спринта")
PROJECT_HOST = os.getenv("PROJECT_HOST", "0.0.0.0")
PROJECT_PORT = int(os.getenv("PROJECT_PORT", "8000"))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
