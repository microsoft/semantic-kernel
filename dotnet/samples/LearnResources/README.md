# Learn Resources

This folder contains a project with code snippets that are related to online documentation sources like Microsoft Learn, DevBlogs and others.

| Subfolders        | Description                                                                                                   |
| ----------------- | ------------------------------------------------------------------------------------------------------------- |
| `MicrosoftLearn`  | Code snippets that are related to [Microsoft Learn Docs](https://learn.microsoft.com/en-us/semantic-kernel/). |

## Running Examples with Filters

You can run specific examples by using test filters (dotnet test --filter).
Type "dotnet test --help" at the command line for more details.

## Configuring Secrets

Most of the examples will require secrets and credentials to access OpenAI, Azure OpenAI,
and other resources. We suggest using .NET
[Secret Manager](https://learn.microsoft.com/aspnet/core/security/app-secrets)
to avoid the risk of leaking secrets into the repository, branches and pull requests.
You can also use environment variables if you prefer.

This project and KernelSyntaxExamples use the same pool of secrets. 

To set your secrets with Secret Manager:

```
cd dotnet/samples/DocumentationExamples

dotnet user-secrets init

dotnet user-secrets set "OpenAI:ModelId" "..."
dotnet user-secrets set "OpenAI:ChatModelId" "..."
dotnet user-secrets set "OpenAI:EmbeddingModelId" "..."
dotnet user-secrets set "OpenAI:ApiKey" "..."

dotnet user-secrets set "AzureOpenAI:ServiceId" "..."
dotnet user-secrets set "AzureOpenAI:DeploymentName" "..."
dotnet user-secrets set "AzureOpenAI:ModelId" "..."
dotnet user-secrets set "AzureOpenAI:ChatDeploymentName" "..."
dotnet user-secrets set "AzureOpenAI:ChatModelId" "..."
dotnet user-secrets set "AzureOpenAI:Endpoint" "https://... .openai.azure.com/"
dotnet user-secrets set "AzureOpenAI:ApiKey" "..."
```

To set your secrets with environment variables, use these names:

```
# OpenAI
OpenAI__ModelId
OpenAI__ChatModelId
OpenAI__EmbeddingModelId
OpenAI__ApiKey

# Azure OpenAI
AzureOpenAI__ServiceId
AzureOpenAI__DeploymentName
AzureOpenAI__ChatDeploymentName
AzureOpenAI__Endpoint
AzureOpenAI__ApiKey
```
