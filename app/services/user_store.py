from __future__ import annotations

from typing import Any

from app.database.cosmos import CosmosStore, store


class UserStore:
    """User repository backed by Cosmos DB."""

    def __init__(self, repository: CosmosStore | None = None) -> None:
        self.repository = repository or store

    def get_user(self, email: str) -> dict[str, Any] | None:
        return self.repository.get_user(email.lower())

    def create_user(self, email: str, password_hash: str) -> dict[str, Any]:
        return self.repository.create_user(email.lower(), password_hash)
