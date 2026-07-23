# Container App Environment for hosting Azure Container Apps workloads.
resource "azurerm_container_app_environment" "mi_env" {
  name                = local.container_app_environment_name
  location            = azurerm_resource_group.mi.location
  resource_group_name = azurerm_resource_group.mi.name

  log_analytics_workspace_id = azurerm_log_analytics_workspace.mi_logs.id

  tags = local.common_tags
}
