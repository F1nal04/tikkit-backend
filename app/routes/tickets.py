from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from ..core import database
from ..core.security import get_current_active_user
from ..schemas.enums import Role, Status, Priority, Topic
from ..schemas.tickets import TicketCreate, TicketPublic, TicketUpdate
from ..models.users import User
from ..models.tickets import Ticket

router = APIRouter(prefix="", tags=["ticket", "tickets"])


@router.post("/ticket", tags=["ticket"], response_model=TicketPublic)
async def create_ticket(ticket: TicketCreate, current_user: User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    db_ticket = Ticket(**ticket.model_dump())
    db_ticket.author = current_user.id
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


@router.get("/ticket/{ticket_id}", tags=["ticket"], response_model=TicketPublic)
async def read_ticket(ticket_id: UUID, db: Session = Depends(database.get_db)):
    db_ticket = db.get(Ticket, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return db_ticket


@router.put("/ticket/{ticket_id}", tags=["ticket"], response_model=TicketPublic)
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


@router.delete("/ticket/{ticket_id}", tags=["ticket"])
async def delete_ticket(ticket_id: UUID, current_user: User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    db_ticket = db.get(Ticket, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if not current_user.role == Role.admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    db.delete(db_ticket)
    db.commit()
    return {"message": "Ticket deleted successfully"}


@router.put("/ticket/{ticket_id}/assign", tags=["ticket"], response_model=TicketPublic)
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


@router.put("/ticket/{ticket_id}/status", tags=["ticket"], response_model=TicketPublic)
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


@router.get("/tickets", tags=["tickets"], response_model=list[TicketPublic])
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
