# Azure Container Registry for storing the application container image.
resource "azurerm_container_registry" "mi_acr" {
  name                = local.acr_name
  resource_group_name = azurerm_resource_group.mi.name
  location            = azurerm_resource_group.mi.location
  sku                 = "Basic"
  # Enable ACR Access Keys for the initial Container App registry authentication.
  admin_enabled = true
  tags          = local.common_tags
}
