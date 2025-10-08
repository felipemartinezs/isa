from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# REMOVIDO: from .database import engine, Base
# REMOVIDO: from .init_db import init_database
from .routers import auth_router, articles_router, sse_router
# TODO: Agregar bom_router, scan_router, reports_router cuando estén listos

# REMOVIDO: init_database() - Firestore no necesita init

app = FastAPI(
    title="Inventory Scanner Pro API",
    description="Backend API for real-time inventory scanning and BOM verification (Firestore)",
    version="2.0.0-firestore"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(auth_router.router)
app.include_router(articles_router.router)
app.include_router(sse_router.router)
# TODO: Descomentar cuando estén migrados:
# app.include_router(bom_router.router)
# app.include_router(scan_router.router)
# app.include_router(reports_router.router)

@app.get("/")
def root():
    return {
        "message": "Inventory Scanner Pro API (Firestore)",
        "version": "2.0.0-firestore",
        "status": "running",
        "database": "Firestore"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "firestore"}
