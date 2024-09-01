---
runme:
  document:
    relativePath: README.md
  session:
    id: 01J6KN9VB82HSJP9RRTDE1D75N
    updated: 2024-08-31 07:30:22Z
---

# Microsoft.SemanticKernel.Connectors.Postgres

This connector uses Postgres to implement Semantic Memory. It requires the [pgvector](ht********************************or) extension to be installed on Postgres to implement vector similarity search.

## What is pgvector?

[pgvector](ht********************************or) is an open-source vector similarity search engine for Postgres. It supports exact and approximate nearest neighbor search, L2 distance, inner product, and cosine distance.

How to install the pgvector extension, please refer to its [documentation](ht*********************************************on).

This extension is also available for **Azure Database for PostgreSQL - Flexible Server** and **Azure Cosmos DB for PostgreSQL**.

- [Azure Database for Postgres](ht**********************************************************************************or)
- [Azure Cosmos DB for PostgreSQL](ht***************************************************************************or)

## Quick start

1. To install pgvector using Docker:

```bash {"id":"01J6KNEBBQ8G1WSGWE0ND2CQET"}
docker run -d --name postgres-pgvector -p 5432:5432 -e PO*************RD=my************rd ankane/pgvector

# Ran on 2024-08-31 07:29:59Z for 22.345s exited with 0
Unable to find image 'ankane/pgvector:latest' locally
latest: Pulling from ankane/pgvector
a8********30: Pull complete 
12********91: Pull complete 
14********eb: Pull complete 
56********16: Pull complete 
f9********29: Pull complete 
7a********eb: Pull complete 
78********85: Pull complete 
04********a4: Pull complete 
2c********c9: Pull complete 
6e********18: Pull complete 
f1********b0: Pull complete 
bb********02: Pull complete 
70********e0: Pull complete 
2e********11: Pull complete 
c5********22: Pull complete 
Digest: sh**56:956744bd14e9cbdf639c61c2a2a7c7c2c48a9c8cdd42f7de4ac034f4e96b90f8
Status: Downloaded newer image for ankane/pgvector:latest
0d8b70ce501e3ba9437cdb16b1574d9302a6a898b91b1336b2139e198136a7f4
```

2. Create a database and enable pgvector extension on this database

```bash {"id":"01J6KNEBBQ8G1WSGWE0RYEQ62N"}
docker exec -it postgres-pgvector psql -U postgres

postgres=# CREATE DATABASE sk_demo;
postgres=# \c sk_demo
sk_demo=# CREATE EXTENSION vector;
```

> Note, "Azure Cosmos DB for PostgreSQL" uses `SELECT CREATE_EXTENSION('vector');` to enable the extension.

3. To use Postgres as a semantic memory store:
   > See [Example 14](../../../samples/Concepts/Memory/SemanticTextMemory_Building.cs) and [Example 15](../../../samples/Concepts/Memory/TextMemoryPlugin_MultipleMemoryStore.cs) for more memory usage examples with the kernel.

```csharp {"id":"01J6KNEBBQ8G1WSGWE0SVP3MH4"}
NpgsqlDataSourceBuilder dataSourceBuilder = new Np*******************er("Ho**********st;Po*****32;Database=sk_demo;User Id=postgres;Password=my************rd");
dataSourceBuilder.UseVector();
NpgsqlDataSource dataSource = dataSourceBuilder.Build();

var memoryWithPostgres = new MemoryBuilder()
    .WithPostgresMemoryStore(dataSource, vectorSize: 1536/*, schema: "public" */)
    .WithLoggerFactory(loggerFactory)
    .WithOpenAITextEmbeddingGeneration("te******************02", apiKey)
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

Please read [the documentation](ht*****************************************ng) for more information.

Based on the data rows of your collection table, consider the following statement to create an index.

```sql {"id":"01J6KNEBBQ8G1WSGWE0THVY732"}
DO $$
DECLARE
    collection TEXT;
    c_count INTEGER;
BEGIN
    SELECT 'REPLACE YOUR COLLECTION TABLE NAME' INTO collection;

    -- Get count of records in collection
    EXECUTE format('SELECT count(*) FROM public.%I;', collection) INTO c_count;

    -- Create Index (ht*****************************************ng)
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

We provide the following migration script to help you migrate to the new structure. However, please note that due to the use of collections as table names, you need to make sure that all Collections conform to the [Postgres naming convention](ht*****************************************************************************RS) before migrating.

- Table names may only consist of ASCII letters, digits, and underscores.
- Table names must start with a letter or an underscore.
- Table names may not exceed 63 characters in length.
- Table names are case-insensitive, but it is recommended to use lowercase letters.

```sql {"id":"01J6KNEBBRM2853YN53A7GMZHJ"}
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
            embedding ve*******36),
            timestamp TIMESTAMP WITH TIME ZONE,
            PRIMARY KEY (key)
        );', r.collection);

        -- Get count of records in collection
        SELECT count(*) INTO c_count FROM sk_memory_table WHERE collection = r.collection AND key <> '';

        -- Create Index (ht*****************************************ng)
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
