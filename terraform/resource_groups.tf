# Create a resource group to contain all application infrastructure resources.
resource "azurerm_resource_group" "mi" {
  name     = local.resource_group_name
  location = var.location
  tags     = local.common_tags
}
