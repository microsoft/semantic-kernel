## About

Contains abstractions for accessing Vector Databases and Vector Indexes.

## Key Features

- Base abstract classes and interfaces for Vector Database implementation. Vector Database implementations are provided separately in other packages, for example  `Microsoft.SemanticKernel.Connectors.AzureAISearch`.
- Abstractions include:
  - Creating, listing and deleting collections with custom schema support.
  - Creating, retrieving, updating and deleting records.
  - Similarty search using vector embeddings.
  - Search using filters.
  - Hybrid search combining vector similarity and keyword search.
  - Built-in embedding generation using `Microsoft.Extensions.AI`.

## How to Use

This package is typically used with an implementation of the vector database abstractions such as `Microsoft.SemanticKernel.Connectors.AzureAISearch`.

## Main Types

The main types provided by this library are:

- [Microsoft.Extensions.VectorData.VectorStore](https://learn.microsoft.com/dotnet/api/microsoft.extensions.vectordata.vectorstore)
- [Microsoft.Extensions.VectorData.VectorStoreCollection](https://learn.microsoft.com/dotnet/api/microsoft.extensions.vectordata.vectorstorecollection-2)

## Additional Documentation

- [Conceptual documentation](https://learn.microsoft.com/en-us/semantic-kernel/concepts/vector-store-connectors)

## Related Packages

Vector Database implementations:

- [Microsoft.SemanticKernel.Connectors.AzureAISearch](https://www.nuget.org/packages/Microsoft.SemanticKernel.Connectors.AzureAISearch)
- [Microsoft.SemanticKernel.Connectors.CosmosMongoDB](https://www.nuget.org/packages/Microsoft.SemanticKernel.Connectors.CosmosMongoDB)
- [Microsoft.SemanticKernel.Connectors.CosmosNoSQL](https://www.nuget.org/packages/Microsoft.SemanticKernel.Connectors.CosmosNoSQL)
- [Elastic.SemanticKernel.Connectors.Elasticsearch](https://www.nuget.org/packages/Elastic.SemanticKernel.Connectors.Elasticsearch)
- [Microsoft.SemanticKernel.Connectors.InMemory](https://www.nuget.org/packages/Microsoft.SemanticKernel.Connectors.InMemory)
- [Microsoft.SemanticKernel.Connectors.MongoDB](https://www.nuget.org/packages/Microsoft.SemanticKernel.Connectors.MongoDB)
- [Microsoft.SemanticKernel.Connectors.PgVector](https://www.nuget.org/packages/Microsoft.SemanticKernel.Connectors.PgVector)
- [Microsoft.SemanticKernel.Connectors.Pinecone](https://www.nuget.org/packages/Microsoft.SemanticKernel.Connectors.Pinecone)
- [Microsoft.SemanticKernel.Connectors.Qdrant](https://www.nuget.org/packages/Microsoft.SemanticKernel.Connectors.Qdrant)
- [Microsoft.SemanticKernel.Connectors.Redis](https://www.nuget.org/packages/Microsoft.SemanticKernel.Connectors.Redis)
- [Microsoft.SemanticKernel.Connectors.SqliteVec](https://www.nuget.org/packages/Microsoft.SemanticKernel.Connectors.SqliteVec)
- [Microsoft.SemanticKernel.Connectors.SqlServer](https://www.nuget.org/packages/Microsoft.SemanticKernel.Connectors.SqlServer)
- [Microsoft.SemanticKernel.Connectors.Weaviate](https://www.nuget.org/packages/Microsoft.SemanticKernel.Connectors.Weaviate)

## Feedback & Contributing

Microsoft.Extensions.VectorData.Abstractions is released as open source under the [MIT license](https://licenses.nuget.org/MIT). Bug reports and contributions are welcome at [the GitHub repository](https://github.com/microsoft/semantic-kernel).
