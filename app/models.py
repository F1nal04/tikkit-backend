from datetime import date
from uuid import uuid4

from sqlalchemy import UUID, Column, Text, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column

from schemas import Topic, Status, Priority

Base = declarative_base()


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(UUID, primary_key=True, index=True, default=uuid4)  # For UUID
    topic: Mapped[Topic] = mapped_column(
        nullable=False)
    description = Column(Text, nullable=False)
    message = Column(Text, nullable=True)
    status: Mapped[Status] = mapped_column(default=Status.open)
    priority: Mapped[Priority] = mapped_column(
        nullable=False)
    assigned_to = Column(UUID, nullable=True)
    author = Column(UUID, nullable=False)
    created_at = Column(Date, default=date.today())
    updated_at = Column(Date, default=date.today(),
                        onupdate=date.today())
