from __future__ import annotations

from app.core.config import AppConfig


def test_backend_reads_runtime_environment_variables_only(monkeypatch) -> None:
    monkeypatch.setenv("APP_NAME", "Runtime App")
    monkeypatch.setenv("JWT_EXPIRY_MINUTES", "90")

    config = AppConfig.from_env()

    assert config.app_name == "Runtime App"
    assert config.access_token_expires_minutes == 90
