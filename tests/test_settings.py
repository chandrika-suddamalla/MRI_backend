import os

from app.core.settings import Settings, settings


def test_settings_exposes_non_sensitive_values(monkeypatch):
    monkeypatch.setenv("APP_NAME", "Test App")
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("JWT_ALGORITHM", "HS512")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "45")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("DATABASE_NAME", "test.db")

    config = Settings()

    assert config.app_name == "Test App"
    assert config.environment == "testing"
    assert config.jwt_algorithm == "HS512"
    assert config.access_token_expires_minutes == 45
    assert config.log_level == "DEBUG"
    assert config.database_name == "test.db"


def test_settings_exposes_secrets_via_secrets_manager(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "secret-value")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-value")
    monkeypatch.setenv("DATABASE_PASSWORD", "db-pass")

    config = Settings()

    assert config.secrets.get_jwt_secret() == "secret-value"
    assert config.secrets.get_gemini_api_key() == "gemini-value"
    assert config.secrets.get_database_password() == "db-pass"


def test_module_level_settings_object_exists():
    assert settings is not None
    assert settings.app_name
