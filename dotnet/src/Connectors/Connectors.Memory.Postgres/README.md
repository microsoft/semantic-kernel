# Microsoft.SemanticKernel.Connectors.Memory.Postgres

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
docker run -d --name postgres-pgvector -p 5432:5432 -e POSTGRES_PASSWORD=mysecretpassword ankane/pgvector
```

2. Create a database and enable pgvector extension on this database

```bash
docker exec -it postgres-pgvector psql -U postgres

postgres=# CREATE DATABASE sk_demo;
postgres=# \c sk_demo
sk_demo=# CREATE EXTENSION vector;
```

> Note, "Azure Cosmos DB for PostgreSQL" uses `SELECT CREATE_EXTENSION('vector');` to enable the extension.

3. To use Postgres as a semantic memory store:

```csharp
NpgsqlDataSourceBuilder dataSourceBuilder = new NpgsqlDataSourceBuilder("Host=localhost;Port=5432;Database=sk_demo;User Id=postgres;Password=mysecretpassword");
dataSourceBuilder.UseVector();
NpgsqlDataSource dataSource = dataSourceBuilder.Build();

PostgresMemoryStore memoryStore = new PostgresMemoryStore(dataSource, vectorSize: 1536/*, schema: "public" */);

IKernel kernel = Kernel.Builder
    .WithLogger(ConsoleLogger.Log)
    .WithOpenAITextEmbeddingGenerationService("text-embedding-ada-002", Env.Var("OPENAI_API_KEY"))
    .WithMemoryStorage(memoryStore)
    //.WithPostgresMemoryStore(dataSource, vectorSize: 1536, schema: "public") // This method offers an alternative approach to registering Postgres memory store.
    .Build();
```

### Create Index

> By default, pgvector performs exact nearest neighbor search, which provides perfect recall.

> You can add an index to use approximate nearest neighbor search, which trades some recall for performance. Unlike typical indexes, you will see different results for queries after adding an approximate index.

> Three keys to achieving good recall are:
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

## Migration from older versions
Since Postgres Memory connector has been re-implemented, the new implementation uses a separate table to store each Collection.

We provide the following migration script to help you migrate to the new structure. However, please note that due to the use of collections as table names, you need to make sure that all Collections conform to the [Postgres naming convention](https://www.postgresql.org/docs/15/sql-syntax-lexical.html#SQL-SYNTAX-IDENTIFIERS) before migrating.

- Table names may only consist of ASCII letters, digits, and underscores.
- Table names must start with a letter or an underscore.
- Table names may not exceed 63 characters in length.
- Table names are case-insensitive, but it is recommended to use lowercase letters.

```sql
-- Create new tables, each with the name of the collection field value
DO $$
DECLARE
    r record;
    c_count integer;
BEGIN
    FOR r IN SELECT DISTINCT collection FROM sk_memory_table LOOP

        -- Drop Table (This will delete the table that already exists. Please consider carefully if you think you need to cancel this comment!)
        -- EXECUTE format('DROP TABLE IF EXISTS %I;', r.collection);

        -- Create Table (Modify vector size on demand)
        EXECUTE format('CREATE TABLE public.%I (
            key TEXT NOT NULL,
            metadata JSONB,
            embedding vector(1536),
            timestamp TIMESTAMP WITH TIME ZONE,
            PRIMARY KEY (key)
        );', r.collection);

        -- Get count of records in collection
        SELECT count(*) INTO c_count FROM sk_memory_table WHERE collection = r.collection AND key <> '';

        -- Create Index (https://github.com/pgvector/pgvector#indexing)
        IF c_count > 10000000 THEN
            EXECUTE format('CREATE INDEX %I
                ON public.%I USING ivfflat (embedding vector_cosine_ops) WITH (lists = %s);',
                r.collection || '_ix', r.collection, ROUND(sqrt(c_count)));
        ELSIF c_count > 10000 THEN
            EXECUTE format('CREATE INDEX %I
                ON public.%I USING ivfflat (embedding vector_cosine_ops) WITH (lists = %s);',
                r.collection || '_ix', r.collection, c_count / 1000);
        END IF;
    END LOOP;
END $$;

-- Copy data from the old table to the new table
DO $$
DECLARE
    r record;
BEGIN
    FOR r IN SELECT DISTINCT collection FROM sk_memory_table LOOP
        EXECUTE format('INSERT INTO public.%I (key, metadata, embedding, timestamp)
            SELECT key, metadata::JSONB, embedding, to_timestamp(timestamp / 1000.0) AT TIME ZONE ''UTC'' 
            FROM sk_memory_table WHERE collection = %L AND key <> '''';', r.collection, r.collection);
    END LOOP;
END $$;

-- Drop old table (After ensuring successful execution, you can remove the following comments to remove sk_memory_table.)
-- DROP TABLE IF EXISTS sk_memory_table;
```
