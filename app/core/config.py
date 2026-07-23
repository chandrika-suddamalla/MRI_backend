from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

backend_root = Path(__file__).resolve().parents[2]
workspace_root = Path(__file__).resolve().parents[3]

for env_path in [backend_root / ".env", backend_root / ".env.example", workspace_root / ".env"]:
    if env_path.exists():
        load_dotenv(env_path, override=True)
        break
else:
    load_dotenv(override=True)


@dataclass(frozen=True)
class AppConfig:
    """Configuration values that are safe to expose and do not contain secrets."""

    app_name: str
    environment: str
    jwt_algorithm: str
    access_token_expires_minutes: int
    log_level: str
    database_name: str
    api_prefix: str
    app_version: str
    debug: bool
    allowed_origins: tuple[str, ...]

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            app_name=os.getenv("APP_NAME", "Market Research Intelligence Assistant"),
            environment=os.getenv("ENVIRONMENT", "development"),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            access_token_expires_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            database_name=os.getenv("DATABASE_NAME", "market_research.db"),
            api_prefix=os.getenv("API_PREFIX", "/api"),
            app_version=os.getenv("APP_VERSION", "0.1.0"),
            debug=os.getenv("DEBUG", "true").lower() == "true",
            allowed_origins=tuple(
                origin.strip()
                for origin in os.getenv(
                    "ALLOWED_ORIGINS",
                    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
                ).split(",")
                if origin.strip()
            ),
        )
