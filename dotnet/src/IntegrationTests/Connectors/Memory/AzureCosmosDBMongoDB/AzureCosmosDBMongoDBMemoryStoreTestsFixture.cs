// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;
using MongoDB.Driver;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.AzureCosmosDBMongoDB;

[Obsolete("The IMemoryStore abstraction is being obsoleted")]
public class AzureCosmosDBMongoDBMemoryStoreTestsFixture : IAsyncLifetime
{
    public AzureCosmosDBMongoDBMemoryStore MemoryStore { get; }
    public string DatabaseName { get; }
    public string CollectionName { get; }

    public AzureCosmosDBMongoDBMemoryStoreTestsFixture()
    {
        // Load Configuration
        var configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(
                path: "testsettings.development.json",
                optional: false,
                reloadOnChange: true
            )
            .AddEnvironmentVariables()
            .Build();
        var connectionString = GetSetting(configuration, "ConnectionString");
        this.DatabaseName = "DotNetSKTestDB";
        this.CollectionName = "DotNetSKTestCollection";
        this.MemoryStore = new AzureCosmosDBMongoDBMemoryStore(
            connectionString,
            this.DatabaseName,
            new AzureCosmosDBMongoDBConfig(dimensions: 3)
        );
    }

    public async Task InitializeAsync()
    {
        await this.MemoryStore.CreateCollectionAsync(this.CollectionName);
        await this
            .MemoryStore.UpsertBatchAsync(this.CollectionName, DataHelper.VectorSearchTestRecords)
            .ToListAsync();
    }

    public async Task DisposeAsync()
    {
        await this.MemoryStore.DeleteCollectionAsync(this.CollectionName);
        this.MemoryStore.Dispose();
    }

    private static string GetSetting(IConfigurationRoot configuration, string settingName)
    {
        var settingValue = configuration[$"AzureCosmosDBMongoDB:{settingName}"];
        if (string.IsNullOrWhiteSpace(settingValue))
        {
            throw new ArgumentNullException($"{settingValue} string is not configured");
        }

        return settingValue;
    }
}
