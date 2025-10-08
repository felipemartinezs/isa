from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base


class CategoryEnum(str, enum.Enum):
    CCTV = "CCTV"
    CX = "CX"
    FIRE_BURG_ALARM = "FIRE & BURG ALARM"


class ModeEnum(str, enum.Enum):
    INVENTORY = "INVENTORY"
    BOM = "BOM"


class StatusEnum(str, enum.Enum):
    MATCH = "MATCH"
    OVER = "OVER"
    UNDER = "UNDER"
    PENDING = "PENDING"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    scan_sessions = relationship("ScanSession", back_populates="user")


class Article(Base):
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    sap_article = Column(String, index=True, nullable=False)
    part_number = Column(String, index=True, nullable=False)
    description = Column(String, nullable=False)
    category = Column(Enum(CategoryEnum), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('sap_article', 'category', name='uix_article_category'),
    )


class BOM(Base):
    __tablename__ = "boms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(Enum(CategoryEnum), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    items = relationship("BOMItem", back_populates="bom", cascade="all, delete-orphan")
    user = relationship("User")


class BOMItem(Base):
    __tablename__ = "bom_items"
    
    id = Column(Integer, primary_key=True, index=True)
    bom_id = Column(Integer, ForeignKey("boms.id"), nullable=False)
    sap_article = Column(String, index=True, nullable=False)
    part_number = Column(String, nullable=False)
    description = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    
    bom = relationship("BOM", back_populates="items")


class ScanSession(Base):
    __tablename__ = "scan_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    mode = Column(Enum(ModeEnum), nullable=False)
    category = Column(Enum(CategoryEnum), nullable=True)  # Nullable para INVENTORY mode
    bom_id = Column(Integer, ForeignKey("boms.id"), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="scan_sessions")
    bom = relationship("BOM")
    records = relationship("ScanRecord", back_populates="session", cascade="all, delete-orphan")


class ScanRecord(Base):
    __tablename__ = "scan_records"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("scan_sessions.id"), nullable=False)
    sap_article = Column(String, index=True, nullable=False)
    part_number = Column(String, nullable=True)
    description = Column(String, nullable=True)
    po_number = Column(String, nullable=True)
    quantity = Column(Float, default=1.0)
    scanned_at = Column(DateTime, default=datetime.utcnow)
    manual_entry = Column(Boolean, default=False)
    # Agregar después de línea 110:
    detected_category = Column(Enum(CategoryEnum), nullable=True)  # Auto-detected from Article DB
    # BOM comparison fields
    expected_quantity = Column(Float, nullable=True)
    status = Column(Enum(StatusEnum), nullable=True)
    
    session = relationship("ScanSession", back_populates="records")
