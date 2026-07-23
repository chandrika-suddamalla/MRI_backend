from __future__ import annotations

from datetime import datetime


class HistoryService:
    """Service containing mock history retrieval logic."""

    def get_history(self) -> list[dict]:
        """Return mock historical reports for now."""
        return [
            {
                "id": 1,
                "title": "Enterprise AI Research",
                "created_at": datetime(2026, 7, 21, 10, 0, 0).isoformat(),
            }
        ]
