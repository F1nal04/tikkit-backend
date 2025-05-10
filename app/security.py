from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from argon2 import PasswordHasher, exceptions as argon2_exceptions
from schemas import Role
from sqlalchemy.orm import Session
from database import get_db
from dotenv import load_dotenv
import models
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is not set.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

ph = PasswordHasher()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    try:
        return ph.verify(hashed_password, plain_password)
    except argon2_exceptions.VerifyMismatchError:
        return False


def get_password_hash(password):
    return ph.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
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
