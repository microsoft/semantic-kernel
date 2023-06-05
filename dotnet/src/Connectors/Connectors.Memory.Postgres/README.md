# Microsoft.SemanticKernel.Connectors.Memory.Postgres

This connector uses Postgres to implement Semantic Memory. It requires the [pgvector](https://github.com/pgvector/pgvector) extension to be installed on Postgres to implement vector similarity search.

## What is pgvector?

[pgvector](https://github.com/pgvector/pgvector) is an open-source vector similarity search engine for Postgres. It supports exact and approximate nearest neighbor search, L2 distance, inner product, and cosine distance.

How to install the pgvector extension, please refer to its [documentation](https://github.com/pgvector/pgvector#installation).

## Quick start

1. To install pgvector using Docker:

```bash
docker run -d --name postgres-pgvector -p 5432:5432 -e POSTGRES_PASSWORD=mysecretpassword ankane/pgvector
```

2. To use Postgres as a semantic memory store:

```csharp
NpgsqlDataSourceBuilder dataSourceBuilder = new NpgsqlDataSourceBuilder("Host=localhost;Port=5432;Database=sk_memory;User Id=postgres;Password=mysecretpassword");
dataSourceBuilder.UseVector();// Use pgvector
using NpgsqlDataSource dataSource = dataSourceBuilder.Build();

PostgresMemoryStore memoryStore = await PostgresMemoryStore.ConnectAsync(dataSource, vectorSize: 1536);

IKernel kernel = Kernel.Builder
    .WithLogger(ConsoleLogger.Log)
    .WithOpenAITextEmbeddingGenerationService("text-embedding-ada-002", Env.Var("OPENAI_API_KEY"))
    .WithMemoryStorage(memoryStore)
    .Build();
```

