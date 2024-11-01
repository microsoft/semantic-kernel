---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: dmytrostruk
date: 2024-08-20
deciders: sergeymenshykh, markwallace, rbarreto, westey-m
---

# Entity Framework as Vector Store Connector

## Context and Problem Statement

This ADR contains investigation results about adding Entity Framework as Vector Store connector to the Semantic Kernel codebase. 

Entity Framework is a modern object-relation mapper that allows to build a clean, portable, and high-level data access layer with .NET (C#) across a variety of databases, including SQL Database (on-premises and Azure), SQLite, MySQL, PostgreSQL, Azure Cosmos DB and more. It supports LINQ queries, change tracking, updates and schema migrations. 

One of the huge benefits of Entity Framework for Semantic Kernel is the support of multiple databases. In theory, one Entity Framework connector can work as a hub to multiple databases at the same time, which should simplify the development and maintenance of integration with these databases.

However, there are some limitations, which won't allow Entity Framework to fit in updated Vector Store design.

### Collection Creation

In new Vector Store design, interface `IVectorStoreRecordCollection<TKey, TRecord>` contains methods to manipulate with database collections:
- `CollectionExistsAsync`
- `CreateCollectionAsync`
- `CreateCollectionIfNotExistsAsync`
- `DeleteCollectionAsync`

In Entity Framework, collection (also known as schema/table) creation using programmatic approach is not recommended in production scenarios. The recommended approach is to use Migrations (in case of code-first approach), or to use Reverse Engineering (also known as scaffolding/database-first approach). Programmatic schema creation is recommended only for testing/local scenarios. Also, collection creation process differs for different databases. For example, MongoDB EF Core provider doesn't support schema migrations or database-first/model-first approaches. Instead, the collection is created automatically when a document is inserted for the first time, if collection doesn't already exist. This brings the complexity around methods such as `CreateCollectionAsync` from `IVectorStoreRecordCollection<TKey, TRecord>` interface, since there is no abstraction around collection management in EF that will work for most databases. For such cases, the recommended approach is to rely on automatic creation or handle collection creation individually for each database. As an example, in MongoDB it's recommended to use MongoDB C# Driver directly.

Sources:
- https://learn.microsoft.com/en-us/ef/core/managing-schemas/
- https://learn.microsoft.com/en-us/ef/core/managing-schemas/ensure-created
- https://learn.microsoft.com/en-us/ef/core/managing-schemas/migrations/applying?tabs=dotnet-core-cli#apply-migrations-at-runtime
- https://github.com/mongodb/mongo-efcore-provider?tab=readme-ov-file#not-supported--out-of-scope-features

### Key Management

It won't be possible to define one set of valid key types, since not all databases support all types as keys. In such case, it will be possible to support only standard type for keys such as `string`, and then the conversion should be performed to satisfy key restrictions for specific database. This removes the advantage of unified connector implementation, since key management should be handled for each database individually.

Sources:
- https://learn.microsoft.com/en-us/ef/core/modeling/keys?tabs=data-annotations

### Vector Management

`ReadOnlyMemory<T>` type, which is used in most SK connectors today to hold embeddings is not supported in Entity Framework out-of-the-box. When trying to use this type, the following error occurs:

```
The property '{Property Name}' could not be mapped because it is of type 'ReadOnlyMemory<float>?', which is not a supported primitive type or a valid entity type. Either explicitly map this property, or ignore it using the '[NotMapped]' attribute or by using 'EntityTypeBuilder.Ignore' in 'OnModelCreating'.
```

However, it's possible to use `byte[]` type or create explicit mapping to support `ReadOnlyMemory<T>`. It's already implemented in `pgvector` package, but it's not clear whether it will work with different databases.

Sources: 
- https://github.com/pgvector/pgvector-dotnet/blob/master/README.md#entity-framework-core
- https://github.com/pgvector/pgvector-dotnet/blob/master/src/Pgvector/Vector.cs
- https://github.com/pgvector/pgvector-dotnet/blob/master/src/Pgvector.EntityFrameworkCore/VectorTypeMapping.cs

### Testing

Create Entity Framework connector and write the tests using SQLite database doesn't mean that this integration will work for other EF-supported databases. Each database implements its own set of Entity Framework features, so in order to ensure that Entity Framework connector covers main use-cases with specific database, unit/integration tests should be added using each database separately. 

Sources:
- https://github.com/mongodb/mongo-efcore-provider?tab=readme-ov-file#supported-features

### Compatibility

It's not possible to use latest Entity Framework Core package and develop it for .NET Standard. Last version of EF Core which supports .NET Standard was version 5.0 (latest EF Core version is 8.0). Which means that Entity Framework connector can target .NET 8.0 only (which is different from other available SK connectors today, which target both net8.0 and netstandard2.0).

Another way would be to use Entity Framework 6, which can target both net8.0 and netstandard2.0, but this version of Entity Framework is no longer being actively developed. Entity Framework Core offers new features that won't be implemented in EF6.

Sources: 
- https://learn.microsoft.com/en-us/ef/core/miscellaneous/platforms
- https://learn.microsoft.com/en-us/ef/efcore-and-ef6/

### Existence of current SK connectors

Taking into account that Semantic Kernel already has some integration with databases, which are also supported Entity Framework, there are multiple options how to proceed:
- Support both Entity Framework and DB connector (e.g. `Microsoft.SemanticKernel.Connectors.EntityFramework` and `Microsoft.SemanticKernel.Connectors.MongoDB`) - in this case both connectors should produce exactly the same outcome, so additional work will be required (such as implementing the same set of unit/integration tests) to ensure this state. Also, any modifications to the logic should be applied in both connectors. 
- Support just one Entity Framework connector (e.g. `Microsoft.SemanticKernel.Connectors.EntityFramework`) - in this case, existing DB connector should be removed, which may be a breaking change to existing customers. An additional work will be required to ensure that Entity Framework covers exactly the same set of features as previous DB connector.
- Support just one DB connector (e.g. `Microsoft.SemanticKernel.Connectors.MongoDB`) - in this case, if such connector already exists - no additional work is required. If such connector doesn't exist and it's important to add it - additional work is required to implement that DB connector.


Table with Entity Framework and Semantic Kernel database support (only for databases which support vector search):

|Database Engine|Maintainer / Vendor|Supported in EF|Supported in SK|Updated to SK memory v2 design
|-|-|-|-|-|
|Azure Cosmos|Microsoft|Yes|Yes|Yes|
|Azure SQL and SQL Server|Microsoft|Yes|Yes|No|
|SQLite|Microsoft|Yes|Yes|No|
|PostgreSQL|Npgsql Development Team|Yes|Yes|No|
|MongoDB|MongoDB|Yes|Yes|No|
|MySQL|Oracle|Yes|No|No|
|Oracle DB|Oracle|Yes|No|No|
|Google Cloud Spanner|Cloud Spanner Ecosystem|Yes|No|No|

**Note**:
One database engine can have multiple Entity Framework integrations, which can be maintained by different vendors (e.g. there are 2 MySQL EF NuGet packages - one is maintained by Oracle and another one is maintained by Pomelo Foundation Project).

Vector DB connectors which are additionally supported in Semantic Kernel:
- Azure AI Search
- Chroma
- Milvus
- Pinecone
- Qdrant
- Redis
- Weaviate

Sources:
- https://learn.microsoft.com/en-us/ef/core/providers/?tabs=dotnet-core-cli#current-providers

## Considered Options

- Add new `Microsoft.SemanticKernel.Connectors.EntityFramework` connector.
- Do not add `Microsoft.SemanticKernel.Connectors.EntityFramework` connector, but add a new connector for individual database when needed.

## Decision Outcome

Based on the above investigation, the decision is not to add Entity Framework connector, but to add a new connector for individual database when needed. The reason for this decision is that Entity Framework providers do not uniformly support collection management operations and will require database specific code for key handling and object mapping. These factors will make use of an Entity Framework connector unreliable and it will not abstract away the underlying database. Additionally the number of vector databases that Entity Framework supports that Semantic Kernel does not have a memory connector for is very small.
