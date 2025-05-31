from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timezone
from . import models, schemas
import json


def format_value_for_display(field_name: str, value) -> str:
    """Format field values for human-readable display in history."""
    if value is None:
        return "None"

    # Handle enum values
    if hasattr(value, 'value'):
        return value.value

    # Handle UUID values (convert to user names where applicable)
    if isinstance(value, UUID):
        return str(value)

    # Handle other types
    return str(value)


def get_user_name_by_id(db: Session, user_id: UUID) -> str:
    """Get user name by ID for better history display."""
    if user_id is None:
        return "None"

    user = db.get(models.User, user_id)
    return user.name if user else f"Unknown User ({user_id})"


def format_value_with_names(db: Session, field_name: str, value) -> str:
    """Format field values with user names for better readability."""
    if value is None:
        return "None"

    # Handle enum values
    if hasattr(value, 'value'):
        return value.value

    # Handle user ID fields - convert to names
    if field_name in ['assigned_to', 'author', 'changed_by'] and isinstance(value, (UUID, str)):
        try:
            user_id = UUID(str(value))
            return get_user_name_by_id(db, user_id)
        except (ValueError, TypeError):
            return str(value)

    return str(value)


def record_ticket_creation(db: Session, ticket: models.Ticket, created_by: UUID):
    """Record the initial creation of a ticket."""
    history_entry = models.TicketHistory(
        ticket_id=ticket.id,
        changed_by=created_by,
        field_name="ticket",
        old_value=None,
        new_value="Ticket created",
        change_type="created",
        changed_at=datetime.now(timezone.utc)
    )
    db.add(history_entry)


def record_ticket_changes(db: Session, ticket_id: UUID, old_ticket: models.Ticket,
                          new_data: dict, changed_by: UUID):
    """Record changes made to a ticket by comparing old and new values."""

    # Fields to track for changes
    trackable_fields = {
        'topic': 'Topic',
        'description': 'Description',
        'message': 'Message',
        'status': 'Status',
        'priority': 'Priority',
        'assigned_to': 'Assigned To'
    }

    for field_name, display_name in trackable_fields.items():
        if field_name in new_data:
            old_value = getattr(old_ticket, field_name)
            new_value = new_data[field_name]

            # Only record if there's actually a change
            if old_value != new_value:
                # Format values for better display
                old_display = format_value_with_names(
                    db, field_name, old_value)
                new_display = format_value_with_names(
                    db, field_name, new_value)

                history_entry = models.TicketHistory(
                    ticket_id=ticket_id,
                    changed_by=changed_by,
                    field_name=display_name,
                    old_value=old_display,
                    new_value=new_display,
                    change_type="updated",
                    changed_at=datetime.now(timezone.utc)
                )
                db.add(history_entry)


def record_ticket_assignment(db: Session, ticket_id: UUID, old_assigned_to: UUID | None,
                             new_assigned_to: UUID, changed_by: UUID):
    """Record ticket assignment changes."""
    old_display = format_value_with_names(db, 'assigned_to', old_assigned_to)
    new_display = format_value_with_names(db, 'assigned_to', new_assigned_to)

    history_entry = models.TicketHistory(
        ticket_id=ticket_id,
        changed_by=changed_by,
        field_name="Assigned To",
        old_value=old_display,
        new_value=new_display,
        change_type="updated",
        changed_at=datetime.now(timezone.utc)
    )
    db.add(history_entry)


def record_ticket_status_change(db: Session, ticket_id: UUID, old_status: schemas.Status,
                                new_status: schemas.Status, changed_by: UUID):
    """Record ticket status changes."""
    history_entry = models.TicketHistory(
        ticket_id=ticket_id,
        changed_by=changed_by,
        field_name="Status",
        old_value=old_status.value,
        new_value=new_status.value,
        change_type="updated",
        changed_at=datetime.now(timezone.utc)
    )
    db.add(history_entry)


def record_ticket_deletion(db: Session, ticket_id: UUID, deleted_by: UUID):
    """Record ticket deletion."""
    history_entry = models.TicketHistory(
        ticket_id=ticket_id,
        changed_by=deleted_by,
        field_name="ticket",
        old_value="Ticket existed",
        new_value="Ticket deleted",
        change_type="deleted",
        changed_at=datetime.now(timezone.utc)
    )
    db.add(history_entry)
