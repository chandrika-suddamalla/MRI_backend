from __future__ import annotations

from app.database.cosmos import CosmosStore, store


class HistoryService:
    """Service for retrieving persisted research reports."""

    def __init__(self, repository: CosmosStore | None = None) -> None:
        self.repository = repository or store

    def get_history(self, user_id: str) -> list[dict]:
        return self.repository.list_reports(user_id)
