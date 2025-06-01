from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from argon2 import PasswordHasher, exceptions as argon2_exceptions
from ..schemas import Role
from sqlalchemy.orm import Session
from .database import get_db
from dotenv import load_dotenv
from .. import models
import os
from uuid import UUID
import string

load_dotenv()

SECRET_KEY = os.getenv("JWT_KEY")
if not SECRET_KEY:
    raise RuntimeError("JWT_KEY environment variable is not set.")
ALGORITHM = "HS256"
PASSWORD_MIN_LENGTH = 8
ACCESS_TOKEN_EXPIRE_MINUTES = 30

ph = PasswordHasher()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
optional_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token", auto_error=False)


def verify_password(plain_password, hashed_password):
    try:
        return ph.verify(hashed_password, plain_password)
    except argon2_exceptions.VerifyMismatchError:
        return False


def get_password_hash(password):
    return ph.hash(password)


def check_password_strength(password: str) -> bool:
    if len(password) < PASSWORD_MIN_LENGTH:
        return False

    has_number = any(char.isdigit() for char in password)
    if not has_number:
        return False

    has_special_char = any(char in string.punctuation for char in password)
    if not has_special_char:
        return False

    return True


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + \
            timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_exception
        user_id = UUID(user_id)
        user = db.get(models.User, user_id)
        if not user:
            raise credentials_exception
        return user
    except jwt.exceptions.InvalidTokenError:
        raise credentials_exception


def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    if current_user.role == Role.deactivated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is deactivated",
        )
    return current_user


def get_current_user_optional(
    token: str | None = Depends(optional_oauth2_scheme),
    db: Session = Depends(get_db)
):
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            return None
        user_id = UUID(user_id)
        user = db.get(models.User, user_id)
        if not user:
            return None
        return user
    except jwt.exceptions.InvalidTokenError:
        return None


def get_current_active_user_optional(current_user: models.User = Depends(get_current_user_optional)):
    if not current_user:
        return None
    if current_user.role == Role.deactivated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is deactivated",
        )
    return current_user
