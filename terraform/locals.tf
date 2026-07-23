# Local naming conventions and tags used across the infrastructure.
locals {
  # Common prefix for all resources
  prefix = lower(replace("${var.project}-${var.environment}", "_", "-"))

  # Application infrastructure naming
  resource_group_name            = "${local.prefix}-rg"
  acr_name                       = lower(replace("${var.project}${var.environment}acr", "-", ""))
  log_analytics_name             = "${local.prefix}-la"
  application_insights_name      = "${local.prefix}-ai"
  container_app_environment_name = "${local.prefix}-env"
  container_app_name             = "${local.prefix}-app"
  cosmosdb_account_name          = lower(replace("${var.project}-${var.environment}-cosmosdb", "-", ""))
  cosmosdb_database_name         = "mi-db"
  key_vault_name                 = "${local.prefix}-kv"

  # Common tags applied to all resources
  common_tags = merge({
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    ManagedBy   = "Terraform"
  }, var.resource_group_tags)
}
