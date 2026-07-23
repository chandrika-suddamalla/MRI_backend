# Terraform Configuration - Consolidated Infrastructure

This Terraform configuration provisions all Azure infrastructure for the MI Backend project in a **single consolidated folder**, combining both bootstrap state resources and application infrastructure.

## Folder Structure

```
terraform/
├── versions.tf                      # Terraform version and provider requirements
├── provider.tf                      # AzureRM provider configuration
├── backend.tf                       # Remote state backend configuration
├── variables.tf                     # Input variables (merged from bootstrap & infra)
├── locals.tf                        # Naming conventions and local values
├── outputs.tf                       # All outputs (bootstrap & application)
├── terraform.tfvars.example         # Example variable values
│
├── bootstrap_state.tf               # Bootstrap resources (resource group, storage)
├── resource_groups.tf               # Application resource group
├── log_analytics.tf                 # Log Analytics workspace
├── application_insights.tf          # Application Insights
├── container_app_environment.tf     # Container Apps environment
├── container_app.tf                 # Container App deployment
├── acr.tf                           # Azure Container Registry
├── sql.tf                           # Azure SQL Server & Database
└── keyvault.tf                      # Azure Key Vault
```

## Deployment Workflow

### Phase 1: Bootstrap (Create Remote State Backend)

1. **Authenticate to Azure:**
   ```powershell
   az login
   az account set --subscription <your-subscription-id>
   ```

2. **Copy and configure variables:**
   ```powershell
   cd terraform
   Copy-Item terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

3. **Initialize Terraform:**
   ```powershell
   terraform init
   ```

4. **Plan bootstrap resources only:**
   ```powershell
   terraform plan -target=azurerm_resource_group.bootstrap -target=azurerm_storage_account.bootstrap -target=azurerm_storage_container.tfstate
   ```

5. **Apply bootstrap resources:**
   ```powershell
   terraform apply -target=azurerm_resource_group.bootstrap -target=azurerm_storage_account.bootstrap -target=azurerm_storage_container.tfstate
   ```

6. **Capture bootstrap outputs:**
   ```powershell
   terraform output -raw bootstrap_resource_group_name
   terraform output -raw bootstrap_storage_account_name
   terraform output -raw bootstrap_container_name
   ```

### Phase 2: Configure Remote Backend

1. **Update `backend.tf`** with the bootstrap output values:
   ```hcl
   terraform {
     backend "azurerm" {
       resource_group_name  = "<bootstrap-resource-group-name>"
       storage_account_name = "<bootstrap-storage-account-name>"
       container_name       = "<bootstrap-container-name>"
       key                  = "terraform.tfstate"
     }
   }
   ```

2. **Reconfigure Terraform to use the remote backend:**
   ```powershell
   terraform init -reconfigure
   ```

### Phase 3: Deploy Application Infrastructure

1. **Validate configuration:**
   ```powershell
   terraform validate
   ```

2. **Plan application resources:**
   ```powershell
   terraform plan -var-file="terraform.tfvars"
   ```

3. **Apply application infrastructure:**
   ```powershell
   terraform apply -var-file="terraform.tfvars"
   ```

4. **Retrieve outputs:**
   ```powershell
   terraform output
   ```

## Using Environment Variables

Instead of `terraform.tfvars`, you can use environment variables:

```powershell
$env:TF_VAR_project = "mi-backend"
$env:TF_VAR_environment = "dev"
$env:TF_VAR_location = "eastus"
$env:TF_VAR_owner = "team@example.com"
$env:TF_VAR_sql_administrator_password = "SecurePassword123!"
```

Then run without `-var-file`:
```powershell
terraform plan
terraform apply
```

## Key Resources Provisioned

### Bootstrap Phase
- **Resource Group**: `mi-backend-dev-bootstrap-rg`
- **Storage Account**: `mibackenddevstg`
- **Blob Container**: `tfstate`

### Application Phase
- **Resource Group**: `mi-backend-dev-rg`
- **Log Analytics**: `mi-backend-dev-la`
- **Application Insights**: `mi-backend-dev-ai`
- **Container Registry**: `mibackenddevacr`
- **Container App Environment**: `mi-backend-dev-env`
- **Container App**: `mi-backend-dev-app`
- **SQL Server**: `mi-backend-dev-sql`
- **SQL Database**: `mi-backend-dev-db`
- **Key Vault**: `mi-backend-dev-kv`

## Common Commands

```powershell
# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Format HCL files
terraform fmt -recursive

# Check what will change
terraform plan -var-file="terraform.tfvars"

# Apply changes
terraform apply -var-file="terraform.tfvars"

# Show current state
terraform show

# Destroy all resources
terraform destroy -var-file="terraform.tfvars"

# Destroy only application resources (keep bootstrap)
terraform destroy -target='azurerm_resource_group.main' -var-file="terraform.tfvars"

# Get specific output
terraform output container_app_url
```

## Troubleshooting

### Terraform command not found

The VS Code terminal might not have Terraform in its PATH. Try:

```powershell
# In PowerShell, check where Terraform is installed
where.exe terraform

# If not found, use absolute path or add to PATH
C:\HashiCorp\terraform\terraform.exe --version
```

### Backend state lock errors

If you get state lock errors, check who has Terraform running:

```powershell
terraform force-unlock <LOCK-ID>
```

### Backend configuration errors

If you get "Error: Backend initialization required" after updating `backend.tf`:

```powershell
terraform init -reconfigure
```

### SQL password issues

Sensitive variables like `sql_administrator_password` should never be in version control. Use:

```powershell
terraform apply -var='sql_administrator_password=YourSecurePassword123!'
```

Or set via environment variable:
```powershell
$env:TF_VAR_sql_administrator_password = "YourSecurePassword123!"
terraform apply -var-file="terraform.tfvars"
```

## Next Steps

1. Deploy the container image to ACR
2. Update the Container App image if needed
3. Configure DNS and SSL certificates
4. Set up Key Vault secrets for application configuration
5. Configure SQL database with application schema

## References

- [Terraform Azure Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [Azure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/)
- [Azure SQL Database](https://learn.microsoft.com/en-us/azure/azure-sql/database/)
- [Azure Key Vault](https://learn.microsoft.com/en-us/azure/key-vault/)
