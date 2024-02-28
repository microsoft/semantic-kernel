// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Connectors.Memory.AzureCosmosDBMongoVCore;
using MongoDB.Driver;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.AzureCosmosDB;

public class AzureCosmosDBMemoryStoreTestsFixture : IAsyncLifetime
{
    #pragma warning disable CA1859 // Use concrete types when possible for improved performance
    private readonly IMongoClient _mongoClient = null!;
    #pragma warning restore CA1859 // Use concrete types when possible for improved performance

    public AzureCosmosDBMongoVCore MemoryStore { get; }
    public string DatabaseName { get; }
    public string CollectionName { get; }
    public string indexName = default;
    public string kind = "vector_hnsw",
    public int numLists = 1, 
    public string similarity = "COS",
    public int dimensions = 3,
    public int numberOfConnections = 16,
    public int efConstruction = 64,
    public int efSearch = 40
    
    public AzureCosmosDBMemoryStoreTestsFixture()
    {
        // Load Configuration
        var configuration new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: false, reloadOnChange: true)
            .AddEnvironmentVariables()
            .Build()

        var connectionString = GetSetting(configuration, "ConnectionString");
        this.DatabaseName = "DotNetSKTestDB"
        this.CollectionNameName = "DotNetSKTestCollection"
        this._mongoClient = new MongoClient(connectionString);
        this.MemoryStore = new AzureCosmosDBMongoVCoreMemoryStore(
            this._mongoClient,
            this.DatabaseName,
            this.indexName,
            this.kind,
            this.numLists,
            this.similarity,
            this.dimensions,
            this.numberOfConnections,
            this.efConstruction,
            this.efSearch
            )    
    }

    public async Task InitializeAsync()
    {
        await this.MemoryStore.UpsertBatchAsync(this.CollectionName, DataHelper.VectorSearchTestRecords).ToListAsync();
    }

    public async Task DisposeAsync() 
    {
        var database = this._mongoClient.GetDatabase(databaseName);
        collectionNames = await database.ListCollectionNamesAsync();

        foreach (var collectionName in collectionNames)
        {
            await database.DropCollectionAsync(collectionName);
        }

        this.MemoryStore.Dispose();
    }

    private static string GetSetting(IConfigurationRoot configuration, string settingName)
    {
        var settingValue = configuration[$"MongoDB:{settingName}"];
        if (string.IsNullOrWhiteSpace(settingValue))
        {
            throw new ArgumentNullException($"{settingValue} string is not configured");
        }

        return settingValue;
    }
}