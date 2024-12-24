﻿# Microsoft.SemanticKernel.Connectors.Postgres

This connector uses Postgres to implement Semantic Memory. It requires the [pgvector](https://github.com/pgvector/pgvector) extension to be installed on Postgres to implement vector similarity search.

## What is pgvector?

[pgvector](https://github.com/pgvector/pgvector) is an open-source vector similarity search engine for Postgres. It supports exact and approximate nearest neighbor search, L2 distance, inner product, and cosine distance.

How to install the pgvector extension, please refer to its [documentation](https://github.com/pgvector/pgvector#installation).

This extension is also available for **Azure Database for PostgreSQL - Flexible Server** and **Azure Cosmos DB for PostgreSQL**.

- [Azure Database for Postgres](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/how-to-use-pgvector)
- [Azure Cosmos DB for PostgreSQL](https://learn.microsoft.com/en-us/azure/cosmos-db/postgresql/howto-use-pgvector)

## Quick start

1. To install pgvector using Docker:

```bash
docker run -d --name postgres-pgvector -p 5432:5432 -e POSTGRES_PASSWORD=mysecretpassword pgvector/pgvector
```

2. Create a database and enable pgvector extension on this database

```bash
docker exec -it postgres-pgvector psql -U postgres

postgres=# CREATE DATABASE sk_demo;
postgres=# \c sk_demo
sk_demo=# CREATE EXTENSION vector;
```

> Note, "Azure Cosmos DB for PostgreSQL" uses `SELECT CREATE_EXTENSION('vector');` to enable the extension.

### Using PostgresVectorStore

See [this sample](../../../samples/Concepts/Memory/VectorStore_VectorSearch_MultiStore_Postgres.cs) for an example of using the vector store.

### Using  PostgresMemoryStore

> See [Example 14](../../../samples/Concepts/Memory/SemanticTextMemory_Building.cs) and [Example 15](../../../samples/Concepts/Memory/TextMemoryPlugin_MultipleMemoryStore.cs) for more memory usage examples with the kernel.

```csharp
NpgsqlDataSourceBuilder dataSourceBuilder = new NpgsqlDataSourceBuilder("Host=localhost;Port=5432;Database=sk_demo;User Id=postgres;Password=mysecretpassword");
dataSourceBuilder.UseVector();
NpgsqlDataSource dataSource = dataSourceBuilder.Build();

var memoryWithPostgres = new MemoryBuilder()
    .WithPostgresMemoryStore(dataSource, vectorSize: 1536/*, schema: "public" */)
    .WithLoggerFactory(loggerFactory)
    .WithOpenAITextEmbeddingGeneration("text-embedding-ada-002", apiKey)
    .Build();

var memoryPlugin = kernel.ImportPluginFromObject(new TextMemoryPlugin(memoryWithPostgres));
```

### Create Index

> By default, pgvector performs exact nearest neighbor search, which provides perfect recall.

> You can add an index to use approximate nearest neighbor search, which trades some recall for performance. Unlike typical indexes, you will see different results for queries after adding an approximate index.

> Three keys to achieving good recall are:
>
> - Create the index after the table has some data
> - Choose an appropriate number of lists - a good place to start is rows / 1000 for up to 1M rows and sqrt(rows) for over 1M rows
> - When querying, specify an appropriate number of probes (higher is better for recall, lower is better for speed) - a good place to start is sqrt(lists)

Please read [the documentation](https://github.com/pgvector/pgvector#indexing) for more information.

Based on the data rows of your collection table, consider the following statement to create an index.

```sql
DO $$
DECLARE
    collection TEXT;
    c_count INTEGER;
BEGIN
    SELECT 'REPLACE YOUR COLLECTION TABLE NAME' INTO collection;

    -- Get count of records in collection
    EXECUTE format('SELECT count(*) FROM public.%I;', collection) INTO c_count;

    -- Create Index (https://github.com/pgvector/pgvector#indexing)
    IF c_count > 10000000 THEN
        EXECUTE format('CREATE INDEX %I ON public.%I USING ivfflat (embedding vector_cosine_ops) WITH (lists = %s);',
                       collection || '_ix', collection, ROUND(sqrt(c_count)));
    ELSIF c_count > 10000 THEN
        EXECUTE format('CREATE INDEX %I ON public.%I USING ivfflat (embedding vector_cosine_ops) WITH (lists = %s);',
                       collection || '_ix', collection, c_count / 1000);
    END IF;
END $$;
```
