from __future__ import annotations

from sqlalchemy import Column, Integer, String, Text
from app.database.database import Base


class ResearchReport(Base):
    """Placeholder research report model for future persistence."""

    __tablename__ = "research_reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)
