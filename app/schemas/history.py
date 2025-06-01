"""
History schema definitions for the TikKit API.

Contains Pydantic models for ticket history tracking and responses.
"""

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID
from .enums import ChangeType


class TicketHistoryBase(BaseModel):
    """Base ticket history schema with common fields."""
    model_config = ConfigDict(from_attributes=True)

    field_name: str
    old_value: str | None
    new_value: str | None
    change_type: ChangeType


class TicketHistory(TicketHistoryBase):
    """Complete ticket history schema with all database fields."""
    id: UUID
    ticket_id: UUID
    changed_by: UUID
    changed_at: datetime


class TicketHistoryPublic(TicketHistory):
    """Public ticket history schema with resolved user names."""
    changed_by_name: str
