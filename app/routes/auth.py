from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError

from ..core import database
from ..core.security import verify_password, create_access_token, get_password_hash, check_password_strength
from ..schemas import Token, UserCreate
from .. import models

router = APIRouter(prefix="", tags=["auth"])


@router.post("/register", response_model=Token)
async def register(user: UserCreate, db: Session = Depends(database.get_db)):
    if not check_password_strength(user.password):
        raise HTTPException(
            status_code=400, detail="Password must be at least 8 characters long and contain at least one number and one special character.")
    hashed_password = get_password_hash(user.password)
    user_data = user.model_dump(exclude={'password'})

    db_user = models.User(**user_data)
    db_user.hashed_password = hashed_password

    db.add(db_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")
    db.refresh(db_user)
    access_token = create_access_token({"sub": str(db_user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    form_data.username = form_data.username.strip()
    form_data.username = form_data.username.lower()
    form_data.password = form_data.password.strip()

    user = db.query(models.User).filter(
        models.User.email == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code=400, detail="Incorrect email or password")
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=400, detail="Incorrect email or password")
    access_token = create_access_token({"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}
