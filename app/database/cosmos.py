from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import uuid4

from app.core.settings import settings


class CosmosStore:
    """Persist users and research reports in Azure Cosmos DB.

    When Cosmos settings are absent, a process-local store is used for local
    development and tests. It is intentionally not durable.
    """

    def __init__(
        self,
        endpoint: str = "",
        key: str = "",
        database_name: str = "mi-db",
        users_container_name: str = "users",
        reports_container_name: str = "reports",
    ) -> None:
        self._memory_users: dict[str, dict[str, Any]] = {}
        self._memory_reports: list[dict[str, Any]] = []
        self._lock = Lock()
        self._users_container = None
        self._reports_container = None

        endpoint = "" if endpoint in {"replace_me", "replace-me"} else endpoint
        key = "" if key in {"replace_me", "replace-me"} else key

        if bool(endpoint) != bool(key):
            raise RuntimeError("COSMOS_ENDPOINT and COSMOS_KEY must be configured together")

        if endpoint and key:
            try:
                from azure.cosmos import CosmosClient
            except ImportError as exc:
                raise RuntimeError("azure-cosmos is required when Cosmos DB is configured") from exc

            client = CosmosClient(endpoint, credential=key)
            database = client.get_database_client(database_name)
            self._users_container = database.get_container_client(users_container_name)
            self._reports_container = database.get_container_client(reports_container_name)

    @property
    def is_cosmos_configured(self) -> bool:
        return self._users_container is not None and self._reports_container is not None

    def get_user(self, email: str) -> dict[str, Any] | None:
        if self.is_cosmos_configured:
            try:
                return dict(self._users_container.read_item(item=email, partition_key=email))
            except Exception as exc:
                if exc.__class__.__name__ != "CosmosResourceNotFoundError":
                    raise
                return None

        with self._lock:
            user = self._memory_users.get(email)
            return dict(user) if user else None

    def create_user(self, email: str, password_hash: str) -> dict[str, Any]:
        user = {"id": email, "email": email, "password": password_hash, "role": "Analyst"}
        if self.is_cosmos_configured:
            try:
                return dict(self._users_container.create_item(body=user))
            except Exception as exc:
                if exc.__class__.__name__ == "CosmosResourceExistsError":
                    raise ValueError("User already exists") from exc
                raise

        with self._lock:
            if email in self._memory_users:
                raise ValueError("User already exists")
            self._memory_users[email] = user
            return dict(user)

    def save_report(self, user_id: str, report: dict[str, Any]) -> dict[str, Any]:
        document = {
            "id": str(uuid4()),
            "userId": user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **report,
        }
        if self.is_cosmos_configured:
            return dict(self._reports_container.create_item(body=document))

        with self._lock:
            self._memory_reports.append(document)
            return dict(document)

    def list_reports(self, user_id: str) -> list[dict[str, Any]]:
        if self.is_cosmos_configured:
            query = "SELECT * FROM c WHERE c.userId = @userId ORDER BY c.created_at DESC"
            items = self._reports_container.query_items(
                query=query,
                parameters=[{"name": "@userId", "value": user_id}],
                partition_key=user_id,
            )
            return [dict(item) for item in items]

        with self._lock:
            reports = [dict(item) for item in self._memory_reports if item.get("userId") == user_id]
        return sorted(reports, key=lambda item: item.get("created_at", ""), reverse=True)


store = CosmosStore(
    endpoint=settings.cosmos_endpoint,
    key=settings.secrets.get_cosmos_key(),
    database_name=settings.cosmos_database_name,
    users_container_name=settings.cosmos_users_container,
    reports_container_name=settings.cosmos_reports_container,
)
