from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Firestore Configuration - PRODUCCIÓN
    USE_FIRESTORE_EMULATOR: bool = False
    FIRESTORE_PROJECT_ID: str = "qtsisa"
    GOOGLE_APPLICATION_CREDENTIALS: str = "credentials/service-account.json"
    
    # JWT Configuration
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
