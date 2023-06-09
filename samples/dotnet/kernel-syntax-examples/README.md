# Semantic Kernel syntax examples

This project contains a collection of semi-random examples about various scenarios
using SK components. 

The examples are ordered by number, starting with very basic examples.

Most of the examples will require secrets and credentials, to access OpenAI, Azure OpenAI,
Bing and other resources. We suggest using .NET 
[Secret Manager](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets)
to avoid the risk of leaking secrets into the repository, branches and pull requests.
You can also use environment variables if you prefer.

To set your secrets with Secret Manager:

```
cd samples/dotnet/kernel-syntax-examples

dotnet user-secrets set "BING_API_KEY" "..."
dotnet user-secrets set "OPENAI_API_KEY" "..."
dotnet user-secrets set "AZURE_OPENAI_SERVICE_ID" "..."
dotnet user-secrets set "AZURE_OPENAI_DEPLOYMENT_NAME" "..."
dotnet user-secrets set "AZURE_OPENAI_CHAT_DEPLOYMENT_NAME" "..."
dotnet user-secrets set "AZURE_OPENAI_ENDPOINT" "https://... .openai.azure.com/"
dotnet user-secrets set "AZURE_OPENAI_KEY" "..."
dotnet user-secrets set "AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT_NAME" "..."
dotnet user-secrets set "AZURE_OPENAI_EMBEDDINGS_ENDPOINT" "https://... .openai.azure.com/"
dotnet user-secrets set "AZURE_OPENAI_EMBEDDINGS_KEY" "..."
dotnet user-secrets set "ACS_ENDPOINT" "https://... .search.windows.net"
dotnet user-secrets set "ACS_API_KEY" "..."
dotnet user-secrets set "QDRANT_ENDPOINT" "..."
dotnet user-secrets set "QDRANT_PORT" "..."
dotnet user-secrets set "WEAVIATE_SCHEME" "..."
dotnet user-secrets set "WEAVIATE_ENDPOINT" "..."
dotnet user-secrets set "WEAVIATE_PORT" "..."
dotnet user-secrets set "WEAVIATE_APIKEY" "..."
dotnet user-secrets set "GITHUB_PERSONAL_ACCESS_TOKEN" "github_pat_..."
dotnet user-secrets set "POSTGRES_CONNECTIONSTRING" "..."
```

To set your secrets with environment variables, use these names:

* BING_API_KEY
* OPENAI_API_KEY
* AZURE_OPENAI_SERVICE_ID
* AZURE_OPENAI_DEPLOYMENT_NAME
* AZURE_OPENAI_ENDPOINT
* AZURE_OPENAI_KEY
* ACS_ENDPOINT
* ACS_API_KEY
* QDRANT_ENDPOINT
* QDRANT_PORT
* WEAVIATE_SCHEME
* WEAVIATE_ENDPOINT
* WEAVIATE_PORT
* WEAVIATE_APIKEY
* GITHUB_PERSONAL_ACCESS_TOKEN
* POSTGRES_CONNECTIONSTRING
* AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT_NAME
* AZURE_OPENAI_EMBEDDINGS_ENDPOINT
* AZURE_OPENAI_EMBEDDINGS_KEY
