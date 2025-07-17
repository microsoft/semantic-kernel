// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.VectorData;
using MongoDB.Driver;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.CosmosMongoDB;

public class CosmosMongoVectorStoreFixture : IAsyncLifetime
{
    private readonly List<string> _testCollections = ["sk-test-hotels", "sk-test-contacts", "sk-test-addresses"];

    /// <summary>Main test collection for tests.</summary>
    public string TestCollection => this._testCollections[0];

    /// <summary><see cref="IMongoDatabase"/> that can be used to manage the collections in Azure CosmosDB MongoDB.</summary>
    public IMongoDatabase MongoDatabase { get; }

    /// <summary>Gets the manually created vector store record definition for Azure CosmosDB MongoDB test model.</summary>
    public VectorStoreCollectionDefinition HotelVectorStoreRecordDefinition { get; private set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="CosmosMongoVectorStoreFixture"/> class.
    /// </summary>
    public CosmosMongoVectorStoreFixture()
    {
        var configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(
                path: "testsettings.development.json",
                optional: true,
                reloadOnChange: true
            )
            .AddEnvironmentVariables()
            .AddUserSecrets<CosmosMongoVectorStoreFixture>()
            .Build();

        var connectionString = GetConnectionString(configuration);
        var client = new MongoClient(connectionString);

        this.MongoDatabase = client.GetDatabase("test");

        this.HotelVectorStoreRecordDefinition = new()
        {
            Properties =
            [
                new VectorStoreKeyProperty("HotelId", typeof(string)),
                new VectorStoreDataProperty("HotelName", typeof(string)),
                new VectorStoreDataProperty("HotelCode", typeof(int)),
                new VectorStoreDataProperty("ParkingIncluded", typeof(bool)) { StorageName = "parking_is_included" },
                new VectorStoreDataProperty("HotelRating", typeof(float)),
                new VectorStoreDataProperty("Tags", typeof(List<string>)),
                new VectorStoreDataProperty("Timestamp", typeof(DateTime)),
                new VectorStoreDataProperty("Description", typeof(string)),
                new VectorStoreVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?), 4) { IndexKind = IndexKind.IvfFlat, DistanceFunction = DistanceFunction.CosineDistance }
            ]
        };
    }

    public async Task InitializeAsync()
    {
        foreach (var collection in this._testCollections)
        {
            await this.MongoDatabase.CreateCollectionAsync(collection);
        }
    }

    public async Task DisposeAsync()
    {
        var cursor = await this.MongoDatabase.ListCollectionNamesAsync();

        while (await cursor.MoveNextAsync().ConfigureAwait(false))
        {
            foreach (var collection in cursor.Current)
            {
                await this.MongoDatabase.DropCollectionAsync(collection);
            }
        }
    }

    #region private

    private static string GetConnectionString(IConfigurationRoot configuration)
    {
        var settingValue = configuration["CosmosMongo:ConnectionString"];
        if (string.IsNullOrWhiteSpace(settingValue))
        {
            throw new ArgumentNullException($"{settingValue} string is not configured");
        }

        return settingValue;
    }

    #endregion
}
