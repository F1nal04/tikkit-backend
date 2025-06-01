from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from ..core import database
from ..core.security import get_current_active_user_optional, get_current_active_user, verify_password, get_password_hash
from ..schemas.enums import Role
from ..schemas.auth import PasswordChange, EmailChange, RoleChange
from ..schemas.users import UserPublic, UserUpdate
from ..models.users import User
from ..models.tickets import Ticket

router = APIRouter(prefix="", tags=["user", "users"])


@router.get("/user", tags=["user"], response_model=UserPublic)
async def get_user(user_id: UUID | None = None,  current_user: User | None = Depends(get_current_active_user_optional), db: Session = Depends(database.get_db)):
    if not user_id:
        if not current_user:
            raise HTTPException(
                status_code=400, detail="No user_id provided and no authenticated user.")
        user = db.get(User, current_user.id)
    else:
        user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/user/{user_id}", tags=["user"], response_model=UserPublic)
async def update_user(user_id: UUID, user: UserUpdate, current_user: User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    if not current_user.role == Role.admin:
        if not user_id == current_user.id:
            raise HTTPException(
                status_code=403, detail="Not enough permissions")

    db_user = db.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete("/user/{user_id}", tags=["user"])
async def delete_user(user_id: UUID, current_user: User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    if not current_user.role == Role.admin:
        if not user_id == current_user.id:
            raise HTTPException(
                status_code=403, detail="Not enough permissions")

    db_user = db.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    tickets_as_author = db.query(Ticket).filter(
        Ticket.author == user_id).count()
    if tickets_as_author > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete user: user has {tickets_as_author} tickets as author. Please reassign or delete these tickets first."
        )

    tickets_assigned = db.query(Ticket).filter(
        Ticket.assigned_to == user_id).count()
    if tickets_assigned > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete user: user has {tickets_assigned} tickets assigned to them. Please reassign these tickets first."
        )

    db.delete(db_user)
    db.commit()
    return {"message": "User deleted successfully"}


@router.put("/user/{user_id}/password", tags=["user"])
async def change_password(password: PasswordChange, user_id: UUID, current_user: User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    if not current_user.role == Role.admin:
        if not user_id == current_user.id:
            raise HTTPException(
                status_code=403, detail="Not enough permissions")

    db_user = db.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not current_user.role == Role.admin or user_id == current_user.id:
        if not verify_password(password.old_password, db_user.hashed_password):
            raise HTTPException(
                status_code=400, detail="Old password is incorrect")

    db_user.hashed_password = get_password_hash(password.new_password)
    db.commit()
    return {"message": "Password changed successfully"}


@router.put("/user/{user_id}/email", tags=["user"], response_model=UserPublic)
async def change_email(email: EmailChange, user_id: UUID, current_user: User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    if not current_user.role == Role.admin:
        if not user_id == current_user.id:
            raise HTTPException(
                status_code=403, detail="Not enough permissions")

    db_user = db.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not current_user.role == Role.admin or user_id == current_user.id:
        if not verify_password(email.password, db_user.hashed_password):
            raise HTTPException(
                status_code=400, detail="Password is incorrect")

    db_user.email = email.new_email
    db.commit()
    db.refresh(db_user)
    return db_user


@router.put("/user/{user_id}/role", tags=["user"])
async def change_role(user_id: UUID, role: RoleChange, current_user: User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    if not current_user.role == Role.admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    db_user = db.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if db_user.role == Role.admin:
        raise HTTPException(
            status_code=403, detail="Cannot change role of admin users")

    db_user.role = role.new_role
    db.commit()
    return {"message": "Role changed successfully"}


@router.get("/users", tags=["users"], response_model=list[UserPublic])
async def get_users(skip: int = 0, limit: int = 100, role: Role | None = None, db: Session = Depends(database.get_db)):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)

    users = query.order_by(User.created_at.desc()).offset(
        skip).limit(limit).all()
    return users
