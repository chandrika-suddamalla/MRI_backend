from __future__ import annotations

import os
from abc import ABC, abstractmethod
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


class SecretsManager(ABC):
    """Abstract interface for retrieving sensitive configuration values."""

    @abstractmethod
    def get_jwt_secret(self) -> str:
        """Return the JWT signing secret."""

    @abstractmethod
    def get_gemini_api_key(self) -> str:
        """Return the Gemini API key."""

    @abstractmethod
    def get_database_password(self) -> str:
        """Return the database password."""


class LocalSecretsManager(SecretsManager):
    """Local implementation that reads secrets from environment variables."""

    def get_jwt_secret(self) -> str:
        return os.getenv("JWT_SECRET_KEY", "replace_me")

    def get_gemini_api_key(self) -> str:
        return os.getenv("GEMINI_API_KEY", "replace_me")

    def get_database_password(self) -> str:
        return os.getenv("DATABASE_PASSWORD", "replace_me")


# class AzureKeyVaultSecretsManager(SecretsManager):
#     """Example Azure Key Vault implementation that can replace LocalSecretsManager later."""
#
#     def __init__(self, vault_url: str, credential=None) -> None:
#         self.vault_url = vault_url
#         self.credential = credential
#
#     def get_jwt_secret(self) -> str:
#         # from azure.identity import DefaultAzureCredential
#         # from azure.keyvault.secrets import SecretClient
#         # client = SecretClient(vault_url=self.vault_url, credential=self.credential)
#         # return client.get_secret("jwt-secret").value
#         raise NotImplementedError("Azure Key Vault integration is not implemented yet")
#
#     def get_gemini_api_key(self) -> str:
#         raise NotImplementedError("Azure Key Vault integration is not implemented yet")
#
#     def get_database_password(self) -> str:
#         raise NotImplementedError("Azure Key Vault integration is not implemented yet")
