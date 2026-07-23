from __future__ import annotations

import json
from pathlib import Path
from typing import Any

USER_STORE_PATH = Path(__file__).resolve().parent.parent / "storage" / "users.json"


class UserStore:
    """Simple JSON-backed user store for local development."""

    def __init__(self, file_path: Path | None = None) -> None:
        self.file_path = file_path or USER_STORE_PATH
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.write_text('{"users": []}\n', encoding="utf-8")

    def _read(self) -> dict[str, Any]:
        with self.file_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write(self, data: dict[str, Any]) -> None:
        with self.file_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")

    def get_user(self, email: str) -> dict[str, Any] | None:
        user_data = self._read()
        for user in user_data.get("users", []):
            if user.get("email") == email:
                return user
        return None

    def create_user(self, email: str, password_hash: str) -> dict[str, Any]:
        user_data = self._read()
        if self.get_user(email):
            raise ValueError("User already exists")

        user = {"email": email, "password": password_hash}
        user_data.setdefault("users", []).append(user)
        self._write(user_data)
        return user
