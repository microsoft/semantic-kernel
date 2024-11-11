# OpenAI Realtime API

TODO

## Configuring Secrets

The example requires credentials to access OpenAI or Azure OpenAI.

If you have set up those credentials as secrets within Secret Manager or through environment variables for other samples from the solution in which this project is found, they will be re-used.

### To set your secrets with Secret Manager:

```
cd dotnet/samples/Demos/OpenAIRuntime

dotnet user-secrets init

dotnet user-secrets set "OpenAI:ModelId" "..."
dotnet user-secrets set "OpenAI:ApiKey" "..."

dotnet user-secrets set "AzureOpenAI:DeploymentName" "..."
dotnet user-secrets set "AzureOpenAI:Endpoint" "https://... .openai.azure.com/"
dotnet user-secrets set "AzureOpenAI:ApiKey" "..."
```

### To set your secrets with environment variables

Use these names:

```
# OpenAI
OpenAI__ModelId
OpenAI__ApiKey

# Azure OpenAI
AzureOpenAI__DeploymentName
AzureOpenAI__Endpoint
AzureOpenAI__ApiKey
```
