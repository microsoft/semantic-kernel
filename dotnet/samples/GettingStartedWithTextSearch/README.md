# Starting With Semantic Kernel

This project contains a step by step guide to get started using Text Search with the Semantic Kernel.

The examples can be run as integration tests but their code can also be copied to stand-alone programs.

## Configuring Secrets

Most of the examples will require secrets and credentials, to access OpenAI, Azure OpenAI,
Bing and other resources. We suggest using .NET
[Secret Manager](https://learn.microsoft.com/aspnet/core/security/app-secrets)
to avoid the risk of leaking secrets into the repository, branches and pull requests.
You can also use environment variables if you prefer.

**NOTE**
The `Step2_Search_For_RAG.RagWithBingTextSearchUsingFullPagesAsync` sample requires a large context window so we recommend using `gpt-4o` or `gpt-4o-mini` models.

To set your secrets with Secret Manager:

```
cd dotnet/samples/Concepts

dotnet user-secrets init

dotnet user-secrets set "OpenAI:EmbeddingModelId" "..."
dotnet user-secrets set "OpenAI:ChatModelId" "..."
dotnet user-secrets set "OpenAI:ApiKey" "..."

dotnet user-secrets set "Bing:ApiKey" "..."

dotnet user-secrets set "Google:SearchEngineId" "..."
dotnet user-secrets set "Google:ApiKey" "..."
```

To set your secrets with environment variables, use these names:

```
OpenAI__EmbeddingModelId
OpenAI__ChatModelId
OpenAI__ApiKey

Bing__ApiKey

Google__SearchEngineId
Google__ApiKey
```
