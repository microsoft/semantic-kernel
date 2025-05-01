// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using MongoDB.Driver;
using Testcontainers.MongoDb;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.MongoDB;

#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.

public class MongoDBVectorStoreFixture : IAsyncLifetime
{
    private readonly MongoDbContainer _container = new MongoDbBuilder()
        .WithImage("mongodb/mongodb-atlas-local:7.0.6")
        .Build();

    private readonly List<string> _testCollections = ["sk-test-hotels", "sk-test-contacts", "sk-test-addresses"];

    /// <summary>Main test collection for tests.</summary>
    public string TestCollection => this._testCollections[0];

    /// <summary><see cref="IMongoDatabase"/> that can be used to manage the collections in MongoDB.</summary>
    public IMongoDatabase MongoDatabase { get; private set; }

    /// <summary>Gets the manually created vector store record definition for MongoDB test model.</summary>
    public VectorStoreRecordDefinition HotelVectorStoreRecordDefinition { get; private set; }

    public async Task InitializeAsync()
    {
        await this._container.StartAsync();

        var mongoClient = new MongoClient(new MongoClientSettings
        {
            Server = new MongoServerAddress(this._container.Hostname, this._container.GetMappedPublicPort(MongoDbBuilder.MongoDbPort)),
            DirectConnection = true,
        });

        this.MongoDatabase = mongoClient.GetDatabase("test");

        this.HotelVectorStoreRecordDefinition = new()
        {
            Properties =
            [
                new VectorStoreRecordKeyProperty("HotelId", typeof(string)),
                new VectorStoreRecordDataProperty("HotelName", typeof(string)),
                new VectorStoreRecordDataProperty("HotelCode", typeof(int)),
                new VectorStoreRecordDataProperty("ParkingIncluded", typeof(bool)) { StoragePropertyName = "parking_is_included" },
                new VectorStoreRecordDataProperty("HotelRating", typeof(float)),
                new VectorStoreRecordDataProperty("Tags", typeof(List<string>)),
                new VectorStoreRecordDataProperty("Timestamp", typeof(DateTime)),
                new VectorStoreRecordDataProperty("Description", typeof(string)),
                new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?), 4) { IndexKind = IndexKind.IvfFlat, DistanceFunction = DistanceFunction.CosineSimilarity }
            ]
        };

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

        await this._container.StopAsync();
    }
}
