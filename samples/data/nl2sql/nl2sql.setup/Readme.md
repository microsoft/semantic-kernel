# Setup: Natural Language to SQL Console

## LLM Configuration

This project aligns with the configuration strategy used throughout this repo: 
[Common variables](../../../../dotnet/samples/KernelSyntaxExamples/README.md)

Choose the settings according to your endpoint (*Azure Open AI* or *Open AI*):

#### Azure Open AI
- AZURE_OPENAI_DEPLOYMENT_NAME
- AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT_NAME
- AZURE_OPENAI_ENDPOINT
- AZURE_OPENAI_KEY

#### OpenAI
- OPENAI_API_KEY
- OPENAI_API_COMPLETION_MODEL
- OPENAI_API_EMBEDDINGS_MODEL

### Examples
To set your secrets with .NET 
[Secret Manager](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets):

```
cd samples/data/nl2sql/nl2sql.console

dotnet user-secrets set "AZURE_OPENAI_DEPLOYMENT_NAME" "gpt-4"
```

To set your secrets with environment variables, use either `SET` or `SETX`:
```
SET AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
```
OR
```
SETX AZURE_OPENAI_DEPLOYMENT_NAME "gpt-4"
```
## SQL Configuration

#### Setup

- `AdventureWorksLT` - This is the *light* version of the well known sample database.
    - [Azure Setup](https://learn.microsoft.com/en-us/sql/samples/adventureworks-install-configure#deploy-to-azure-sql-database)
    - [Local Setup](https://learn.microsoft.com/en-us/sql/samples/adventureworks-install-configure#download-backup-files)
- `DescriptionTest` - This is a database designed to exercise the description semantics of the schema expression.  The table and column names are completely devoid of meaning; however, description meta-data has been injected: [DescriptionTest.yaml](../nl2sql.config/schemas/DescriptionTest.yaml)
    - [Create a blank database.](https://learn.microsoft.com/en-us/azure/azure-sql/database/single-database-create-quickstart?view=azuresql&tabs=azure-portal)
    > Note: ['Basic'](https://learn.microsoft.com/en-us/azure/azure-sql/database/purchasing-models?view=azuresql-db) is an adequate service-tier for this sample.
    - [Create and populate table A - (Users)](./sql//DescriptionTest) (`A.sql`)
    - [Create and populate table B - (Interest Categories)](./sql//DescriptionTest) (`B.sql`)
    - [Create and populate table C - (Association of users & categories)](./sql//DescriptionTest) (`C.sql`)
- Ensure [Network Access](https://learn.microsoft.com/en-us/azure/azure-sql/database/connectivity-settings?view=azuresql&tabs=azure-portal) if connecting to Azure hosted SQL.
    > Note: [Connecting to Azure SQL database via SSMS](https://learn.microsoft.com/en-us/sql/ssms/object/connect-to-an-instance-from-object-explorer) will prompt to configure an IP based firewall rule.

#### Connection Strings
Use the .NET [Secret Manager](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets)
to define the connection strings to the two databases targeted by this sample:

```
cd samples/data/nl2sql/nl2sql.console

dotnet user-secrets set ConnectionStrings:AdventureWorksLT "..."
dotnet user-secrets set ConnectionStrings:DescriptionTest "..."
```

## Advanced (Custom Schema)
The following steps allows you to describe and target your own database schema.

1. Define the connection string so it can be consumed to reverse engineer your schema and also by the console:
```
cd samples/data/nl2sql/nl2sql.console

dotnet user-secrets set ConnectionStrings:YourSchema "..."
```
2. Reverse-engineer your schema with the [development harness](../nl2sql.harness/SqlSchemaProviderHarness.cs) by editing the `ReverseEngineerSchemaAsync` method:
```
await this.CaptureSchemaAsync(
    "YourSchema",
    "A description for your-schema.").ConfigureAwait(false);
```
3. Review YourSchema.json in the [schemas](../nl2sql.config/schemas/) folder.
1. Replace the default configuration with your own in [SchemaDefinitions.cs](//nl2sql.console/SchemasDefinitions.cs):
```
public static IEnumerable<string> GetNames()
{
    yield return "yourschema";
}
```
