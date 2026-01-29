// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.MongoDB;
using MongoDB.Bson.Serialization.Attributes;
using MongoDB.ConformanceTests.Support;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace MongoDB.ConformanceTests;

public sealed class MongoBsonMappingTests(MongoBsonMappingTests.Fixture fixture)
    : IClassFixture<MongoBsonMappingTests.Fixture>
{
    [ConditionalFact]
    public async Task Upsert_with_bson_model_works()
    {
        var store = (MongoTestStore)fixture.TestStore;
        var collectionName = fixture.TestStore.AdjustCollectionName("BsonModel");

        var definition = new VectorStoreCollectionDefinition
        {
            Properties =
            [
                new VectorStoreKeyProperty(nameof(BsonTestModel.Id), typeof(string)),
                new VectorStoreDataProperty(nameof(BsonTestModel.HotelName), typeof(string))
            ]
        };

        var model = new BsonTestModel { Id = "key", HotelName = "Test Name" };

        using var collection = new MongoCollection<string, BsonTestModel>(
            store.Database,
            collectionName,
            new() { Definition = definition });

        await collection.EnsureCollectionExistsAsync();

        try
        {
            await collection.UpsertAsync(model);
            var getResult = await collection.GetAsync(model.Id!);

            Assert.NotNull(getResult);
            Assert.Equal("key", getResult!.Id);
            Assert.Equal("Test Name", getResult.HotelName);
        }
        finally
        {
            await collection.EnsureCollectionDeletedAsync();
        }
    }

    [ConditionalFact]
    public async Task Upsert_with_bson_vector_store_model_works()
    {
        var store = (MongoTestStore)fixture.TestStore;
        var collectionName = fixture.TestStore.AdjustCollectionName("BsonVectorStoreModel");

        var model = new BsonVectorStoreTestModel { HotelId = "key", HotelName = "Test Name" };

        using var collection = new MongoCollection<string, BsonVectorStoreTestModel>(store.Database, collectionName);

        await collection.EnsureCollectionExistsAsync();

        try
        {
            await collection.UpsertAsync(model);
            var getResult = await collection.GetAsync(model.HotelId!);

            Assert.NotNull(getResult);
            Assert.Equal("key", getResult!.HotelId);
            Assert.Equal("Test Name", getResult.HotelName);
        }
        finally
        {
            await collection.EnsureCollectionDeletedAsync();
        }
    }

    [ConditionalFact]
    public async Task Upsert_with_bson_vector_store_with_name_model_works()
    {
        var store = (MongoTestStore)fixture.TestStore;
        var collectionName = fixture.TestStore.AdjustCollectionName("BsonVectorStoreWithNameModel");

        var model = new BsonVectorStoreWithNameTestModel { Id = "key", HotelName = "Test Name" };

        using var collection = new MongoCollection<string, BsonVectorStoreWithNameTestModel>(store.Database, collectionName);

        await collection.EnsureCollectionExistsAsync();

        try
        {
            await collection.UpsertAsync(model);
            var getResult = await collection.GetAsync(model.Id!);

            Assert.NotNull(getResult);
            Assert.Equal("key", getResult!.Id);
            Assert.Equal("Test Name", getResult.HotelName);
        }
        finally
        {
            await collection.EnsureCollectionDeletedAsync();
        }
    }

    public sealed class Fixture : VectorStoreFixture
    {
        public override TestStore TestStore => MongoTestStore.Instance;
    }

    private sealed class BsonTestModel
    {
        [BsonId]
        public string? Id { get; set; }

        [BsonElement("hotel_name")]
        public string? HotelName { get; set; }
    }

    private sealed class BsonVectorStoreTestModel
    {
        [BsonId]
        [VectorStoreKey]
        public string? HotelId { get; set; }

        [BsonElement("hotel_name")]
        [VectorStoreData]
        public string? HotelName { get; set; }
    }

    private sealed class BsonVectorStoreWithNameTestModel
    {
        [BsonId]
        [VectorStoreKey]
        public string? Id { get; set; }

        [BsonElement("bson_hotel_name")]
        [VectorStoreData(StorageName = "storage_hotel_name")]
        public string? HotelName { get; set; }
    }
}
