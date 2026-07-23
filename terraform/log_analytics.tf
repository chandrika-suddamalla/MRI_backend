# Log Analytics workspace to collect container app and infrastructure logs.
resource "azurerm_log_analytics_workspace" "mi_logs" {
  name                = local.log_analytics_name
  location            = azurerm_resource_group.mi.location
  resource_group_name = azurerm_resource_group.mi.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = local.common_tags
}
