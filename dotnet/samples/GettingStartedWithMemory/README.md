# Getting Started With Semantic Kernel Memory Connector

This project contains a step by step guide to get started with the Semantic Kernel Memory Connectors.

The examples can be run as integration tests but their code can also be copied to stand-alone programs.

1. Performing **C**reate, **R**ead, **U**pdate and **D**elete optations using the `VolatileVectorStore`
2. Configure the Vector Store you are using, we currently support:
   1. Azure AI Search
   2. Redis
   3. Qdrant
   4. Pinecone
3. Options to configure your data model and custom mapping
4. ...

## Configuring a Vector Database
Here is a table showing the different databases plus useful information on how to get started with them. 

- Docker Command: The docker command to run a local container with the database where available 
- Portal: The portal where it�s possible to observe any collections and records created 
- Fixture Name: Where available a fixture that can be used to automatically start and stop the docker container (alternative to running it manually) 
- Add to Kernel: An example of the command to use to add the VectorStore to DI on the kernelbuilder. 


| Database | Docker Command | Portal | Fixture Name | Add to Kernel |
|----------|----------------|--------|--------------|---------------|
| Redis | `docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest` | http://localhost:8001/redis-stack/browser | IClassFixture<VectorStoreRedisContainerFixture> | kernelBuilder.AddRedisVectorStore("localhost:6379"); |
| Qdrant | `docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant:latest` | http://localhost:6333/dashboard | IClassFixture<VectorStoreQdrantContainerFixture> | kernelBuilder.AddQdrantVectorStore("localhost"); |
| Volatile | n/a | n/a | IClassFixture<VectorStoreVolatileFixture> | kernelBuilder.AddVolatileVectorStore(); |
| Azure AI Search | n/a | n/a | IClassFixture<VectorStoreAzureAISearchFixture> | kernelBuilder.AddAzureAISearchVectorStore(new Uri("https://vectorstore-bugbash-2024-07-25.search.windows.net"), new AzureKeyCredential("")); |
| Pinecone | n/a | Requires signup: https://www.pinecone.io/ (API key can be requested after signup) | n/a | kernelBuilder.AddPineconeVectorStore("api key"); |


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

dotnet user-secrets set "OpenAI:ModelId" "..."
dotnet user-secrets set "OpenAI:ChatModelId" "..."
dotnet user-secrets set "OpenAI:EmbeddingModelId" "..."
dotnet user-secrets set "OpenAI:ApiKey" "..."

```

To set your secrets with environment variables, use these names:

```
# OpenAI
OpenAI__ModelId
OpenAI__ChatModelId
OpenAI__EmbeddingModelId
OpenAI__ApiKey
```
