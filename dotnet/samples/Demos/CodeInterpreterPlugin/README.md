# Semantic Kernel - Code Interpreter Plugin with Azure Container Apps

This example demonstrates how to do AI Code Interpretetion using a Plugin with Azure Container Apps to execute python code in a container.

## Configuring Secrets

The example require credentials to access OpenAI and Azure Container Apps (ACA)

If you have set up those credentials as secrets within Secret Manager or through environment variables for other samples from the solution in which this project is found, they will be re-used.

### To set your secrets with Secret Manager:

```
dotnet user-secrets init

dotnet user-secrets set "OpenAI:ApiKey" "..."

dotnet user-secrets set "AzureContainerApps:BearerKey" " .. current token .. "
dotnet user-secrets set "AzureContainerApps:Endpoint" " .. endpoint .. "
```

### To set your secrets with environment variables

Use these names:

```
# OpenAI
OpenAI__ApiKey

# Azure Container Apps
AzureContainerApps__BearerKey
AzureContainerApps__Endpoint
```
