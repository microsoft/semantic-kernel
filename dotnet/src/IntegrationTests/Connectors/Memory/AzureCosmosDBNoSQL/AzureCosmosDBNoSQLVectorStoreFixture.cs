// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.Configuration;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.AzureCosmosDBNoSQL;

public class AzureCosmosDBNoSQLVectorStoreFixture : IAsyncLifetime, IDisposable
{
    private const string DatabaseName = "testdb";

    private readonly List<string> _testCollections = ["sk-test-hotels", "sk-test-contacts"];

    private readonly CosmosClient _cosmosClient;

    /// <summary>Main test collection for tests.</summary>
    public string TestCollection => this._testCollections[0];

    /// <summary><see cref="Database"/> that can be used to manage the collections in Azure CosmosDB NoSQL.</summary>
    public Database? Database { get; private set; }

    public AzureCosmosDBNoSQLVectorStoreFixture()
    {
        var configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(
                path: "testsettings.development.json",
                optional: false,
                reloadOnChange: true
            )
            .AddEnvironmentVariables()
            .Build();

        var connectionString = GetConnectionString(configuration);

        this._cosmosClient = new CosmosClient(connectionString);
    }

    public async Task InitializeAsync()
    {
        await this._cosmosClient.CreateDatabaseIfNotExistsAsync(DatabaseName);

        this.Database = this._cosmosClient.GetDatabase(DatabaseName);

        foreach (var collection in this._testCollections)
        {
            await this.Database.CreateContainerIfNotExistsAsync(new ContainerProperties(collection, "/key"));
        }
    }

    public async Task DisposeAsync()
    {
        foreach (var collection in this._testCollections)
        {
            await this.Database!
                .GetContainer(collection)
                .DeleteContainerAsync();
        }

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

    #region private

    private static string GetConnectionString(IConfigurationRoot configuration)
    {
        var settingValue = configuration["AzureCosmosDBNoSQL:ConnectionString"];
        if (string.IsNullOrWhiteSpace(settingValue))
        {
            throw new ArgumentNullException($"{settingValue} string is not configured");
        }

        return settingValue;
    }

    #endregion
}
