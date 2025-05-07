# Microsoft.SemanticKernel.Connectors.Postgres

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

For more information on using Postgres as a vector store, see the [PostgresVectorStore](https://learn.microsoft.com/semantic-kernel/concepts/vector-store-connectors/out-of-the-box-connectors/postgres-connector) documentation.

Use the [getting started instructions](https://learn.microsoft.com/semantic-kernel/concepts/vector-store-connectors/?pivots=programming-language-csharp#getting-started-with-vector-store-connectors) on the Microsoft Leearn site to learn more about using the vector store.
