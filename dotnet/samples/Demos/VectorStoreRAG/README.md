# Vector Store RAG Demo

This sample demonstrates how to ingest text from pdf files into a vector store and ask questions about the content
using an LLM while using RAG to supplement the LLM with additional information from the vector store.

## Configuring the Sample

The sample can be configured in various ways:

1. You can choose your preferred vector store by setting the `Rag:VectorStoreType` configuration setting in the `appsettings.json` file to one of the following values:
   1. AzureAISearch
   1. AzureCosmosDBMongoDB
   1. AzureCosmosDBNoSQL
   1. InMemory
   1. Qdrant
   1. Redis
   1. Weaviate
1. You can choose your preferred AI Chat service by settings the `Rag:AIChatService` configuration setting in the `appsettings.json` file to one of the following values:
   1. AzureOpenAI
   1. OpenAI
1. You can choose your preferred AI Embedding service by settings the `Rag:AIEmbeddingService` configuration setting in the `appsettings.json` file to one of the following values:
   1. AzureOpenAIEmbeddings
   1. OpenAIEmbeddings
1. You can choose whether to load data into the vector store by setting the `Rag:BuildCollection` configuration setting in the `appsettings.json` file to `true`. If you set this to `false`, the sample will assume that data was already loaded previously and it will go straight into the chat experience.
1. You can choose the name of the collection to use by setting the `Rag:CollectionName` configuration setting in the `appsettings.json` file.
1. You can choose the pdf file to load into the vector store by setting the `Rag:PdfFilePaths` array in the `appsettings.json` file.
1. You can choose the number of records to process per batch when loading data into the vector store by setting the `Rag:DataLoadingBatchSize` configuration setting in the `appsettings.json` file.
1. You can choose the number of milliseconds to wait between batches when loading data into the vector store by setting the `Rag:DataLoadingBetweenBatchDelayInMilliseconds` configuration setting in the `appsettings.json` file.

## Dependency Setup

To run this sample, you need to setup your source data, setup your vector store and AI services, and setup secrets for these.

### Source PDF File

You will need to supply some source pdf files to load into the vector store.
Once you have a file ready, update the `PdfFilePaths` array in the `appsettings.json` file with the path to the file.

```json
{
    "Rag": {
        "PdfFilePaths": [ "sourcedocument.pdf" ],
    }
}
```

Why not try the semantic kernel documentation as your input.
You can download it as a PDF from the https://learn.microsoft.com/en-us/semantic-kernel/overview/ page.
See the Download PDF button at the bottom of the page.

### Azure OpenAI Chat Completion

For Azure OpenAI Chat Completion, you need to add the following secrets:

```cli
dotnet user-secrets set "AIServices:AzureOpenAI:Endpoint" "https://<yourservice>.openai.azure.com"
dotnet user-secrets set "AIServices:AzureOpenAI:ChatDeploymentName" "<your deployment name>"
```

Note that the code doesn't use an API Key to communicate with Azure OpenAI, but rather an `AzureCliCredential` so no api key secret is required.

### OpenAI Chat Completion

For OpenAI Chat Completion, you need to add the following secrets:

```cli
dotnet user-secrets set "AIServices:OpenAI:ModelId" "<your model id>"
dotnet user-secrets set "AIServices:OpenAI:ApiKey" "<your api key>"
```

Optionally, you can also provide an Org Id

```cli
dotnet user-secrets set "AIServices:OpenAI:OrgId" "<your org id>"
```

### Azure OpenAI Embeddings

For Azure OpenAI Embeddings, you need to add the following secrets:

```cli
dotnet user-secrets set "AIServices:AzureOpenAIEmbeddings:Endpoint" "https://<yourservice>.openai.azure.com"
dotnet user-secrets set "AIServices:AzureOpenAIEmbeddings:DeploymentName" "<your deployment name>"
```

Note that the code doesn't use an API Key to communicate with Azure OpenAI, but rather an `AzureCliCredential` so no api key secret is required.

### OpenAI Embeddings

For OpenAI Embeddings, you need to add the following secrets:

```cli
dotnet user-secrets set "AIServices:OpenAIEmbeddings:ModelId" "<your model id>"
dotnet user-secrets set "AIServices:OpenAIEmbeddings:ApiKey" "<your api key>"
```

Optionally, you can also provide an Org Id

```cli
dotnet user-secrets set "AIServices:OpenAIEmbeddings:OrgId" "<your org id>"
```

### Azure AI Search

If you want to use Azure AI Search as your vector store, you will need to create an instance of Azure AI Search and add
the following secrets here:

```cli
dotnet user-secrets set "VectorStores:AzureAISearch:Endpoint" "https://<yourservice>.search.windows.net"
dotnet user-secrets set "VectorStores:AzureAISearch:ApiKey" "<yoursecret>"
```

### Azure CosmosDB MongoDB

If you want to use Azure CosmosDB MongoDB as your vector store, you will need to create an instance of Azure CosmosDB MongoDB and add
the following secrets here:

```cli
dotnet user-secrets set "VectorStores:AzureCosmosDBMongoDB:ConnectionString" "<yourconnectionstring>"
dotnet user-secrets set "VectorStores:AzureCosmosDBMongoDB:DatabaseName" "<yourdbname>"
```

### Azure CosmosDB NoSQL

If you want to use Azure CosmosDB NoSQL as your vector store, you will need to create an instance of Azure CosmosDB NoSQL and add
the following secrets here:

```cli
dotnet user-secrets set "VectorStores:AzureCosmosDBNoSQL:ConnectionString" "<yourconnectionstring>"
dotnet user-secrets set "VectorStores:AzureCosmosDBNoSQL:DatabaseName" "<yourdbname>"
```

### Qdrant

If you want to use Qdrant as your vector store, you will need to have an instance of Qdrant available.

You can use the following command to start a Qdrant instance in docker, and this will work with the default configured settings:

```cli
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant:latest
```

If you want to use a different instance of Qdrant, you can update the appsettings.json file or add the following secrets to reconfigure:

```cli
dotnet user-secrets set "VectorStores:Qdrant:Host" "<yourservice>"
dotnet user-secrets set "VectorStores:Qdrant:Port" "6334"
dotnet user-secrets set "VectorStores:Qdrant:Https" "true"
dotnet user-secrets set "VectorStores:Qdrant:ApiKey" "<yoursecret>"
```

### Redis

If you want to use Redis as your vector store, you will need to have an instance of Redis available.

You can use the following command to start a Redis instance in docker, and this will work with the default configured settings:

```cli
docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest
```

If you want to use a different instance of Redis, you can update the appsettings.json file or add the following secret to reconfigure:

```cli
dotnet user-secrets set "VectorStores:Redis:ConnectionConfiguration" "<yourredisconnectionconfiguration>"
```

### Weaviate

If you want to use Weaviate as your vector store, you will need to have an instance of Weaviate available.

You can use the following command to start a Weaviate instance in docker, and this will work with the default configured settings:

```cli
docker run -d --name weaviate -p 8080:8080 -p 50051:50051 cr.weaviate.io/semitechnologies/weaviate:1.26.4
```

If you want to use a different instance of Weaviate, you can update the appsettings.json file or add the following secret to reconfigure:

```cli
dotnet user-secrets set "VectorStores:Weaviate:Endpoint" "<yourweaviateurl>"
```
