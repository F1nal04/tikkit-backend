"""Endpoints to view the change history of tickets."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from ..core import database
from ..schemas import TicketHistoryPublic, TicketWithHistory, TicketPublic
from .. import models

router = APIRouter(prefix="", tags=["history"])


@router.get("/ticket/{ticket_id}/history", response_model=list[TicketHistoryPublic])
async def get_ticket_history(ticket_id: UUID, db: Session = Depends(database.get_db)):
    """Retrieve all history entries for a ticket.

    Args:
        ticket_id (UUID): Identifier of the ticket.
        db (Session): Database session used for queries.

    Returns:
        list[TicketHistoryPublic]: Ordered list of history records.
    """
    # Verify ticket exists
    db_ticket = db.get(models.Ticket, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Get history entries ordered by date (newest first)
    history_entries = db.query(models.TicketHistory).filter(
        models.TicketHistory.ticket_id == ticket_id
    ).order_by(models.TicketHistory.changed_at.desc()).all()

    return history_entries


@router.get("/ticket/{ticket_id}/with-history", tags=["ticket"], response_model=TicketWithHistory)
async def read_ticket_with_history(ticket_id: UUID, db: Session = Depends(database.get_db)):
    """Return ticket information together with its history.

    Args:
        ticket_id (UUID): Identifier of the ticket.
        db (Session): Database session used to load ticket and history.

    Returns:
        TicketWithHistory: The ticket and its associated history entries.
    """
    db_ticket = db.get(models.Ticket, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Get history entries
    history_entries = db.query(models.TicketHistory).filter(
        models.TicketHistory.ticket_id == ticket_id
    ).order_by(models.TicketHistory.changed_at.desc()).all()

    # Convert to response model
    ticket_data = TicketPublic.model_validate(db_ticket)
    return TicketWithHistory(
        **ticket_data.model_dump(),
        history=[TicketHistoryPublic.model_validate(
            entry) for entry in history_entries]
    )
