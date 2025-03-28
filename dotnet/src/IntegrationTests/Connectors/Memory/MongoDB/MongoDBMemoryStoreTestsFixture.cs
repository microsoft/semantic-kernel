// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Connectors.MongoDB;
using Microsoft.SemanticKernel.Memory;
using MongoDB.Driver;
using MongoDB.Driver.Core.Configuration;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.MongoDB;

[Obsolete("The IMemoryStore abstraction is being obsoleted")]
public class MongoDBMemoryStoreTestsFixture : IAsyncLifetime
{
#pragma warning disable CA1859 // Use concrete types when possible for improved performance
    private readonly IMongoClient _mongoClient = null!;
#pragma warning restore CA1859 // Use concrete types when possible for improved performance

    public string DatabaseTestName { get; }
    public string ListCollectionsDatabaseTestName { get; }
    public string VectorSearchCollectionName { get; }

    public MongoDBMemoryStore MemoryStore { get; }
    public MongoDBMemoryStore ListCollectionsMemoryStore { get; }
    public MongoDBMemoryStore VectorSearchMemoryStore { get; }

    public MongoDBMemoryStoreTestsFixture()
    {
        // Load configuration
        var configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .Build();

        var connectionString = GetSetting(configuration, "ConnectionString");
        var vectorSearchCollection = GetSetting(configuration, "VectorSearchCollection");

        var vectorSearchCollectionNamespace = CollectionNamespace.FromFullName(vectorSearchCollection);
        this.VectorSearchCollectionName = vectorSearchCollectionNamespace.CollectionName;

        var skVersion = typeof(IMemoryStore).Assembly?.GetName()?.Version?.ToString();
        var mongoClientSettings = MongoClientSettings.FromConnectionString(connectionString);
        mongoClientSettings.ApplicationName = GetRandomName();
        mongoClientSettings.LibraryInfo = new LibraryInfo("Microsoft Semantic Kernel", skVersion);

        this.DatabaseTestName = "dotnetMSKIntegrationTests1";
        this.ListCollectionsDatabaseTestName = "dotnetMSKIntegrationTests2";

        this._mongoClient = new MongoClient(mongoClientSettings);
        this.MemoryStore = new MongoDBMemoryStore(this._mongoClient, this.DatabaseTestName);
        this.VectorSearchMemoryStore = new MongoDBMemoryStore(this._mongoClient, vectorSearchCollectionNamespace.DatabaseNamespace.DatabaseName);
        this.ListCollectionsMemoryStore = new MongoDBMemoryStore(this._mongoClient, this.ListCollectionsDatabaseTestName);
    }

    public async Task InitializeAsync()
    {
        await this.VectorSearchMemoryStore.UpsertBatchAsync(this.VectorSearchCollectionName, DataHelper.VectorSearchTestRecords).ToListAsync();
    }

    public async Task DisposeAsync()
    {
        await this.DropAllCollectionsAsync(this.DatabaseTestName);
        await this.DropAllCollectionsAsync(this.ListCollectionsDatabaseTestName);

        this.MemoryStore.Dispose();
        this.VectorSearchMemoryStore.Dispose();
    }

    #region private ================================================================================

    private async Task DropAllCollectionsAsync(string databaseName)
    {
        var database = this._mongoClient.GetDatabase(databaseName);
        var allCollectionCursor = await database.ListCollectionNamesAsync();
        var allCollectionNames = await allCollectionCursor.ToListAsync();

        foreach (var collectionName in allCollectionNames)
        {
            await database.DropCollectionAsync(collectionName);
        }
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

    private static string GetRandomName() => $"test_{Guid.NewGuid():N}";

    #endregion
}
