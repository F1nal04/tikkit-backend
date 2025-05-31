from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import UUID, Boolean, Column, ForeignKey, String, Text, Date, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .schemas import Topic, Status, Priority, Role

Base = declarative_base()


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(UUID, primary_key=True, index=True, default=uuid4)
    topic: Mapped[Topic] = mapped_column(
        nullable=False)
    description = Column(Text, nullable=False)
    message = Column(Text, nullable=True)
    status: Mapped[Status] = mapped_column(default=Status.open)
    priority: Mapped[Priority] = mapped_column(
        nullable=False)
    assigned_to = Column(UUID, ForeignKey("users.id"), nullable=True)
    assigned_to_user = relationship(
        "User", foreign_keys=[assigned_to])
    author = Column(UUID, ForeignKey("users.id"), nullable=False)
    author_user = relationship("User", foreign_keys=[
                               author], back_populates="tickets")
    created_at = Column(Date, default=date.today)
    updated_at = Column(Date, default=date.today,
                        onupdate=date.today)

    # Relationship to history entries
    history = relationship(
        "TicketHistory", back_populates="ticket", cascade="all, delete-orphan")

    @property
    def author_name(self):
        return self.author_user.name

    @property
    def assigned_to_name(self):
        return self.assigned_to_user.name if self.assigned_to_user else None


class TicketHistory(Base):
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
        return self.changed_by_user.name if self.changed_by_user else "Unknown"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID, primary_key=True, index=True, default=uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    role: Mapped[Role] = mapped_column(default=Role.user)
    tickets = relationship("Ticket", foreign_keys=[
                           Ticket.author], back_populates="author_user")
    created_at = Column(Date, default=date.today)
    updated_at = Column(Date, default=date.today,
                        onupdate=date.today)
