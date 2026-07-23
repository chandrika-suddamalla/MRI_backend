project             = "mi-backend"
environment         = "dev"
location            = "westus2"
owner               = "team@example.com"
resource_group_tags = {}

# Container image configuration
container_image_name = "fastapi-app"
container_image_tag  = "latest"

# Container sizing and scaling configuration.
container_cpu    = 0.5
container_memory = "1Gi"
min_replicas     = 1
max_replicas     = 3

acr_password = "FV3yucr0A60ogdzKBleYgdQ2G2oxULRlSheev7RSCVkufU6LuwHjJQQJ99CGAC8vTInEqg7NAAACAZCRw1kJ"

jwt_secret_key = "super-secret-jwt-key-for-development-only"
