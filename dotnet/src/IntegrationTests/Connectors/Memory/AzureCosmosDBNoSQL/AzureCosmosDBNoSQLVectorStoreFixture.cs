// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.Configuration;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.AzureCosmosDBNoSQL;

public class AzureCosmosDBNoSQLVectorStoreFixture : IAsyncLifetime, IDisposable
{
    public const string ConnectionStringKey = "AzureCosmosDBNoSQL:ConnectionString";
    private const string DatabaseName = "testdb";

    private readonly CosmosClient _cosmosClient;

    /// <summary><see cref="Database"/> that can be used to manage the collections in Azure CosmosDB NoSQL.</summary>
    public Database? Database { get; private set; }

    public AzureCosmosDBNoSQLVectorStoreFixture()
    {
        var connectionString = GetConnectionString();
        if (string.IsNullOrWhiteSpace(connectionString))
        {
            throw new ArgumentNullException($"{connectionString} string is not configured");
        }

        var options = new CosmosClientOptions { UseSystemTextJsonSerializerWithOptions = JsonSerializerOptions.Default };

        this._cosmosClient = new CosmosClient(connectionString, options);
    }

    public static string? GetConnectionString()
    {
        var configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(
                path: "testsettings.development.json",
                optional: true,
                reloadOnChange: true
            )
            .AddEnvironmentVariables()
            .AddUserSecrets<AzureCosmosDBNoSQLVectorStoreFixture>()
            .Build();

        return configuration[ConnectionStringKey];
    }

    public async Task InitializeAsync()
    {
        await this._cosmosClient.CreateDatabaseIfNotExistsAsync(DatabaseName);

        this.Database = this._cosmosClient.GetDatabase(DatabaseName);
    }

    public async Task DisposeAsync()
    {
        await this.Database!.DeleteAsync();
    }

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._cosmosClient.Dispose();
        }
    }
}
