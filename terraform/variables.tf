# Naming and location variables for infrastructure resources.
variable "project" {
  description = "Logical project identifier used in resource naming."
  type        = string
  default     = "mi-backend"
}

variable "environment" {
  description = "Deployment environment identifier used in resource naming and tagging."
  type        = string
  default     = "dev"
}

variable "location" {
  description = "Azure region where resources are created."
  type        = string
  default     = "westus2"
}

variable "owner" {
  description = "Owner or contact for the provisioned Azure resources."
  type        = string
  default     = "team@example.com"
}

variable "resource_group_tags" {
  description = "Additional tags for resources."
  type        = map(string)
  default     = {}
}

variable "container_image_name" {
  description = "Name of the container image stored in ACR."
  type        = string
  default     = "fastapi-app"
}

variable "container_image_tag" {
  description = "Tag of the container image to deploy."
  type        = string
  default     = "latest"
}

# Secret input values are supplied through TF_VAR_* or a secure CI/CD secret store,
# never through terraform.tfvars.
variable "acr_password" {
  description = "ACR admin password for the initial Container App deployment."
  type        = string
  sensitive   = true
}

variable "acr_username" {
  description = "ACR admin username for the initial Container App deployment."
  type        = string
}

variable "jwt_secret_key" {
  description = "JWT signing secret for the deployed application."
  type        = string
  sensitive   = true
}

variable "groq_api_key" {
  description = "Groq API key for the deployed research analysis service."
  type        = string
  sensitive   = true
}

variable "gemini_api_key" {
  description = "Gemini API key reserved for future model integrations."
  type        = string
  sensitive   = true
}

# Container sizing and scaling are infrastructure configuration, not application secrets.
variable "container_cpu" {
  description = "Container CPU allocation in Azure Container Apps."
  type        = number
  default     = 0.5
}

variable "container_memory" {
  description = "Container memory allocation in Azure Container Apps."
  type        = string
  default     = "1Gi"
}

variable "min_replicas" {
  description = "Minimum number of Container App replicas."
  type        = number
  default     = 1
}

variable "max_replicas" {
  description = "Maximum number of Container App replicas."
  type        = number
  default     = 3
}
