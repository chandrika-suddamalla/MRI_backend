# Azure Key Vault for secure secret storage and future secret management.
resource "azurerm_key_vault" "mi_keyvault" {
  name                       = local.key_vault_name
  resource_group_name        = azurerm_resource_group.mi.name
  location                   = azurerm_resource_group.mi.location
  sku_name                   = "standard"
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days = 7
  purge_protection_enabled   = false
  network_acls {
    default_action = "Allow"
    bypass         = "AzureServices"
  }
  tags = local.common_tags
}

# Sensitive values are managed in Key Vault and referenced by the Container App.
# Values are supplied through TF_VAR_* or a secure CI/CD secret store, not tfvars.
resource "azurerm_key_vault_secret" "cosmos_primary_key" {
  name         = "cosmos-primary-key"
  value        = azurerm_cosmosdb_account.mi_cosmosdb.primary_key
  key_vault_id = azurerm_key_vault.mi_keyvault.id
}

resource "azurerm_key_vault_secret" "jwt_secret" {
  name         = "jwt-secret"
  value        = var.jwt_secret_key
  key_vault_id = azurerm_key_vault.mi_keyvault.id
}

resource "azurerm_key_vault_secret" "gemini_api_key" {
  name         = "gemini-api-key"
  value        = var.gemini_api_key
  key_vault_id = azurerm_key_vault.mi_keyvault.id
}

resource "azurerm_key_vault_secret" "groq_api_key" {
  name         = "groq-api-key"
  value        = var.groq_api_key
  key_vault_id = azurerm_key_vault.mi_keyvault.id
}

