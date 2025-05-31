"""
User schema definitions for the TikKit API.

Contains Pydantic models for user creation, updates, and responses.
Includes validation for user data integrity.
"""

from pydantic import BaseModel, field_validator, EmailStr
from datetime import datetime
from uuid import UUID
from .enums import Role


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    name: str

    @field_validator('name')
    @classmethod
    def validate_name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v


class UserCreate(UserBase):
    """Schema for user creation requests."""
    password: str

    @field_validator('password')
    @classmethod
    def validate_password_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Password cannot be empty')
        return v


class User(UserBase):
    """Complete user schema with all database fields."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    role: Role


class UserPublic(User):
    """Public user schema for API responses."""
    pass


class UserUpdate(UserBase):
    """Schema for user update requests with optional fields."""
    email: str | None = None
    password: str | None = None
    role: Role | None = None
    name: str | None = None
