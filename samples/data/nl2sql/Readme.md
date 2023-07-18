# Natural Language to SQL Console

`Nl2Sql` provides a sandbox for experimentation and testing of the abilities of LLM's to generate SQL queries based on natural language expression.

[GPT-4 has raised the bar](https://medium.com/querymind/gpt-4s-sql-mastery-2cd1f3dea543) on query generation capabilities.

While other approaches exist in this space, this sample serves to showcase the capability (and limitations) of LLM using [Semantic Kernel](https://github.com/microsoft/semantic-kernel) for *dotnet*.
Whether or not this approach provides an adequate or cost-effective solution for any particular use-case depends on its specific context and associated expectations.

While a full ecosystem for data-retrieval and processing includes components and capabilities in addition to natural language query generation, this sample aims to:

1. Demonstrate the natural ability of LLM to reason over an objective and generate a SQL query.
1. Allow exploration of any *(SQL Server)* database (on-premises or cloud hosted).

## Sample Info

The default configuration targets two sample schemas, but it may be configured to target your own database as well.

This sample is organized as follows:

- `nl2sql.config` - Contains [setup instructions](./nl2sql.config/Readme.md), [data-schemas](./nl2sql.config/schemas/Readme.md) and [semantic-prompts](./nl2sql.config/prompts/Readme.md).
- `nl2sql.console` - A console application that translates a natural language objective into a SQL query.
- `nl2sql.library` - A console application that translates a natural language objective into a SQL query.
- `nl2sql.harness` - A dev-harness for reverse-engineering live schema.
- `nl2sql.sln` - A *Visual Studio* solution.

The first step to run the sample is to perform the [initial setup and configuration](./nl2sql.config/Readme.md): [nl2sql.setup/Readme.md](./nl2sql.config/Readme.md).
