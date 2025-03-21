# Structured Data Plugin - Demo Application

This sample demonstrates how to use the Semantic Kernel's Structured Data Plugin to interact with relational databases through Entity Framework Core. The demo shows how to perform database operations using natural language queries, which are translated into appropriate database commands.

## Semantic Kernel Features Used

- Structured Data Plugin - Enables natural language interactions with databases
- Entity Framework 6 Integration - Provides database access layer
- OpenAI Function Calling - Used to parse natural language into structured database operations

## Prerequisites

- OpenAI API key
- Function Calling enabled model (e.g., gpt-4o)
- Relational database (e.g., SQL Server)
- .NET 8.0 or higher

## Database Setup

1. Create the Products table in your database:

```sql
-- SQL Server example
CREATE TABLE Products (
    Id uniqueidentifier DEFAULT newsequentialid() NOT NULL,
    Name nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
    Price decimal(18,2) NOT NULL,
    DateCreated datetime DEFAULT getdate() NOT NULL,
    CONSTRAINT Products_PK PRIMARY KEY (Id)
);
```

## Key Components

### Product Entity

The demo uses a `Product` entity as an example of structured data. This entity represents items in a database table named "Test1".

### ApplicationDbContext

`ApplicationDbContext` is an Entity Framework Core database context that:

- Inherits from `DbContext`
- Configures database connection using either:
  - Configuration string from IConfiguration
  - Direct connection string
- Disables database initialization
- Maps the `Product` entity to the "Test1" table

### Connection String Setup

You can configure the connection string using one of these methods:

1. Using appsettings.json:

```json
{
  "ConnectionStrings": {
    "ApplicationDbContext": "your_connection_string"
  }
}
```

2. Using appsettings.Development.json (for development environment):

```json
{
  "ConnectionStrings": {
    "ApplicationDbContext": "your_connection_string"
  }
}
```

3. Using user secrets (recommended for development):

```bash
dotnet user-secrets set "ConnectionStrings:ApplicationDbContext" "your_connection_string"
```

4. Using environment variables:

```bash
set ConnectionStrings__ApplicationDbContext="your_connection_string"
```

The application uses the following configuration hierarchy (highest to lowest priority):

1. User Secrets
2. Environment Variables
3. appsettings.json

## Usage Examples

The demo showcases various database operations using natural language:

1. Inserting new records:

```csharp
var result = await kernel.InvokeAsync("Insert a new product with name 'Sample Product' and price 29.99");
```

2. Querying data:

```csharp
var result = await kernel.InvokeAsync("Find all products under $50");
```

3. Updating records:

```csharp
var result = await kernel.InvokeAsync("Update the price of 'Sample Product' to 39.99");
```

4. Deleting records:

```csharp
var result = await kernel.InvokeAsync("Delete the product named 'Sample Product'");
```

## Important Notes

- The plugin uses OpenAI's function calling feature to parse natural language into structured database operations
- Database operations are performed through Entity Framework Core
- The demo includes proper error handling and transaction management
- Connection strings should be secured and not committed to source control
- For production environments, consider using Azure Key Vault or similar secure configuration storage

## Additional Resources

- [Entity Framework Core Documentation](https://learn.microsoft.com/en-us/ef/core/)
- [Semantic Kernel Documentation](https://learn.microsoft.com/en-us/semantic-kernel/overview/)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [Safe Storage of App Secrets in Development](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets)
