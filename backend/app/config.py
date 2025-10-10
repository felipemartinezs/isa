from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
from dotenv import load_dotenv
import os

# FORZAR CARGA DEL .ENV ANTES DE CREAR SETTINGS
load_dotenv()

class Settings(BaseSettings):
    # SQLite local (desarrollo por defecto)
    DATABASE_URL: str = "sqlite:///./inventory_scanner.db"
    
    # Cloud SQL (opcionales, usados cuando DB_DIALECT está presente)
    DB_DIALECT: Optional[str] = None
    DB_INSTANCE: Optional[str] = None
    DB_NAME: Optional[str] = None
    DB_USER: Optional[str] = None
    DB_PASS: Optional[str] = None
    
    # Auth
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()