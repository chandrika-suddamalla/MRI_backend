# Container App deployment using a placeholder image from ACR.
resource "azurerm_container_app" "mi_app" {
  name                         = local.container_app_name
  container_app_environment_id = azurerm_container_app_environment.mi_env.id
  resource_group_name          = azurerm_resource_group.mi.name
  revision_mode                = "Single"

  ingress {
    external_enabled = true
    target_port      = 8000
    transport        = "auto"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  identity {
    type = "SystemAssigned"
  }

  # Key Vault-backed secrets are resolved by the Container App system identity.
  secret {
    name                = "cosmos-key"
    key_vault_secret_id = azurerm_key_vault_secret.cosmos_primary_key.versionless_id
    identity            = "System"
  }

  secret {
    name  = "acr-password"
    value = var.acr_password
  }

  secret {
    name                = "jwt-secret-key"
    key_vault_secret_id = azurerm_key_vault_secret.jwt_secret.versionless_id
    identity            = "System"
  }

  secret {
    name                = "groq-api-key"
    key_vault_secret_id = azurerm_key_vault_secret.groq_api_key.versionless_id
    identity            = "System"
  }

  secret {
    name                = "gemini-api-key"
    key_vault_secret_id = azurerm_key_vault_secret.gemini_api_key.versionless_id
    identity            = "System"
  }

  template {
    container {
      name   = "fastapi-app"
      image  = "${azurerm_container_registry.mi_acr.login_server}/${var.container_image_name}:${var.container_image_tag}"
      cpu    = var.container_cpu
      memory = var.container_memory

      env {
        name  = "APP_ENV"
        value = var.environment
      }

      env {
        name  = "LOG_LEVEL"
        value = "info"
      }

      env {
        name  = "APP_NAME"
        value = "Market Research Intelligence Assistant"
      }

      env {
        name  = "APP_VERSION"
        value = "1.0.0"
      }

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }

      env {
        name  = "DEBUG"
        value = "false"
      }

      env {
        name  = "JWT_ALGORITHM"
        value = "HS256"
      }

      env {
        name  = "JWT_EXPIRY_MINUTES"
        value = "60"
      }

      env {
        name  = "API_PREFIX"
        value = "/api"
      }

      env {
        name        = "JWT_SECRET_KEY"
        secret_name = "jwt-secret-key"
      }

      env {
        name        = "GROQ_API_KEY"
        secret_name = "groq-api-key"
      }

      env {
        name        = "GEMINI_API_KEY"
        secret_name = "gemini-api-key"
      }

      env {
        name  = "GROQ_MODEL"
        value = "llama-3.3-70b-versatile"
      }

      env {
        name  = "GROQ_MAX_RETRIES"
        value = "3"
      }

      env {
        name  = "COSMOS_ENDPOINT"
        value = azurerm_cosmosdb_account.mi_cosmosdb.endpoint
      }

      env {
        name        = "COSMOS_KEY"
        secret_name = "cosmos-key"
      }

      env {
        name  = "COSMOS_DATABASE_NAME"
        value = azurerm_cosmosdb_sql_database.mi_database.name
      }

      env {
        name  = "COSMOS_USERS_CONTAINER"
        value = azurerm_cosmosdb_sql_container.users.name
      }

      env {
        name  = "COSMOS_REPORTS_CONTAINER"
        value = azurerm_cosmosdb_sql_container.reports.name
      }
    }

    max_replicas = 3
    min_replicas = 1
  }

  tags = local.common_tags

  registry {
    # Use ACR admin credentials for the initial deployment; managed identity migration can follow later.
    server               = azurerm_container_registry.mi_acr.login_server
    username             = var.acr_username
    password_secret_name = "acr-password"
  }
}

# Allow the Container App system identity to resolve Key Vault-backed secrets.
resource "azurerm_role_assignment" "key_vault_secrets_user" {
  scope                = azurerm_key_vault.mi_keyvault.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_container_app.mi_app.identity[0].principal_id
}

# Retained for future migration to managed identity authentication; not required for the initial deployment.
resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.mi_acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_container_app.mi_app.identity[0].principal_id
}
