from datetime import date
from uuid import uuid4

from sqlalchemy import UUID, Boolean, Column, ForeignKey, String, Text, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column

from schemas import Topic, Status, Priority, Role

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
    author = Column(UUID, ForeignKey("users.id"), nullable=False)
    created_at = Column(Date, default=date.today)
    updated_at = Column(Date, default=date.today,
                        onupdate=date.today)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID, primary_key=True, index=True, default=uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    role: Mapped[Role] = mapped_column(default=Role.user)
    created_at = Column(Date, default=date.today)
    updated_at = Column(Date, default=date.today,
                        onupdate=date.today)
