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
