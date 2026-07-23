# Azure Key Vault for secure secret storage and future secret management.
resource "azurerm_key_vault" "mi_keyvault" {
  name                        = local.key_vault_name
  resource_group_name         = azurerm_resource_group.mi.name
  location                    = azurerm_resource_group.mi.location
  sku_name                    = "standard"
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days  = 7
  purge_protection_enabled    = false
  network_acls {
    default_action             = "Allow"
    bypass                     = "AzureServices"
  }
  tags = local.common_tags
}
