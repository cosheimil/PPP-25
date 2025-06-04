from typing import Generator, Optional
import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError

from app.db.database import SessionLocal
from app.schemas.user import UserCreate, UserLogin, UserWithToken, UserOut
from app.core.security import create_access_token
from app.cruds import user as user_crud
from app.models.user import User

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login/")

def get_db() -> Generator[Session, None, None]:
    """Dependency for database session management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(
            token,
            os.getenv("SECRET_KEY"),
            algorithms=[os.getenv("ALGORITHM")]
        )
        return payload
    except JWTError:
        return None

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> UserOut:
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(token)
    if not payload:
        raise credentials_exception
        
    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise credentials_exception
        
    return user

@router.post("/sign-up/", response_model=UserWithToken, status_code=status.HTTP_201_CREATED)
async def sign_up(
    user_data: UserCreate,
    db: Session = Depends(get_db)
) -> UserWithToken:
    """Register a new user."""
    if user_crud.get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
        
    user = user_crud.create_user(db, user_data)
    token = create_access_token({"sub": str(user.id)})
    return UserWithToken(id=user.id, email=user.email, token=token)

@router.post("/login/", response_model=UserWithToken)
async def login(
    data: UserLogin,
    db: Session = Depends(get_db)
) -> UserWithToken:
    """Authenticate user and return token."""
    user = user_crud.authenticate_user(db, data.email, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    token = create_access_token({"sub": str(user.id)})
    return UserWithToken(id=user.id, email=user.email, token=token)

@router.get("/users/me/", response_model=UserOut)
async def read_users_me(
    current_user: UserOut = Depends(get_current_user)
) -> UserOut:
    """Get current user information."""
    return current_user
