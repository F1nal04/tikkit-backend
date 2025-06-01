from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from .core import database
from fastapi.security import OAuth2PasswordRequestForm
from .core.security import get_current_active_user_optional, verify_password, create_access_token, get_password_hash, get_current_active_user, check_password_strength
from sqlalchemy.exc import IntegrityError
from . import ai

from .schemas.enums import Role, Status, Priority, Topic
from .schemas.auth import Token, PasswordChange, EmailChange, RoleChange
from .schemas.users import UserCreate, UserPublic, UserUpdate
from .schemas.tickets import TicketCreate, TicketPublic, TicketUpdate

from .models.base import Base
from .models.users import User
from .models.tickets import Ticket

# Create the database tables
Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="Ticket System API",
    description="A REST API for managing IT support tickets",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "auth",
            "description": "Operations for authentication. The **register** and **token** endpoints allow you to register and login.",
        },
        {
            "name": "ticket",
            "description": "Operations for a single ticket. The **ticket** endpoint allows you to create, read, update and delete a ticket.",
        },
        {
            "name": "tickets",
            "description": "Operations for multiple tickets. The **tickets** endpoint allows you to read all tickets.",
        },
        {
            "name": "user",
            "description": "Operations for a single user. The **user** endpoint allows you to read, update and delete a user.",
        },
        {
            "name": "users",
            "description": "Operations for multiple users. The **users** endpoint allows you to read all users.",
        },
        {
            "name": "ai",
            "description": "Operations for ai purposes. The **ai** endpoint allows you to create requests to the ai.",
        }
    ]
)


@app.post("/register", tags=["auth"], response_model=Token)
async def register(user: UserCreate, db: Session = Depends(database.get_db)):
    if not check_password_strength(user.password):
        raise HTTPException(
            status_code=400, detail="Password must be at least 8 characters long and contain at least one number and one special character.")
    hashed_password = get_password_hash(user.password)
    user_data = user.model_dump(exclude={'password'})

    db_user = User(**user_data)
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


@app.post("/token", tags=["auth"], response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    form_data.username = form_data.username.strip()
    form_data.username = form_data.username.lower()
    form_data.password = form_data.password.strip()

    user = db.query(User).filter(
        User.email == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code=400, detail="Incorrect email or password")
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=400, detail="Incorrect email or password")
    access_token = create_access_token({"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/ticket", tags=["ticket"], response_model=TicketPublic)
async def create_ticket(ticket: TicketCreate, current_user: User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    db_ticket = Ticket(**ticket.model_dump())
    db_ticket.author = current_user.id
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


@app.get("/ticket/{ticket_id}", tags=["ticket"], response_model=TicketPublic)
async def read_ticket(ticket_id: UUID, db: Session = Depends(database.get_db)):
    db_ticket = db.get(Ticket, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return db_ticket


@app.put("/ticket/{ticket_id}", tags=["ticket"], response_model=TicketPublic)
async def update_ticket(ticket_id: UUID, ticket: TicketUpdate, current_user: User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    db_ticket = db.get(Ticket, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if not current_user.role == Role.admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    update_data = ticket.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_ticket, field, value)

    db.commit()
    db.refresh(db_ticket)
    return db_ticket


@app.delete("/ticket/{ticket_id}", tags=["ticket"])
async def delete_ticket(ticket_id: UUID, current_user: User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    db_ticket = db.get(Ticket, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if not current_user.role == Role.admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    db.delete(db_ticket)
    db.commit()
    return {"message": "Ticket deleted successfully"}


@app.put("/ticket/{ticket_id}/assign", tags=["ticket"], response_model=TicketPublic)
async def assign_ticket(ticket_id: UUID, assigned_to: UUID, current_user: User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    db_ticket = db.get(Ticket, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if not ((current_user.role == Role.admin) or (current_user.id == assigned_to and db_ticket.assigned_to is None)):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    db_ticket.assigned_to = assigned_to
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


@app.put("/ticket/{ticket_id}/status", tags=["ticket"], response_model=TicketPublic)
async def update_ticket_status(ticket_id: UUID, status: Status, current_user: User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    db_ticket = db.get(Ticket, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if not ((current_user.role == Role.admin) or (current_user.id == db_ticket.author and status == Status.closed) or (current_user.id == db_ticket.assigned_to)):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    db_ticket.status = status
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


@app.get("/tickets", tags=["tickets"], response_model=list[TicketPublic])
async def read_tickets(skip: int = 0, limit: int = 100, status: Status = None, priority: Priority = None, assigned_to: UUID = None, author: UUID = None, topic: Topic = None,  db: Session = Depends(database.get_db)):
    query = db.query(Ticket)

    if status:
        query = query.filter(Ticket.status == status)
    if priority:
        query = query.filter(Ticket.priority == priority)
    if assigned_to:
        query = query.filter(Ticket.assigned_to == assigned_to)
    if author:
        query = query.filter(Ticket.author == author)
    if topic:
        query = query.filter(Ticket.topic == topic)

    tickets = query.order_by(Ticket.created_at.desc()).offset(
        skip).limit(limit).all()
    return tickets


@app.get("/ai_request/{ticket_id}", tags=["ai"])
async def get_ticket_solution(ticket_id: UUID, current_user: User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    if not current_user.role == Role.admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    if not ai.is_ai_available():
        raise HTTPException(
            status_code=503,
            detail="AI service is not available. OpenAI API key is not configured."
        )

    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    try:
        return ai.get_response(ticket)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/user", tags=["user"], response_model=UserPublic)
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


@app.put("/user/{user_id}", tags=["user"], response_model=UserPublic)
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


@app.delete("/user/{user_id}", tags=["user"])
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


@app.put("/user/{user_id}/password", tags=["user"])
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


@app.put("/user/{user_id}/email", tags=["user"], response_model=UserPublic)
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


@app.put("/user/{user_id}/role", tags=["user"])
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


@app.get("/users", tags=["users"], response_model=list[UserPublic])
async def get_users(skip: int = 0, limit: int = 100, role: Role | None = None, db: Session = Depends(database.get_db)):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)

    users = query.order_by(User.created_at.desc()).offset(
        skip).limit(limit).all()
    return users
