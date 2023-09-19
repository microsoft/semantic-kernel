// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Connectors.Memory.MongoDB;
using Microsoft.SemanticKernel.Memory;
using MongoDB.Driver;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.MongoDB;

public class MongoDBMemoryStoreTestsFixture : IAsyncLifetime
{
    private readonly IMongoClient _mongoClient = null!;

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

        var mongoClientSettings = MongoClientSettings.FromConnectionString(connectionString);
        mongoClientSettings.ApplicationName = GetRandomName();

        this.DatabaseTestName = GetRandomName();
        this.ListCollectionsDatabaseTestName = GetRandomName();

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
        await this._mongoClient.DropDatabaseAsync(this.DatabaseTestName);
        await this._mongoClient.DropDatabaseAsync(this.ListCollectionsDatabaseTestName);

        this.MemoryStore.Dispose();
        this.VectorSearchMemoryStore.Dispose();
    }

    #region private ================================================================================

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

    private static MemoryRecord[] CreateBatchRecords(int count) =>
        Enumerable
        .Range(0, count)
        .Select(i => MemoryRecord.LocalRecord(
            id: $"test_{i}",
            text: $"text_{i}",
            description: $"description_{i}",
            embedding: new[] { 1, (float)Math.Cos(Math.PI * i / count), (float)Math.Sin(Math.PI * i / count) }))
        .ToArray();

    #endregion
}
