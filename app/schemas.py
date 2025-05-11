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


class Role(Enum):
    admin = "admin"
    worker = "worker"
    user = "user"
    inactive = "inactive"
    deactivated = "deactivated"


class Token(BaseModel):
    access_token: str
    token_type: str


class TicketBase(BaseModel):
    topic: Topic
    description: str
    message: str | None
    priority: Priority


class TicketCreate(TicketBase):
    pass


class Ticket(TicketBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    status: Status
    assigned_to: UUID | None
    author: UUID


class TicketPublic(Ticket):
    pass


class TicketUpdate(TicketBase):
    topic: Topic | None = None
    description: str | None = None
    message: str | None = None
    priority: Priority | None = None
    status: Status | None = None
    assigned_to: UUID | None = None


class UserBase(BaseModel):
    email: str
    name: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    role: Role


class UserPublic(User):
    pass


class UserUpdate(UserBase):
    email: str | None = None
    password: str | None = None
    role: Role | None = None
    name: str | None = None
