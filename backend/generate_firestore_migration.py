"""
Genera todos los archivos migrados a Firestore en carpeta separada
NO MODIFICA NINGÚN ARCHIVO ORIGINAL
"""
import os

output_dir = "migrated_files"
os.makedirs(output_dir, exist_ok=True)

print("🚀 Generando archivos migrados a Firestore...")
print(f"📁 Destino: {output_dir}/")
print("=" * 60)

# ============================================================================
# 1. auth.py migrado
# ============================================================================
print("1️⃣  Generando auth.py...")
with open(f"{output_dir}/auth.py", "w") as f:
    f.write('''from datetime import datetime, timedelta
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
''')

print("   ✅ auth.py generado")

# ============================================================================
# 2. auth_router.py migrado
# ============================================================================
print("2️⃣  Generando auth_router.py...")
with open(f"{output_dir}/auth_router.py", "w") as f:
    f.write('''from fastapi import APIRouter, Depends, HTTPException, status
from google.cloud import firestore
from datetime import timedelta
from ..firestore_client import get_db
from .. import schemas, auth
from ..firestore_models import FirestoreUser

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def register(user_data: schemas.UserCreate, db: firestore.Client = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_users = db.collection('users').where('username', '==', user_data.username).limit(1).stream()
    if list(existing_users):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_emails = db.collection('users').where('email', '==', user_data.email).limit(1).stream()
    if list(existing_emails):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = auth.get_password_hash(user_data.password)
    user_dict = FirestoreUser.to_dict(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )
    
    _, doc_ref = db.collection('users').add(user_dict)
    user_dict['id'] = doc_ref.id
    
    return FirestoreUser.to_schema(user_dict)


@router.post("/login", response_model=schemas.Token)
async def login(form_data: schemas.UserLogin, db: firestore.Client = Depends(get_db)):
    """Login user and return JWT token"""
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user['username']}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.User)
async def get_me(current_user: dict = Depends(auth.get_current_user)):
    """Get current authenticated user"""
    return FirestoreUser.to_schema(current_user)
''')

print("   ✅ auth_router.py generado")

print("\n" + "=" * 60)
print("✅ ARCHIVOS BASE GENERADOS EXITOSAMENTE")
print("=" * 60)
print(f"\n📂 Archivos generados en: {output_dir}/")
print("\nPróximos pasos:")
print("1. Revisar los archivos generados")
print("2. Si todo se ve bien, ejecutar apply_migration.py")
print("3. Si algo falla, los originales están intactos + backup")
