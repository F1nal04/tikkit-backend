from pydantic import BaseModel, field_validator, EmailStr, ConfigDict
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


class ChangeType(Enum):
    created = "created"
    updated = "updated"
    deleted = "deleted"


class Token(BaseModel):
    access_token: str
    token_type: str


class TicketHistoryBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    field_name: str
    old_value: str | None
    new_value: str | None
    change_type: ChangeType


class TicketHistory(TicketHistoryBase):
    id: UUID
    ticket_id: UUID
    changed_by: UUID
    changed_at: datetime


class TicketHistoryPublic(TicketHistory):
    changed_by_name: str


class TicketBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    assigned_to_name: str | None
    author_name: str


class TicketWithHistory(TicketPublic):
    history: list[TicketHistoryPublic] = []


class TicketUpdate(TicketBase):
    topic: Topic | None = None
    description: str | None = None
    message: str | None = None
    priority: Priority | None = None
    status: Status | None = None
    assigned_to: UUID | None = None


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: EmailStr
    name: str

    @field_validator('name')
    @classmethod
    def validate_name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v


class UserCreate(UserBase):
    password: str

    @field_validator('password')
    @classmethod
    def validate_password_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Password cannot be empty')
        return v


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


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


class EmailChange(BaseModel):
    password: str
    new_email: str


class RoleChange(BaseModel):
    new_role: Role
