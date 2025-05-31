"""
Ticket schema definitions for the TikKit API.

Contains Pydantic models for ticket creation, updates, and responses.
Handles ticket lifecycle and assignment management.
"""

from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from .enums import Status, Priority, Topic


class TicketBase(BaseModel):
    """Base ticket schema with common fields."""
    topic: Topic
    description: str
    message: str | None
    priority: Priority


class TicketCreate(TicketBase):
    """Schema for ticket creation requests."""
    pass


class Ticket(TicketBase):
    """Complete ticket schema with all database fields."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    status: Status
    assigned_to: UUID | None
    author: UUID


class TicketPublic(Ticket):
    """Public ticket schema with resolved user names."""
    assigned_to_name: str | None
    author_name: str


class TicketUpdate(TicketBase):
    """Schema for ticket update requests with optional fields."""
    topic: Topic | None = None
    description: str | None = None
    message: str | None = None
    priority: Priority | None = None
    status: Status | None = None
    assigned_to: UUID | None = None
