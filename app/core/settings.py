from __future__ import annotations

from app.core.config import AppConfig
from app.core.secrets import LocalSecretsManager, SecretsManager


class Settings:
    """Central entry point for application configuration and secrets."""

    def __init__(self, config: AppConfig | None = None, secrets: SecretsManager | None = None) -> None:
        self._config = config or AppConfig.from_env()
        self._secrets = secrets or LocalSecretsManager()

    @property
    def app_name(self) -> str:
        return self._config.app_name

    @property
    def environment(self) -> str:
        return self._config.environment

    @property
    def jwt_algorithm(self) -> str:
        return self._config.jwt_algorithm

    @property
    def access_token_expires_minutes(self) -> int:
        return self._config.access_token_expires_minutes

    @property
    def log_level(self) -> str:
        return self._config.log_level

    @property
    def database_name(self) -> str:
        return self._config.database_name

    @property
    def api_prefix(self) -> str:
        return self._config.api_prefix

    @property
    def app_version(self) -> str:
        return self._config.app_version

    @property
    def debug(self) -> bool:
        return self._config.debug

    @property
    def allowed_origins(self) -> tuple[str, ...]:
        return self._config.allowed_origins

    @property
    def secrets(self) -> SecretsManager:
        return self._secrets


settings = Settings()
