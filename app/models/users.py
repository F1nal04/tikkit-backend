"""
User model definition for the TikKit API.

Contains the User SQLAlchemy model for database operations.
"""

from datetime import date
from uuid import uuid4

from sqlalchemy import UUID, Column, String, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from ..schemas.enums import Role


class User(Base):
    """User database model."""
    __tablename__ = "users"

    id = Column(UUID, primary_key=True, index=True, default=uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    role: Mapped[Role] = mapped_column(default=Role.user)
    tickets = relationship(
        "Ticket", foreign_keys="[Ticket.author]", back_populates="author_user")
    created_at = Column(Date, default=date.today)
    updated_at = Column(Date, default=date.today, onupdate=date.today)
