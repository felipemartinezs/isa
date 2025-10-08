from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from .models import CategoryEnum, ModeEnum, StatusEnum


# User Schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class User(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


# Article Schemas
class ArticleBase(BaseModel):
    sap_article: str
    part_number: str
    description: str
    category: CategoryEnum


class ArticleCreate(ArticleBase):
    pass


class Article(ArticleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# BOM Schemas
class BOMItemBase(BaseModel):
    sap_article: str
    part_number: str
    description: str
    quantity: float


class BOMItemCreate(BOMItemBase):
    pass


class BOMItem(BOMItemBase):
    id: int
    bom_id: int
    
    class Config:
        from_attributes = True


class BOMBase(BaseModel):
    name: str
    category: CategoryEnum


class BOMCreate(BOMBase):
    pass


class BOM(BOMBase):
    id: int
    uploaded_by: int
    uploaded_at: datetime
    is_active: bool
    items: List[BOMItem] = []
    items_count: int = 0
    
    class Config:
        from_attributes = True


# Scan Session Schemas
class ScanSessionCreate(BaseModel):
    mode: ModeEnum
    category: Optional[CategoryEnum] = None  # ← Hacer opcional
    bom_id: Optional[int] = None

class ScanSession(BaseModel):
    id: int
    user_id: int
    mode: ModeEnum
    category: Optional[CategoryEnum]
    bom_id: Optional[int]
    bom_name: Optional[str] = None  # ⭐ NUEVO
    bom_items_count: Optional[int] = None  # ⭐ NUEVO
    scanned_items_count: Optional[int] = None  # ⭐ NUEVO
    started_at: datetime
    ended_at: Optional[datetime]
    is_active: bool
    
    class Config:
        from_attributes = True


# Scan Record Schemas
class ScanRecordCreate(BaseModel):
    session_id: int
    sap_article: str
    po_number: Optional[str] = None
    quantity: float = 1.0
    manual_entry: bool = False
    detected_category: Optional[CategoryEnum] = None  # Para entrada manual

class ScanRecord(BaseModel):
    id: int
    session_id: int
    sap_article: str
    part_number: Optional[str]
    description: Optional[str]
    po_number: Optional[str]
    quantity: float
    scanned_at: datetime
    manual_entry: bool
    expected_quantity: Optional[float]
    status: Optional[StatusEnum]
    detected_category: Optional[CategoryEnum]  # Agregar esta línea
    class Config:
        from_attributes = True


# SSE Event Schemas
class ScanEvent(BaseModel):
    type: str = "scan"
    session_id: int
    record: ScanRecord


# Upload Response
class UploadResponse(BaseModel):
    message: str
    count: int
    items: Optional[List[dict]] = None
