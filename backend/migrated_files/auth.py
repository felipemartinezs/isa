from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.cloud import firestore
from .config import get_settings
from .firestore_client import get_db
from . import schemas
from .firestore_models import FirestoreUser

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str):
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise JWTError("Invalid token payload")
        return payload
    except JWTError as e:
        raise JWTError(f"Token validation failed: {str(e)}")


def authenticate_user(db: firestore.Client, username: str, password: str):
    """Authenticate user against Firestore"""
    users = db.collection('users').where('username', '==', username).limit(1).stream()
    user_docs = list(users)
    
    if not user_docs:
        return False
    
    user_doc = user_docs[0]
    user_data = user_doc.to_dict()
    
    if not verify_password(password, user_data['hashed_password']):
        return False
    
    # Retornar user data con ID
    user_data['id'] = user_doc.id
    return user_data


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: firestore.Client = Depends(get_db)
) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Buscar usuario en Firestore
    users = db.collection('users').where('username', '==', username).limit(1).stream()
    user_docs = list(users)
    
    if not user_docs:
        raise credentials_exception
    
    user_doc = user_docs[0]
    user_data = user_doc.to_dict()
    user_data['id'] = user_doc.id
    
    return user_data
