"""
Enum definitions for the TikKit API.

Contains all enumeration types used throughout the application for
status tracking, priorities, topics, and user roles.
"""

from enum import Enum


class Status(Enum):
    """Ticket status enumeration."""
    open = "open"
    in_progress = "in_progress"
    closed = "closed"
    hold = "hold"


class Priority(Enum):
    """Ticket priority enumeration."""
    low = "low"
    medium = "medium"
    high = "high"


class Topic(Enum):
    """Ticket topic/category enumeration."""
    printer = "printer"
    nas = "nas"
    wifi = "wifi"
    lan = "lan"
    macbook = "macbook"
    imac = "imac"
    other = "other"


class Role(Enum):
    """User role enumeration."""
    admin = "admin"
    worker = "worker"
    user = "user"
    inactive = "inactive"
    deactivated = "deactivated"
