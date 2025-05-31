"""
Schema definitions for the TikKit API.

This package contains all Pydantic models used for request/response validation
and serialization throughout the application.
"""

# Import all schemas to maintain backward compatibility
from .enums import Status, Priority, Topic, Role
from .auth import Token, PasswordChange, EmailChange, RoleChange
from .users import UserBase, UserCreate, User, UserPublic, UserUpdate
from .tickets import TicketBase, TicketCreate, Ticket, TicketPublic, TicketUpdate

__all__ = [
    # Enums
    "Status",
    "Priority",
    "Topic",
    "Role",
    # Auth schemas
    "Token",
    "PasswordChange",
    "EmailChange",
    "RoleChange",
    # User schemas
    "UserBase",
    "UserCreate",
    "User",
    "UserPublic",
    "UserUpdate",
    # Ticket schemas
    "TicketBase",
    "TicketCreate",
    "Ticket",
    "TicketPublic",
    "TicketUpdate",
]
