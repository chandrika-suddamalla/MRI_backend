# Azure Cosmos DB Account for the application database.
# Using SQL (Core) API with session-level consistency.
resource "azurerm_cosmosdb_account" "mi_cosmosdb" {
  name                = local.cosmosdb_account_name
  location            = azurerm_resource_group.mi.location
  resource_group_name = azurerm_resource_group.mi.name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"

  consistency_policy {
    consistency_level       = "Session"
    max_interval_in_seconds = 5
    max_staleness_prefix    = 100
  }

  geo_location {
    location          = azurerm_resource_group.mi.location
    failover_priority = 0
  }

  capabilities {
    name = "EnableServerless"
  }

  public_network_access_enabled = true

  # Allow force deletion without delays
  access_key_metadata_writes_enabled = false

  tags = local.common_tags
}

# Cosmos SQL Database for the application data.
resource "azurerm_cosmosdb_sql_database" "mi_database" {
  name                = local.cosmosdb_database_name
  resource_group_name = azurerm_resource_group.mi.name
  account_name        = azurerm_cosmosdb_account.mi_cosmosdb.name
}

# Users Container - stores user profile information.
# Partition key: /email for efficient user lookups by email.
resource "azurerm_cosmosdb_sql_container" "users" {
  name                = "users"
  database_name       = azurerm_cosmosdb_sql_database.mi_database.name
  resource_group_name = azurerm_resource_group.mi.name
  account_name        = azurerm_cosmosdb_account.mi_cosmosdb.name

  partition_key_paths = ["/email"]

  indexing_policy {
    indexing_mode = "consistent"

    included_path {
      path = "/*"
    }

    excluded_path {
      path = "/\"_etag\"/?"
    }
  }
}

# Reports Container - stores generated research reports.
# Partition key: /userId for efficient filtering by user.
resource "azurerm_cosmosdb_sql_container" "reports" {
  name                = "reports"
  database_name       = azurerm_cosmosdb_sql_database.mi_database.name
  resource_group_name = azurerm_resource_group.mi.name
  account_name        = azurerm_cosmosdb_account.mi_cosmosdb.name

  partition_key_paths = ["/userId"]

  indexing_policy {
    indexing_mode = "consistent"

    included_path {
      path = "/*"
    }

    excluded_path {
      path = "/\"_etag\"/?"
    }
  }
}
