# MI_backend
Market Research Intelligence Backend

## Configuration and Secrets

The Python application reads configuration exclusively from environment
variables. It does not load `.env` files in the deployed container.

Terraform places non-sensitive settings directly on the Azure Container App and
stores sensitive values in Azure Key Vault. The Container App system identity
reads the Key Vault-backed secrets at runtime. Secret inputs for Terraform must
be supplied through `TF_VAR_*` environment variables or a secure CI/CD secret
store, never through `terraform.tfvars`.

Sensitive values include the Cosmos primary key, JWT signing secret, model API
keys, and ACR credentials. The local `.env` file is only for developer-managed
runtime configuration and must not be included in a container image.

## Persistence

The API stores users and generated research reports in Azure Cosmos DB when
these environment variables are configured:

```text
COSMOS_ENDPOINT=https://<account>.documents.azure.com:443/
COSMOS_DATABASE_NAME=mi-db
COSMOS_USERS_CONTAINER=users
COSMOS_REPORTS_CONTAINER=reports
```

The Terraform Container App injects these values from the provisioned Cosmos
account. The `users` container uses `/email` as its partition key, and the
`reports` container uses `/userId`; history queries are therefore scoped to the
authenticated user's email.

When Cosmos settings are absent, local development and tests use a process-local
in-memory adapter. This adapter is not durable.

## Run locally

```powershell
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Register through `POST /api/auth/register`, authenticate with
`POST /api/auth/login`, create reports through `POST /api/research`, and read
the authenticated user's saved reports with `GET /api/history`.
