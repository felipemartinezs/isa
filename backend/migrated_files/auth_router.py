from fastapi import APIRouter, Depends, HTTPException, status
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
