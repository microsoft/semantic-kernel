// Copyright (c) Microsoft. All rights reserved.

#define DISABLEHOST
namespace SemanticKernel.Data.Nl2Sql.Harness.Schema;

using System;
using System.Threading.Tasks;
using Microsoft.Data.SqlClient;
using Microsoft.Extensions.Configuration;
using Nl2Sql.Schema;
using Xunit;
using Xunit.Abstractions;

/// <summary>
/// Harness for utilizing SqlSchemaProvider to capture live database schema definition: <see cref="SchemaDefinition"/>.
/// </summary>
public sealed class SqlSchemaProviderHarness
{
#if DISABLEHOST
    private const string SkipReason = "Host only runs locally";
#else
    private const string SkipReason = null;
#endif

    private const string ConnectionStringConfiguration = "AdventureWorks";

    private readonly ITestOutputHelper output;
    private readonly IConfiguration config;

    public SqlSchemaProviderHarness(ITestOutputHelper output)
    {
        this.output = output;

        this.config =
            new ConfigurationBuilder()
                .AddJsonFile("testsettings.json", optional: true)
                .AddJsonFile("testsettings.development.json", optional: true)
                .Build();
    }

    [Fact(Skip = SkipReason)]
    public async Task GetSchemaTestAsync()
    {
        var connectionString = this.config.GetConnectionString(ConnectionStringConfiguration);
        using var connection = new SqlConnection(connectionString);
        await connection.OpenAsync().ConfigureAwait(false);

        var provider = new SqlSchemaProvider(connection);

        // GetSchemaAsync is able to filter by table name:
        // var tableNames = new [] { "table1", "table1", ... };

        var schema = await provider.GetSchemaAsync("Product, sales, and customer data for the AdentureWorks company.").ConfigureAwait(false);

        await connection.CloseAsync().ConfigureAwait(false);

        var schemaText = await schema.FormatAsync(PromptSchemaFormatter.Instance).ConfigureAwait(false);
        this.output.WriteLine(schemaText);

        this.output.WriteLine(schema.ToJson());
        await Task.Delay(TimeSpan.FromSeconds(1)).ConfigureAwait(false);
    }
}
