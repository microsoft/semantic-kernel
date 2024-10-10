# Starting With Semantic Kernel

This project contains a step by step guide to get started using Text Search with the Semantic Kernel.

The examples can be run as integration tests but their code can also be copied to stand-alone programs.

## Configuring Secrets

Most of the examples will require secrets and credentials, to access OpenAI, Azure OpenAI,
Bing and other resources. We suggest using .NET
[Secret Manager](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets)
to avoid the risk of leaking secrets into the repository, branches and pull requests.
You can also use environment variables if you prefer.

To set your secrets with Secret Manager:

```
cd dotnet/samples/Concepts

dotnet user-secrets init

dotnet user-secrets set "AzureOpenAIEmbeddings:DeploymentName" "..."
dotnet user-secrets set "AzureOpenAIEmbeddings:Endpoint" "..."
dotnet user-secrets set "AzureOpenAI:ChatDeploymentName" "..."
dotnet user-secrets set "AzureOpenAI:Endpoint" "..."

```

To set your secrets with environment variables, use these names:

```
AzureOpenAIEmbeddings__DeploymentName
AzureOpenAIEmbeddings__Endpoint
AzureOpenAI__ChatDeploymentName
AzureOpenAI__Endpoint
```
