import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base  # mantiene compat 1.4
from .config import get_settings

settings = get_settings()

# Si DB_DIALECT inicia con "postgresql", usamos Cloud SQL Connector (pg8000).
DB_DIALECT = os.getenv("DB_DIALECT", "").lower()

if DB_DIALECT.startswith("postgresql"):
    # Requiere:
    #   pip install cloud-sql-python-connector[pg8000] pg8000 google-auth
    from google.cloud.sql.connector import Connector, IPTypes

    DB_INSTANCE = os.environ["DB_INSTANCE"]  # "PROYECTO:REGION:INSTANCIA"
    DB_NAME     = os.environ["DB_NAME"]
    DB_USER     = os.environ["DB_USER"]
    DB_PASS     = os.environ["DB_PASS"]

    connector = Connector()

    def getconn():
        # IPTypes.PUBLIC es lo más simple para salir hoy.
        # Cambia a IPTypes.PRIVATE si configuras Serverless VPC Access.
        return connector.connect(
            DB_INSTANCE,
            "pg8000",
            user=DB_USER,
            password=DB_PASS,
            db=DB_NAME,
            ip_type=IPTypes.PUBLIC,
        )

    engine = create_engine(
        "postgresql+pg8000://",
        creator=getconn,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=2,
        pool_recycle=1800,
    )

else:
    # Fallback local (tu comportamiento actual con SQLite).
    # Usa settings.DATABASE_URL (ej. "sqlite:///./local.db")
    connect_args = {}
    if "sqlite" in settings.DATABASE_URL:
        connect_args = {"check_same_thread": False}

    engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
