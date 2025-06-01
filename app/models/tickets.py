"""
Ticket model definition for the TikKit API.

Contains the Ticket SQLAlchemy model for database operations.
"""

from datetime import date
from uuid import uuid4

from sqlalchemy import UUID, Column, ForeignKey, Text, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from ..schemas.enums import Topic, Status, Priority


class Ticket(Base):
    """Ticket database model."""
    __tablename__ = "tickets"

    id = Column(UUID, primary_key=True, index=True, default=uuid4)
    topic: Mapped[Topic] = mapped_column(nullable=False)
    description = Column(Text, nullable=False)
    message = Column(Text, nullable=True)
    status: Mapped[Status] = mapped_column(default=Status.open)
    priority: Mapped[Priority] = mapped_column(nullable=False)
    assigned_to = Column(UUID, ForeignKey("users.id"), nullable=True)
    assigned_to_user = relationship("User", foreign_keys=[assigned_to])
    author = Column(UUID, ForeignKey("users.id"), nullable=False)
    author_user = relationship("User", foreign_keys=[
                               author], back_populates="tickets")
    created_at = Column(Date, default=date.today)
    updated_at = Column(Date, default=date.today, onupdate=date.today)

    # Relationship to history entries
    history = relationship(
        "TicketHistory", back_populates="ticket", cascade="all, delete-orphan")

    @property
    def author_name(self):
        """Get the name of the ticket author."""
        return self.author_user.name

    @property
    def assigned_to_name(self):
        """Get the name of the assigned user, if any."""
        return self.assigned_to_user.name if self.assigned_to_user else None
