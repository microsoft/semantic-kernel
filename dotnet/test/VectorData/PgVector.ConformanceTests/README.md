# PostgreSQL Vector Store Conformance Tests

This project contains conformance tests for the PostgreSQL (pgvector) Vector Store implementation.

## Running the Tests

By default, the tests will automatically use a testcontainer to spin up a PostgreSQL instance with the pgvector extension. Docker must be running on your machine for this to work.

### Using an External PostgreSQL Instance

If you want to run the tests against an external PostgreSQL instance (e.g., a cloud database, local PostgreSQL server, or any other instance), you can provide a connection string through one of the following methods:

**Note**: The external PostgreSQL instance must have the `pgvector` extension available. The tests will attempt to create the extension if it doesn't exist.

#### Option 1: Environment Variable

Set the `Postgres__ConnectionString` environment variable:

```bash
# Bash/Linux/macOS
export Postgres__ConnectionString="Host=myserver.postgres.database.azure.com;Database=mydb;Username=myuser;Password=mypassword;"

# PowerShell
$env:Postgres__ConnectionString = "Host=myserver.postgres.database.azure.com;Database=mydb;Username=myuser;Password=mypassword;"
```

#### Option 2: Configuration File

Create a `testsettings.development.json` file in this directory with the following content:

```json
{
  "Postgres": {
    "ConnectionString": "Host=myserver.postgres.database.azure.com;Database=mydb;Username=myuser;Password=mypassword;"
  }
}
```

This file is git-ignored and safe for local development.

#### Option 3: User Secrets

```bash
cd test/VectorData/PgVector.ConformanceTests
dotnet user-secrets set "Postgres:ConnectionString" "Host=myserver.postgres.database.azure.com;Database=mydb;Username=myuser;Password=mypassword;"
```

## Benefits of Using an External Instance

Using an external PostgreSQL instance can be beneficial when:
- You want to avoid the overhead of spinning up Docker containers
- You need to test against a specific PostgreSQL version or configuration
- You want faster test execution (no container startup time)
- You're running tests in an environment where Docker is not available
- You need to test against cloud-hosted PostgreSQL (e.g., Azure Database for PostgreSQL, AWS RDS)

## Prerequisites for External Instances

The external PostgreSQL instance must:
- Have the `pgvector` extension installed and available
- Have sufficient permissions for the connecting user to:
  - Create the vector extension (if not already created)
  - Create tables and indexes
  - Insert, update, and delete data
