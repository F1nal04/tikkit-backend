from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from ..core import database
from ..core.security import get_current_active_user
from ..schemas import TicketCreate, TicketPublic, TicketUpdate, Status, Priority, Topic, Role
from .. import models, history

router = APIRouter(prefix="", tags=["ticket", "tickets"])


@router.post("/ticket", tags=["ticket"], response_model=TicketPublic)
async def create_ticket(ticket: TicketCreate, current_user: models.User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    db_ticket = models.Ticket(**ticket.model_dump())
    db_ticket.author = current_user.id
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)

    # Record ticket creation in history
    history.record_ticket_creation(db, db_ticket, current_user.id)
    db.commit()

    return db_ticket


@router.get("/ticket/{ticket_id}", tags=["ticket"], response_model=TicketPublic)
async def read_ticket(ticket_id: UUID, db: Session = Depends(database.get_db)):
    db_ticket = db.get(models.Ticket, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return db_ticket


@router.put("/ticket/{ticket_id}", tags=["ticket"], response_model=TicketPublic)
async def update_ticket(ticket_id: UUID, ticket: TicketUpdate, current_user: models.User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    db_ticket = db.get(models.Ticket, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if not current_user.role == Role.admin:
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


@router.delete("/ticket/{ticket_id}", tags=["ticket"])
async def delete_ticket(ticket_id: UUID, current_user: models.User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    db_ticket = db.get(models.Ticket, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if not current_user.role == Role.admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Record deletion in history before deleting
    history.record_ticket_deletion(db, ticket_id, current_user.id)

    db.delete(db_ticket)
    db.commit()
    return {"message": "Ticket deleted successfully"}


@router.put("/ticket/{ticket_id}/assign", tags=["ticket"], response_model=TicketPublic)
async def assign_ticket(ticket_id: UUID, assigned_to: UUID, current_user: models.User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    db_ticket = db.get(models.Ticket, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if not ((current_user.role == Role.admin) or (current_user.id == assigned_to and db_ticket.assigned_to is None)):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Record assignment change in history
    old_assigned_to = db_ticket.assigned_to
    history.record_ticket_assignment(
        db, ticket_id, old_assigned_to, assigned_to, current_user.id)

    db_ticket.assigned_to = assigned_to
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


@router.put("/ticket/{ticket_id}/status", tags=["ticket"], response_model=TicketPublic)
async def update_ticket_status(ticket_id: UUID, status: Status, current_user: models.User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    db_ticket = db.get(models.Ticket, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if not ((current_user.role == Role.admin) or (current_user.id == db_ticket.author and status == Status.closed) or (current_user.id == db_ticket.assigned_to)):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Record status change in history
    old_status = db_ticket.status
    history.record_ticket_status_change(
        db, ticket_id, old_status, status, current_user.id)

    db_ticket.status = status
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


@router.get("/tickets", tags=["tickets"], response_model=list[TicketPublic])
async def read_tickets(skip: int = 0, limit: int = 100, status: Status = None, priority: Priority = None, assigned_to: UUID = None, author: UUID = None, topic: Topic = None,  db: Session = Depends(database.get_db)):
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
