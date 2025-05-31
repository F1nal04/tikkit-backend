from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from . import models
from . import schemas
from . import database
from . import history
from fastapi.security import OAuth2PasswordRequestForm
from .security import get_current_active_user_optional, verify_password, create_access_token, get_password_hash, get_current_active_user, check_password_strength
from sqlalchemy.exc import IntegrityError
from . import ai

# Create the database tables
models.Base.metadata.create_all(bind=database.engine)

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
        },
        {
            "name": "history",
            "description": "Operations for ticket history. The **history** endpoints allow you to view ticket change history.",
        }
    ]
)


@app.post("/register", tags=["auth"], response_model=schemas.Token)
async def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
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


@app.post("/token", tags=["auth"], response_model=schemas.Token)
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


@app.post("/ticket", tags=["ticket"], response_model=schemas.TicketPublic)
async def create_ticket(ticket: schemas.TicketCreate, current_user: models.User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    db_ticket = models.Ticket(**ticket.model_dump())
    db_ticket.author = current_user.id
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)

    # Record ticket creation in history
    history.record_ticket_creation(db, db_ticket, current_user.id)
    db.commit()

    return db_ticket


@app.get("/ticket/{ticket_id}", tags=["ticket"], response_model=schemas.TicketPublic)
async def read_ticket(ticket_id: UUID, db: Session = Depends(database.get_db)):
    db_ticket = db.get(models.Ticket, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return db_ticket


@app.get("/ticket/{ticket_id}/history", tags=["history"], response_model=list[schemas.TicketHistoryPublic])
async def get_ticket_history(ticket_id: UUID, db: Session = Depends(database.get_db)):
    """Get the complete history of changes for a specific ticket."""
    # Verify ticket exists
    db_ticket = db.get(models.Ticket, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Get history entries ordered by date (newest first)
    history_entries = db.query(models.TicketHistory).filter(
        models.TicketHistory.ticket_id == ticket_id
    ).order_by(models.TicketHistory.changed_at.desc()).all()

    return history_entries


@app.get("/ticket/{ticket_id}/with-history", tags=["ticket"], response_model=schemas.TicketWithHistory)
async def read_ticket_with_history(ticket_id: UUID, db: Session = Depends(database.get_db)):
    """Get a ticket along with its complete change history."""
    db_ticket = db.get(models.Ticket, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Get history entries
    history_entries = db.query(models.TicketHistory).filter(
        models.TicketHistory.ticket_id == ticket_id
    ).order_by(models.TicketHistory.changed_at.desc()).all()

    # Convert to response model
    ticket_data = schemas.TicketPublic.model_validate(db_ticket)
    return schemas.TicketWithHistory(
        **ticket_data.model_dump(),
        history=[schemas.TicketHistoryPublic.model_validate(
            entry) for entry in history_entries]
    )


@app.put("/ticket/{ticket_id}", tags=["ticket"], response_model=schemas.TicketPublic)
async def update_ticket(ticket_id: UUID, ticket: schemas.TicketUpdate, current_user: models.User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    db_ticket = db.get(models.Ticket, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if not current_user.role == schemas.Role.admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Store old ticket state for history tracking
    old_ticket_copy = models.Ticket(
        id=db_ticket.id,
        topic=db_ticket.topic,
        description=db_ticket.description,
        message=db_ticket.message,
        status=db_ticket.status,
        priority=db_ticket.priority,
        assigned_to=db_ticket.assigned_to,
        author=db_ticket.author
    )

    update_data = ticket.model_dump(exclude_unset=True)

    # Record changes in history before applying them
    history.record_ticket_changes(
        db, ticket_id, old_ticket_copy, update_data, current_user.id)

    # Apply the changes
    for field, value in update_data.items():
        setattr(db_ticket, field, value)

    db.commit()
    db.refresh(db_ticket)
    return db_ticket


@app.delete("/ticket/{ticket_id}", tags=["ticket"])
async def delete_ticket(ticket_id: UUID, current_user: models.User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    db_ticket = db.get(models.Ticket, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if not current_user.role == schemas.Role.admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Record deletion in history before deleting
    history.record_ticket_deletion(db, ticket_id, current_user.id)

    db.delete(db_ticket)
    db.commit()
    return {"message": "Ticket deleted successfully"}


@app.put("/ticket/{ticket_id}/assign", tags=["ticket"], response_model=schemas.TicketPublic)
async def assign_ticket(ticket_id: UUID, assigned_to: UUID, current_user: models.User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    db_ticket = db.get(models.Ticket, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if not ((current_user.role == schemas.Role.admin) or (current_user.id == assigned_to and db_ticket.assigned_to is None)):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Record assignment change in history
    old_assigned_to = db_ticket.assigned_to
    history.record_ticket_assignment(
        db, ticket_id, old_assigned_to, assigned_to, current_user.id)

    db_ticket.assigned_to = assigned_to
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


@app.put("/ticket/{ticket_id}/status", tags=["ticket"], response_model=schemas.TicketPublic)
async def update_ticket_status(ticket_id: UUID, status: schemas.Status, current_user: models.User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    db_ticket = db.get(models.Ticket, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if not ((current_user.role == schemas.Role.admin) or (current_user.id == db_ticket.author and status == schemas.Status.closed) or (current_user.id == db_ticket.assigned_to)):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Record status change in history
    old_status = db_ticket.status
    history.record_ticket_status_change(
        db, ticket_id, old_status, status, current_user.id)

    db_ticket.status = status
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


@app.get("/tickets", tags=["tickets"], response_model=list[schemas.TicketPublic])
async def read_tickets(skip: int = 0, limit: int = 100, status: schemas.Status = None, priority: schemas.Priority = None, assigned_to: UUID = None, author: UUID = None, topic: schemas.Topic = None,  db: Session = Depends(database.get_db)):
    query = db.query(models.Ticket)

    if status:
        query = query.filter(models.Ticket.status == status)
    if priority:
        query = query.filter(models.Ticket.priority == priority)
    if assigned_to:
        query = query.filter(models.Ticket.assigned_to == assigned_to)
    if author:
        query = query.filter(models.Ticket.author == author)
    if topic:
        query = query.filter(models.Ticket.topic == topic)

    tickets = query.order_by(models.Ticket.created_at.desc()).offset(
        skip).limit(limit).all()
    return tickets


@app.get("/ai_request/{ticket_id}", tags=["ai"])
async def get_ticket_solution(ticket_id: UUID, current_user: models.User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    if not current_user.role == schemas.Role.admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    if not ai.is_ai_available():
        raise HTTPException(
            status_code=503,
            detail="AI service is not available. OpenAI API key is not configured."
        )

    ticket = db.get(models.Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    try:
        return ai.get_response(ticket)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/user", tags=["user"], response_model=schemas.UserPublic)
async def get_user(user_id: UUID | None = None,  current_user: models.User | None = Depends(get_current_active_user_optional), db: Session = Depends(database.get_db)):
    if not user_id:
        if not current_user:
            raise HTTPException(
                status_code=400, detail="No user_id provided and no authenticated user.")
        user = db.get(models.User, current_user.id)
    else:
        user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/user/{user_id}", tags=["user"], response_model=schemas.UserPublic)
async def update_user(user_id: UUID, user: schemas.UserUpdate, current_user: models.User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    if not current_user.role == schemas.Role.admin:
        if not user_id == current_user.id:
            raise HTTPException(
                status_code=403, detail="Not enough permissions")

    db_user = db.get(models.User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)
    return db_user


@app.delete("/user/{user_id}", tags=["user"])
async def delete_user(user_id: UUID, current_user: models.User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    if not current_user.role == schemas.Role.admin:
        if not user_id == current_user.id:
            raise HTTPException(
                status_code=403, detail="Not enough permissions")

    db_user = db.get(models.User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    tickets_as_author = db.query(models.Ticket).filter(
        models.Ticket.author == user_id).count()
    if tickets_as_author > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete user: user has {tickets_as_author} tickets as author. Please reassign or delete these tickets first."
        )

    tickets_assigned = db.query(models.Ticket).filter(
        models.Ticket.assigned_to == user_id).count()
    if tickets_assigned > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete user: user has {tickets_assigned} tickets assigned to them. Please reassign these tickets first."
        )

    db.delete(db_user)
    db.commit()
    return {"message": "User deleted successfully"}


@app.put("/user/{user_id}/password", tags=["user"])
async def change_password(password: schemas.PasswordChange, user_id: UUID, current_user: models.User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    if not current_user.role == schemas.Role.admin:
        if not user_id == current_user.id:
            raise HTTPException(
                status_code=403, detail="Not enough permissions")

    db_user = db.get(models.User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not current_user.role == schemas.Role.admin or user_id == current_user.id:
        if not verify_password(password.old_password, db_user.hashed_password):
            raise HTTPException(
                status_code=400, detail="Old password is incorrect")

    db_user.hashed_password = get_password_hash(password.new_password)
    db.commit()
    return {"message": "Password changed successfully"}


@app.put("/user/{user_id}/email", tags=["user"], response_model=schemas.UserPublic)
async def change_email(email: schemas.EmailChange, user_id: UUID, current_user: models.User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    if not current_user.role == schemas.Role.admin:
        if not user_id == current_user.id:
            raise HTTPException(
                status_code=403, detail="Not enough permissions")

    db_user = db.get(models.User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not current_user.role == schemas.Role.admin or user_id == current_user.id:
        if not verify_password(email.password, db_user.hashed_password):
            raise HTTPException(
                status_code=400, detail="Password is incorrect")

    db_user.email = email.new_email
    db.commit()
    db.refresh(db_user)
    return db_user


@app.put("/user/{user_id}/role", tags=["user"])
async def change_role(user_id: UUID, role: schemas.RoleChange, current_user: models.User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    if not current_user.role == schemas.Role.admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    db_user = db.get(models.User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if db_user.role == schemas.Role.admin:
        raise HTTPException(
            status_code=403, detail="Cannot change role of admin users")

    db_user.role = role.new_role
    db.commit()
    return {"message": "Role changed successfully"}


@app.get("/users", tags=["users"], response_model=list[schemas.UserPublic])
async def get_users(skip: int = 0, limit: int = 100, role: schemas.Role | None = None, db: Session = Depends(database.get_db)):
    query = db.query(models.User)
    if role:
        query = query.filter(models.User.role == role)

    users = query.order_by(models.User.created_at.desc()).offset(
        skip).limit(limit).all()
    return users
