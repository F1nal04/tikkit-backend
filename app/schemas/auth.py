"""
Authentication schema definitions for the TikKit API.

Contains Pydantic models for authentication tokens, password changes,
email changes, and role changes.
"""

from pydantic import BaseModel
from .enums import Role


class Token(BaseModel):
    """JWT token response schema."""
    access_token: str
    token_type: str


class PasswordChange(BaseModel):
    """Schema for password change requests."""
    old_password: str
    new_password: str


class EmailChange(BaseModel):
    """Schema for email change requests."""
    password: str
    new_email: str


class RoleChange(BaseModel):
    """Schema for role change requests."""
    new_role: Role
