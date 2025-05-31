"""
Base database configuration for the TikKit API.

Contains the SQLAlchemy declarative base that all models inherit from.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()
