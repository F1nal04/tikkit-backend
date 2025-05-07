from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from enum import Enum


class Status(Enum):
    open = "open"
    in_progress = "in_progress"
    closed = "closed"
    hold = "hold"


class Priority(Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Topic(Enum):
    printer = "printer"
    nas = "nas"
    wifi = "wifi"
    lan = "lan"
    macbook = "macbook"
    imac = "imac"
    other = "other"


class TicketBase(BaseModel):
    topic: Topic
    description: str
    message: str | None
    priority: Priority
    author: UUID


class TicketCreate(TicketBase):
    pass


class Ticket(TicketBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    status: Status
    assigned_to: UUID | None


class TicketPublic(Ticket):
    pass


class TicketUpdate(TicketBase):
    topic: Topic | None = None
    description: str | None = None
    message: str | None = None
    priority: Priority | None = None
    status: Status | None = None
    assigned_to: UUID | None = None
    author: UUID | None = None
