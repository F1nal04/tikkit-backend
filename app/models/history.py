"""
History model definition for the TikKit API.

Contains the TicketHistory SQLAlchemy model for database operations.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID, Column, ForeignKey, String, Text, DateTime
from sqlalchemy.orm import relationship

from .base import Base


class TicketHistory(Base):
    """Ticket history database model."""
    __tablename__ = "ticket_history"

    id = Column(UUID, primary_key=True, index=True, default=uuid4)
    ticket_id = Column(UUID, ForeignKey("tickets.id"), nullable=False)
    changed_by = Column(UUID, ForeignKey("users.id"), nullable=False)
    # e.g., "status", "assigned_to", "priority"
    field_name = Column(String, nullable=False)
    old_value = Column(Text, nullable=True)  # JSON string or simple value
    new_value = Column(Text, nullable=True)  # JSON string or simple value
    # "created", "updated", "deleted"
    change_type = Column(String, nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    ticket = relationship("Ticket", back_populates="history")
    changed_by_user = relationship("User", foreign_keys=[changed_by])

    @property
    def changed_by_name(self):
        """Get the name of the user who made the change."""
        return self.changed_by_user.name if self.changed_by_user else "Unknown"
