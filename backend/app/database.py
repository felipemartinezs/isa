"""
DEPRECATED - Migrado a Firestore
Este archivo se mantiene solo por compatibilidad temporal
"""
# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
# from .config import get_settings

# settings = get_settings()

# Commented out - using Firestore now
# engine = create_engine(
#     settings.DATABASE_URL,
#     connect_args={"check_same_thread": False}
# )
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
