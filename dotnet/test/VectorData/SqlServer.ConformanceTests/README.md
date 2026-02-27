# SQL Server Vector Store Conformance Tests

This project contains conformance tests for the SQL Server Vector Store implementation.

## Running the Tests

By default, the tests will automatically use a testcontainer to spin up a SQL Server instance. Docker must be running on your machine for this to work.

### Using an External SQL Server Instance

If you want to run the tests against an external SQL Server instance (e.g., Azure SQL, a local SQL Server, or any other instance), you can provide a connection string through one of the following methods:

#### Option 1: Environment Variable

Set the `SqlServer__ConnectionString` environment variable:

```bash
# Bash/Linux/macOS
export SqlServer__ConnectionString="Server=myserver.database.windows.net;Database=mydb;User Id=myuser;Password=mypassword;"

# PowerShell
$env:SqlServer__ConnectionString = "Server=myserver.database.windows.net;Database=mydb;User Id=myuser;Password=mypassword;"
```

#### Option 2: Configuration File

Create a `testsettings.development.json` file in this directory with the following content:

```json
{
  "SqlServer": {
    "ConnectionString": "Server=myserver.database.windows.net;Database=mydb;User Id=myuser;Password=mypassword;"
  }
}
```

This file is git-ignored and safe for local development.

#### Option 3: User Secrets

```bash
cd test/VectorData/SqlServer.ConformanceTests
dotnet user-secrets set "SqlServer:ConnectionString" "Server=myserver.database.windows.net;Database=mydb;User Id=myuser;Password=mypassword;"
```

## Benefits of Using an External Instance

Using an external SQL Server instance can be beneficial when:
- You want to avoid the overhead of spinning up Docker containers
- You need to test against Azure SQL specifically
- You want faster test execution (no container startup time)
- You're running tests in an environment where Docker is not available
