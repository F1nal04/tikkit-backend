from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
import models
import schemas
import database
from fastapi.security import OAuth2PasswordRequestForm
from security import verify_password, create_access_token
from sqlalchemy.exc import IntegrityError
from security import get_password_hash

# Create the database tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="Ticket System API",
    description="A REST API for managing IT support tickets",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "ticket",
            "description": "Operations with a single ticket. The **ticket** endpoint allows you to create, read, update and delete a ticket.",
        },
        {
            "name": "tickets",
            "description": "Operations with multiple tickets. The **tickets** endpoint allows you to read all tickets.",
        }
    ]
)


@app.post("/register", tags=["auth"], response_model=schemas.Token)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    hashed_password = get_password_hash(user.password)
    del user.password

    db_user = models.User(**user.model_dump())
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


@app.post("/login", tags=["auth"], response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    client_id = db.query(models.User).filter(
        models.User.email == form_data.username).first().id
    user = db.get(models.User, client_id)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=400, detail="Incorrect email or password")
    access_token = create_access_token({"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/ticket", tags=["ticket"], response_model=schemas.TicketPublic)
def create_ticket(ticket: schemas.TicketCreate, db: Session = Depends(database.get_db)):
    db_ticket = models.Ticket(**ticket.model_dump())
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


@app.get("/ticket/{ticket_id}", tags=["ticket"], response_model=schemas.TicketPublic)
def read_ticket(ticket_id: UUID, db: Session = Depends(database.get_db)):
    db_ticket = db.get(models.Ticket, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return db_ticket


@app.put("/ticket/{ticket_id}", tags=["ticket"], response_model=schemas.TicketPublic)
def update_ticket(ticket_id: UUID, ticket: schemas.TicketUpdate, db: Session = Depends(database.get_db)):
    db_ticket = db.get(models.Ticket, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    update_data = ticket.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_ticket, field, value)

    db.commit()
    db.refresh(db_ticket)
    return db_ticket


@app.delete("/ticket/{ticket_id}", tags=["ticket"])
def delete_ticket(ticket_id: UUID, db: Session = Depends(database.get_db)):
    db_ticket = db.get(models.Ticket, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    db.delete(db_ticket)
    db.commit()
    return {"message": "Ticket deleted successfully"}


@app.put("/ticket/assign", tags=["ticket"], response_model=schemas.TicketPublic)
def assign_ticket(ticket_id: UUID, assigned_to: UUID, db: Session = Depends(database.get_db)):
    db_ticket = db.get(models.Ticket, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    db_ticket.assigned_to = assigned_to
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


@app.put("/ticket/status", tags=["ticket"], response_model=schemas.TicketPublic)
def update_ticket_status(ticket_id: UUID, status: schemas.Status, db: Session = Depends(database.get_db)):
    db_ticket = db.get(models.Ticket, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    db_ticket.status = status
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


@app.put("/ticket/priority", tags=["ticket"], response_model=schemas.TicketPublic)
def update_ticket_priority(ticket_id: UUID, priority: schemas.Priority, db: Session = Depends(database.get_db)):
    db_ticket = db.get(models.Ticket, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    db_ticket.priority = priority
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


@app.get("/tickets", tags=["tickets"], response_model=list[schemas.TicketPublic])
def read_tickets(skip: int = 0, limit: int = 100, status: schemas.Status = None, priority: schemas.Priority = None, assigned_to: UUID = None, author: UUID = None, topic: schemas.Topic = None,  db: Session = Depends(database.get_db)):
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
