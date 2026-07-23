# Container App deployment using a placeholder image from ACR.
resource "azurerm_container_app" "mi_app" {
  name                         = local.container_app_name
  container_app_environment_id = azurerm_container_app_environment.mi_env.id
  resource_group_name          = azurerm_resource_group.mi.name
  revision_mode                = "Single"

  ingress {
    external_enabled   = true
    target_port        = 8000
    transport          = "auto"
    
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  identity {
    type = "SystemAssigned"
  }

  secret {
    name  = "cosmos-key"
    value = azurerm_cosmosdb_account.mi_cosmosdb.primary_key
  }

  template {
    container {
      name   = "fastapi-app"
      image  = "${azurerm_container_registry.mi_acr.login_server}/${var.container_image_name}:${var.container_image_tag}"
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "APP_ENV"
        value = var.environment
      }

      env {
        name  = "LOG_LEVEL"
        value = "info"
      }

      env {
        name  = "COSMOS_ENDPOINT"
        value = azurerm_cosmosdb_account.mi_cosmosdb.endpoint
      }

      env {
        name  = "COSMOS_KEY"
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
    server = azurerm_container_registry.mi_acr.login_server
  }
}

# Grant the Container App's managed identity permission to pull from ACR.
resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.mi_acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_container_app.mi_app.identity[0].principal_id
}
