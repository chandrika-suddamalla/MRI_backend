# Outputs to expose important resource names, endpoints, and connection values.

# Application infrastructure outputs
output "resource_group_name" {
  description = "Name of the Azure resource group created for the application infrastructure."
  value       = azurerm_resource_group.mi.name
}

/* Temporarily commented out - container_app resource is not deployed yet
output "container_app_name" {
  description = "Name of the deployed Azure Container App."
  value       = azurerm_container_app.mi_app.name
}

output "container_app_url" {
  description = "Public URL for the Azure Container App."
  value       = azurerm_container_app.mi_app.ingress[0].fqdn
}
*/

output "container_app_environment_name" {
  description = "Name of the Azure Container Apps environment."
  value       = azurerm_container_app_environment.mi_env.name
}

output "acr_login_server" {
  description = "Login server for the Azure Container Registry."
  value       = azurerm_container_registry.mi_acr.login_server
}

output "cosmosdb_account_name" {
  description = "Name of the Azure Cosmos DB account."
  value       = azurerm_cosmosdb_account.mi_cosmosdb.name
}

output "cosmosdb_endpoint" {
  description = "The endpoint URI of the Cosmos DB account."
  value       = azurerm_cosmosdb_account.mi_cosmosdb.endpoint
  sensitive   = true
}

output "cosmosdb_database_name" {
  description = "Name of the Cosmos DB SQL database."
  value       = azurerm_cosmosdb_sql_database.mi_database.name
}

output "cosmosdb_users_container_name" {
  description = "Name of the users container in Cosmos DB."
  value       = azurerm_cosmosdb_sql_container.users.name
}

output "cosmosdb_reports_container_name" {
  description = "Name of the reports container in Cosmos DB."
  value       = azurerm_cosmosdb_sql_container.reports.name
}

output "key_vault_name" {
  description = "Name of the Azure Key Vault."
  value       = azurerm_key_vault.mi_keyvault.name
}

output "application_insights_connection_string" {
  description = "Connection string for the Application Insights resource."
  value       = azurerm_application_insights.mi_insights.connection_string
  sensitive   = true
}

output "log_analytics_workspace_id" {
  description = "ID of the Log Analytics workspace."
  value       = azurerm_log_analytics_workspace.mi_logs.id
}
