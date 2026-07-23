from __future__ import annotations

from sqlalchemy import Column, Integer, String
from app.database.database import Base


class User(Base):
    """Placeholder user model for future persistence."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, default="Analyst")
