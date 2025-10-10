from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import auth_router, articles_router, bom_router, scan_router, sse_router, reports_router
from .init_db import init_database

# Create database tables and dev user
init_database()

app = FastAPI(
    title="Inventory Scanner Pro API",
    description="Backend API for real-time inventory scanning and BOM verification",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://localhost:8000",
    ],
    allow_origin_regex="http://localhost:3000|http://localhost:3001",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(auth_router.router)
app.include_router(articles_router.router)
app.include_router(bom_router.router)
app.include_router(scan_router.router)
app.include_router(sse_router.router)
app.include_router(reports_router.router)

@app.get("/")
def root():
    return {
        "message": "Inventory Scanner Pro API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}



