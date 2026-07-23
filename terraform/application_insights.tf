# Workspace-based Application Insights for application telemetry.
resource "azurerm_application_insights" "mi_insights" {
  name                = local.application_insights_name
  location            = azurerm_resource_group.mi.location
  resource_group_name = azurerm_resource_group.mi.name
  application_type    = "web"
  workspace_id        = azurerm_log_analytics_workspace.mi_logs.id
  tags                = local.common_tags
}
