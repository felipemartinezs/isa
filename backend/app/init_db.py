from sqlalchemy.orm import Session
from . import models, auth
from .database import SessionLocal, engine, Base


def init_dev_user(db: Session):
    """Create default dev user if not exists"""
    existing_user = db.query(models.User).filter(
        models.User.username == "admin"
    ).first()
    
    if not existing_user:
        dev_user = models.User(
            username="admin",
            email="admin@demo.com",
            hashed_password=auth.get_password_hash("admin123"),
            is_active=True
        )
        db.add(dev_user)
        db.commit()
        db.refresh(dev_user)
        print("✅ Created dev user: username='admin', password='admin123'")
        return dev_user
    else:
        print("ℹ️  Dev user 'admin' already exists")
        return existing_user


def init_database():
    """Initialize database and create dev user"""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create dev user
    db = SessionLocal()
    try:
        init_dev_user(db)
    finally:
        db.close()
