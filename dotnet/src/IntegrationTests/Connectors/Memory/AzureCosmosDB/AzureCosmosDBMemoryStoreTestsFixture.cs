// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoVCore;
using MongoDB.Driver;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.AzureCosmosDB;

public class AzureCosmosDBMemoryStoreTestsFixture : IAsyncLifetime
{
    public AzureCosmosDBMongoVCoreMemoryStore MemoryStore { get; }
    public string DatabaseName { get; }
    public string CollectionName { get; }

    public string indexName = "default_index";
    public string kind = "vector_hnsw";
    public int numLists = 1;
    public string similarity = "COS";
    public int dimensions = 3;
    public int numberOfConnections = 16;
    public int efConstruction = 64;
    public int efSearch = 40;
    
    public AzureCosmosDBMemoryStoreTestsFixture()
    {
        // Load Configuration
        var configuration = new ConfigurationBuilder().AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true).AddJsonFile(path: "testsettings.development.json", optional: false, reloadOnChange: true).AddEnvironmentVariables().Build();

        var connectionString = GetSetting(configuration, "ConnectionString");
        this.DatabaseName = "DotNetSKTestDB";
        this.CollectionName = "DotNetSKTestCollection";
        this.MemoryStore = new AzureCosmosDBMongoVCoreMemoryStore(
            connectionString,
            this.DatabaseName,
            this.indexName,
            this.kind,
            this.numLists,
            this.similarity,
            this.dimensions,
            this.numberOfConnections,
            this.efConstruction,
            this.efSearch
            );    
    }

    public async Task InitializeAsync()
    {
        await this.MemoryStore.UpsertBatchAsync(this.CollectionName, DataHelper.VectorSearchTestRecords).ToListAsync();
    }

    public async Task DisposeAsync() 
    {
        this.MemoryStore.DeleteCollectionAsync(this.CollectionName);
        this.MemoryStore.Dispose();
    }

    private static string GetSetting(IConfigurationRoot configuration, string settingName)
    {
        var settingValue = configuration[$"AzureCosmosDB:{settingName}"];
        if (string.IsNullOrWhiteSpace(settingValue))
        {
            throw new ArgumentNullException($"{settingValue} string is not configured");
        }

        return settingValue;
    }
}