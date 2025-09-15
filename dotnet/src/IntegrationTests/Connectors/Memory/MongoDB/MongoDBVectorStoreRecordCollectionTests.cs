// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.MongoDB;
using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;
using MongoDB.Driver;
using xRetry;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.MongoDB;

#pragma warning disable CS0618 // VectorSearchFilter is obsolete

[Collection("MongoDBVectorStoreCollection")]
public class MongoDBVectorStoreRecordCollectionTests(MongoDBVectorStoreFixture fixture)
{
    // If null, all tests will be enabled
    private const string? SkipReason = "The MongoDB container is intermittently timing out at startup time blocking prs, so these test should be run manually.";

    [RetryTheory(typeof(MongoCommandException), Skip = SkipReason)]
    [InlineData("sk-test-hotels", true)]
    [InlineData("nonexistentcollection", false)]
    public async Task CollectionExistsReturnsCollectionStateAsync(string collectionName, bool expectedExists)
    {
        // Arrange
        using var sut = new MongoCollection<string, MongoDBHotel>(fixture.MongoDatabase, collectionName);

        // Act
        var actual = await sut.CollectionExistsAsync();

        // Assert
        Assert.Equal(expectedExists, actual);
    }

    [RetryFact(typeof(MongoCommandException), Skip = SkipReason)]
    public async Task ItCanEnsureCollectionExistsAsync()
    {
        // Arrange
        var newCollection = Guid.NewGuid().ToString();
        using var sut = new MongoCollection<string, MongoDBHotel>(fixture.MongoDatabase, newCollection);

        // Act
        await sut.EnsureCollectionExistsAsync();

        // Assert
        Assert.True(await sut.CollectionExistsAsync());
        await sut.EnsureCollectionDeletedAsync();
    }

    [RetryTheory(typeof(MongoCommandException), Skip = SkipReason)]
    [InlineData(true, true)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(false, false)]
    public async Task ItCanCreateCollectionUpsertAndGetAsync(bool includeVectors, bool useRecordDefinition)
    {
        // Arrange
        const string HotelId = "55555555-5555-5555-5555-555555555555";

        var collectionNamePostfix = useRecordDefinition ? "with-definition" : "with-type";
        collectionNamePostfix += includeVectors ? "-with-vectors" : "-without-vectors";
        var collectionName = $"collection-{collectionNamePostfix}";

        var options = new MongoCollectionOptions
        {
            Definition = useRecordDefinition ? fixture.HotelVectorStoreRecordDefinition : null
        };

        using var sut = new MongoCollection<string, MongoDBHotel>(fixture.MongoDatabase, collectionName, options);

        var record = this.CreateTestHotel(HotelId);

        // Act
        await sut.EnsureCollectionExistsAsync();
        await sut.UpsertAsync(record);
        var getResult = await sut.GetAsync(HotelId, new() { IncludeVectors = includeVectors });

        // Assert
        Assert.True(await sut.CollectionExistsAsync());
        await sut.EnsureCollectionDeletedAsync();

        Assert.NotNull(getResult);

        Assert.Equal(record.HotelId, getResult.HotelId);
        Assert.Equal(record.HotelName, getResult.HotelName);
        Assert.Equal(record.HotelCode, getResult.HotelCode);
        Assert.Equal(record.HotelRating, getResult.HotelRating);
        Assert.Equal(record.ParkingIncluded, getResult.ParkingIncluded);
        Assert.Equal(record.Tags.ToArray(), getResult.Tags.ToArray());
        Assert.Equal(record.Description, getResult.Description);
        Assert.Equal(record.Timestamp.ToUniversalTime(), getResult.Timestamp.ToUniversalTime());

        if (includeVectors)
        {
            Assert.NotNull(getResult.DescriptionEmbedding);
            Assert.Equal(record.DescriptionEmbedding!.Value.ToArray(), getResult.DescriptionEmbedding.Value.ToArray());
        }
        else
        {
            Assert.Null(getResult.DescriptionEmbedding);
        }
    }

    [RetryFact(typeof(MongoCommandException), Skip = SkipReason)]
    public async Task ItCanDeleteCollectionAsync()
    {
        // Arrange
        const string TempCollectionName = "temp-test";
        await fixture.MongoDatabase.CreateCollectionAsync(TempCollectionName);

        using var sut = new MongoCollection<string, MongoDBHotel>(fixture.MongoDatabase, TempCollectionName);

        Assert.True(await sut.CollectionExistsAsync());

        // Act
        await sut.EnsureCollectionDeletedAsync();

        // Assert
        Assert.False(await sut.CollectionExistsAsync());
    }

    [RetryFact(typeof(MongoCommandException), Skip = SkipReason)]
    public async Task ItCanGetAndDeleteRecordAsync()
    {
        // Arrange
        const string HotelId = "55555555-5555-5555-5555-555555555555";
        using var sut = new MongoCollection<string, MongoDBHotel>(fixture.MongoDatabase, fixture.TestCollection);

        var record = this.CreateTestHotel(HotelId);

        await sut.UpsertAsync(record);
        var getResult = await sut.GetAsync(HotelId);

        Assert.NotNull(getResult);

        // Act
        await sut.DeleteAsync(HotelId);

        getResult = await sut.GetAsync(HotelId);

        // Assert
        Assert.Null(getResult);
    }

    [RetryFact(typeof(MongoCommandException), Skip = SkipReason)]
    public async Task ItCanGetAndDeleteBatchAsync()
    {
        // Arrange
        const string HotelId1 = "11111111-1111-1111-1111-111111111111";
        const string HotelId2 = "22222222-2222-2222-2222-222222222222";
        const string HotelId3 = "33333333-3333-3333-3333-333333333333";

        using var sut = new MongoCollection<string, MongoDBHotel>(fixture.MongoDatabase, fixture.TestCollection);

        var record1 = this.CreateTestHotel(HotelId1);
        var record2 = this.CreateTestHotel(HotelId2);
        var record3 = this.CreateTestHotel(HotelId3);

        await sut.UpsertAsync([record1, record2, record3]);

        var getResults = await sut.GetAsync([HotelId1, HotelId2, HotelId3]).ToListAsync();

        Assert.NotNull(getResults.First(l => l.HotelId == HotelId1));
        Assert.NotNull(getResults.First(l => l.HotelId == HotelId2));
        Assert.NotNull(getResults.First(l => l.HotelId == HotelId3));

        // Act
        await sut.DeleteAsync([HotelId1, HotelId2, HotelId3]);

        getResults = await sut.GetAsync([HotelId1, HotelId2, HotelId3]).ToListAsync();

        // Assert
        Assert.Empty(getResults);
    }

    [RetryFact(typeof(MongoCommandException), Skip = SkipReason)]
    public async Task ItCanUpsertRecordAsync()
    {
        // Arrange
        const string HotelId = "55555555-5555-5555-5555-555555555555";
        using var sut = new MongoCollection<string, MongoDBHotel>(fixture.MongoDatabase, fixture.TestCollection);

        var record = this.CreateTestHotel(HotelId);

        await sut.UpsertAsync(record);
        var getResult = await sut.GetAsync(HotelId);

        Assert.NotNull(getResult);

        // Act
        record.HotelName = "Updated name";
        record.HotelRating = 10;

        await sut.UpsertAsync(record);
        getResult = await sut.GetAsync(HotelId);

        // Assert
        Assert.NotNull(getResult);
        Assert.Equal("Updated name", getResult.HotelName);
        Assert.Equal(10, getResult.HotelRating);
    }

    [RetryFact(typeof(MongoCommandException), Skip = SkipReason)]
    public async Task UpsertWithModelWorksCorrectlyAsync()
    {
        // Arrange
        var definition = new VectorStoreCollectionDefinition
        {
            Properties = new List<VectorStoreProperty>
            {
                new VectorStoreKeyProperty("Id", typeof(string)),
                new VectorStoreDataProperty("HotelName", typeof(string))
            }
        };

        var model = new TestModel { Id = "key", HotelName = "Test Name" };

        using var sut = new MongoCollection<string, TestModel>(
            fixture.MongoDatabase,
            fixture.TestCollection,
            new() { Definition = definition });

        // Act
        await sut.UpsertAsync(model);
        var getResult = await sut.GetAsync(model.Id);

        // Assert
        Assert.NotNull(getResult);
        Assert.Equal("key", getResult.Id);
        Assert.Equal("Test Name", getResult.HotelName);
    }

    [RetryFact(typeof(MongoCommandException), Skip = SkipReason)]
    public async Task UpsertWithVectorStoreModelWorksCorrectlyAsync()
    {
        // Arrange
        var model = new VectorStoreTestModel { HotelId = "key", HotelName = "Test Name" };

        using var sut = new MongoCollection<string, VectorStoreTestModel>(fixture.MongoDatabase, fixture.TestCollection);

        // Act
        await sut.UpsertAsync(model);
        var getResult = await sut.GetAsync(model.HotelId);

        // Assert
        Assert.NotNull(getResult);
        Assert.Equal("key", getResult.HotelId);
        Assert.Equal("Test Name", getResult.HotelName);
    }

    [RetryFact(typeof(MongoCommandException), Skip = SkipReason)]
    public async Task UpsertWithBsonModelWorksCorrectlyAsync()
    {
        // Arrange
        var definition = new VectorStoreCollectionDefinition
        {
            Properties = new List<VectorStoreProperty>
            {
                new VectorStoreKeyProperty("Id", typeof(string)),
                new VectorStoreDataProperty("HotelName", typeof(string))
            }
        };

        var model = new BsonTestModel { Id = "key", HotelName = "Test Name" };

        using var sut = new MongoCollection<string, BsonTestModel>(
            fixture.MongoDatabase,
            fixture.TestCollection,
            new() { Definition = definition });

        // Act
        await sut.UpsertAsync(model);
        var getResult = await sut.GetAsync(model.Id);

        // Assert
        Assert.NotNull(getResult);
        Assert.Equal("key", getResult.Id);
        Assert.Equal("Test Name", getResult.HotelName);
    }

    [RetryFact(typeof(MongoCommandException), Skip = SkipReason)]
    public async Task UpsertWithBsonVectorStoreModelWorksCorrectlyAsync()
    {
        // Arrange
        var model = new BsonVectorStoreTestModel { HotelId = "key", HotelName = "Test Name" };

        using var sut = new MongoCollection<string, BsonVectorStoreTestModel>(fixture.MongoDatabase, fixture.TestCollection);

        // Act
        await sut.UpsertAsync(model);
        var getResult = await sut.GetAsync(model.HotelId);

        // Assert
        Assert.NotNull(getResult);
        Assert.Equal("key", getResult.HotelId);
        Assert.Equal("Test Name", getResult.HotelName);
    }

    [RetryFact(typeof(MongoCommandException), Skip = SkipReason)]
    public async Task UpsertWithBsonVectorStoreWithNameModelWorksCorrectlyAsync()
    {
        // Arrange
        var model = new BsonVectorStoreWithNameTestModel { Id = "key", HotelName = "Test Name" };

        using var sut = new MongoCollection<string, BsonVectorStoreWithNameTestModel>(fixture.MongoDatabase, fixture.TestCollection);

        // Act
        await sut.UpsertAsync(model);
        var getResult = await sut.GetAsync(model.Id);

        // Assert
        Assert.NotNull(getResult);
        Assert.Equal("key", getResult.Id);
        Assert.Equal("Test Name", getResult.HotelName);
    }

    [RetryFact(typeof(MongoCommandException), Skip = SkipReason)]
    public async Task SearchReturnsValidResultsByDefaultAsync()
    {
        // Arrange
        var hotel1 = this.CreateTestHotel(hotelId: "key1", embedding: new[] { 30f, 31f, 32f, 33f });
        var hotel2 = this.CreateTestHotel(hotelId: "key2", embedding: new[] { 31f, 32f, 33f, 34f });
        var hotel3 = this.CreateTestHotel(hotelId: "key3", embedding: new[] { 20f, 20f, 20f, 20f });
        var hotel4 = this.CreateTestHotel(hotelId: "key4", embedding: new[] { -1000f, -1000f, -1000f, -1000f });

        using var sut = new MongoCollection<string, MongoDBHotel>(fixture.MongoDatabase, "TestVectorizedSearch");

        await sut.EnsureCollectionExistsAsync();

        await sut.UpsertAsync([hotel4, hotel2, hotel3, hotel1]);

        // Act
        var searchResults = await sut.SearchAsync(new ReadOnlyMemory<float>([30f, 31f, 32f, 33f]), top: 3).ToListAsync();

        // Assert
        var ids = searchResults.Select(l => l.Record.HotelId).ToList();

        Assert.Equal("key1", ids[0]);
        Assert.Equal("key2", ids[1]);
        Assert.Equal("key3", ids[2]);

        Assert.DoesNotContain("key4", ids);

        Assert.Equal(1, searchResults.First(l => l.Record.HotelId == "key1").Score);
    }

    [RetryFact(typeof(MongoCommandException), Skip = SkipReason)]
    public async Task SearchReturnsValidResultsWithOffsetAsync()
    {
        // Arrange
        var hotel1 = this.CreateTestHotel(hotelId: "key1", embedding: new[] { 30f, 31f, 32f, 33f });
        var hotel2 = this.CreateTestHotel(hotelId: "key2", embedding: new[] { 31f, 32f, 33f, 34f });
        var hotel3 = this.CreateTestHotel(hotelId: "key3", embedding: new[] { 20f, 20f, 20f, 20f });
        var hotel4 = this.CreateTestHotel(hotelId: "key4", embedding: new[] { -1000f, -1000f, -1000f, -1000f });

        using var sut = new MongoCollection<string, MongoDBHotel>(fixture.MongoDatabase, "TestVectorizedSearchWithOffset");

        await sut.EnsureCollectionExistsAsync();

        await sut.UpsertAsync([hotel4, hotel2, hotel3, hotel1]);

        // Act
        var searchResults = await sut.SearchAsync(new ReadOnlyMemory<float>([30f, 31f, 32f, 33f]), top: 2, new()
        {
            Skip = 2
        }).ToListAsync();

        // Assert
        var ids = searchResults.Select(l => l.Record.HotelId).ToList();

        Assert.Equal("key3", ids[0]);
        Assert.Equal("key4", ids[1]);

        Assert.DoesNotContain("key1", ids);
        Assert.DoesNotContain("key2", ids);
    }

    [RetryFact(typeof(MongoCommandException), Skip = SkipReason)]
    public async Task SearchReturnsValidResultsWithFilterAsync()
    {
        // Arrange
        var hotel1 = this.CreateTestHotel(hotelId: "key1", embedding: new[] { 30f, 31f, 32f, 33f });
        var hotel2 = this.CreateTestHotel(hotelId: "key2", embedding: new[] { 31f, 32f, 33f, 34f });
        var hotel3 = this.CreateTestHotel(hotelId: "key3", embedding: new[] { 20f, 20f, 20f, 20f });
        var hotel4 = this.CreateTestHotel(hotelId: "key4", embedding: new[] { -1000f, -1000f, -1000f, -1000f });

        using var sut = new MongoCollection<string, MongoDBHotel>(fixture.MongoDatabase, "TestVectorizedSearchWithFilter");

        await sut.EnsureCollectionExistsAsync();

        await sut.UpsertAsync([hotel4, hotel2, hotel3, hotel1]);

        // Act
        var searchResults = await sut.SearchAsync(new ReadOnlyMemory<float>([30f, 31f, 32f, 33f]), top: 3, new()
        {
            OldFilter = new VectorSearchFilter().EqualTo(nameof(MongoDBHotel.HotelName), "My Hotel key2")
        }).ToListAsync();

        // Assert
        var ids = searchResults.Select(l => l.Record.HotelId).ToList();

        Assert.Equal("key2", ids[0]);

        Assert.DoesNotContain("key1", ids);
        Assert.DoesNotContain("key3", ids);
        Assert.DoesNotContain("key4", ids);
    }

    [RetryFact(typeof(MongoCommandException), Skip = SkipReason)]
    public async Task ItCanUpsertAndRetrieveUsingTheDynamicMapperAsync()
    {
        // Arrange
        var options = new MongoCollectionOptions
        {
            Definition = fixture.HotelVectorStoreRecordDefinition
        };

        using var sut = new MongoDynamicCollection(fixture.MongoDatabase, fixture.TestCollection, options);

        // Act
        await sut.UpsertAsync(new Dictionary<string, object?>
        {
            ["HotelId"] = "DynamicMapper-1",

            ["HotelName"] = "Dynamic Mapper Hotel",
            ["Description"] = "This is a dynamic mapper hotel",
            ["Tags"] = new string[] { "dynamic" },
            ["ParkingIncluded"] = false,
            ["Timestamp"] = new DateTime(1970, 1, 18, 0, 0, 0).ToUniversalTime(),
            ["HotelRating"] = 3.6f,

            ["DescriptionEmbedding"] = new ReadOnlyMemory<float>([30f, 31f, 32f, 33f])
        });

        var localGetResult = await sut.GetAsync("DynamicMapper-1", new RecordRetrievalOptions { IncludeVectors = true });

        // Assert
        Assert.NotNull(localGetResult);
        Assert.Equal("Dynamic Mapper Hotel", localGetResult["HotelName"]);
        Assert.Equal("This is a dynamic mapper hotel", localGetResult["Description"]);
        Assert.Equal(new[] { "dynamic" }, localGetResult["Tags"]);
        Assert.False((bool?)localGetResult["ParkingIncluded"]);
        Assert.Equal(new DateTime(1970, 1, 18, 0, 0, 0).ToUniversalTime(), localGetResult["Timestamp"]);
        Assert.Equal(3.6f, localGetResult["HotelRating"]);
        Assert.Equal(new[] { 30f, 31f, 32f, 33f }, ((ReadOnlyMemory<float>)localGetResult["DescriptionEmbedding"]!).ToArray());
    }

    #region private

    private MongoDBHotel CreateTestHotel(string hotelId, ReadOnlyMemory<float>? embedding = null)
    {
        return new MongoDBHotel
        {
            HotelId = hotelId,
            HotelName = $"My Hotel {hotelId}",
            HotelCode = 42,
            HotelRating = 4.5f,
            ParkingIncluded = true,
            Tags = { "t1", "t2" },
            Description = "This is a great hotel.",
            Timestamp = new DateTime(2024, 09, 23, 15, 32, 33),
            DescriptionEmbedding = embedding ?? new[] { 30f, 31f, 32f, 33f },
        };
    }

    private sealed class TestModel
    {
        public string? Id { get; set; }

        public string? HotelName { get; set; }
    }

    private sealed class VectorStoreTestModel
    {
        [VectorStoreKey]
        public string? HotelId { get; set; }

        [VectorStoreData(StorageName = "hotel_name")]
        public string? HotelName { get; set; }
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

    #endregion
}
