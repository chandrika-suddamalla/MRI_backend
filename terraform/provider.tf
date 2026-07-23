# Configure the AzureRM provider for this Terraform project.
provider "azurerm" {
  features {}
}

# Retrieve information about the current authenticated Azure identity.
data "azurerm_client_config" "current" {}
