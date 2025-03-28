## About

Contains abstractions for accessing Vector Databases and Vector Indexes.

## Key Features

- Interfaces for Vector Database implementation. Vector Database implementations are provided separately in other packages, for example  `Microsoft.SemanticKernel.Connectors.AzureAISearch`.

## How to Use

This package is typically used with an implementation of the vector database abstractions such as `Microsoft.SemanticKernel.Connectors.AzureAISearch`.

## Main Types

The main types provided by this library are:

- `Microsoft.Extensions.VectorData.IVectorStore`

## Additional Documentation

- [Conceptual documentation](https://learn.microsoft.com/en-us/semantic-kernel/concepts/vector-store-connectors)

## Related Packages

Vector Database utilities:

- `Microsoft.Extensions.VectorData`

Vector Database implementations:

- `Microsoft.SemanticKernel.Connectors.AzureAISearch`
- `Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB`
- `Microsoft.SemanticKernel.Connectors.AzureCosmosNoSQL`
- `Microsoft.SemanticKernel.Connectors.InMemory`
- `Microsoft.SemanticKernel.Connectors.MongoDB`
- `Microsoft.SemanticKernel.Connectors.Pinecone`
- `Microsoft.SemanticKernel.Connectors.Postgres`
- `Microsoft.SemanticKernel.Connectors.Qdrant`
- `Microsoft.SemanticKernel.Connectors.Redis`
- `Microsoft.SemanticKernel.Connectors.Sqlite`
- `Microsoft.SemanticKernel.Connectors.SqlServer`
- `Microsoft.SemanticKernel.Connectors.Weaviate`

## Feedback & Contributing

Microsoft.Extensions.VectorData.Abstractions is released as open source under the [MIT license](https://licenses.nuget.org/MIT). Bug reports and contributions are welcome at [the GitHub repository](https://github.com/microsoft/semantic-kernel).
