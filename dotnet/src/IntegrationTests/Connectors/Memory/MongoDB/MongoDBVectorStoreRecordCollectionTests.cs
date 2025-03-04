// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.MongoDB;
using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.MongoDB;

#pragma warning disable CS0618 // VectorSearchFilter is obsolete

[Collection("MongoDBVectorStoreCollection")]
public class MongoDBVectorStoreRecordCollectionTests(MongoDBVectorStoreFixture fixture)
{
    // If null, all tests will be enabled
    private const string? SkipReason = "The tests are for manual verification.";

    [Theory(Skip = SkipReason)]
    [InlineData("sk-test-hotels", true)]
    [InlineData("nonexistentcollection", false)]
    public async Task CollectionExistsReturnsCollectionStateAsync(string collectionName, bool expectedExists)
    {
        // Arrange
        var sut = new MongoDBVectorStoreRecordCollection<MongoDBHotel>(fixture.MongoDatabase, collectionName);

        // Act
        var actual = await sut.CollectionExistsAsync();

        // Assert
        Assert.Equal(expectedExists, actual);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanCreateCollectionAsync()
    {
        // Arrange
        var sut = new MongoDBVectorStoreRecordCollection<MongoDBHotel>(fixture.MongoDatabase, fixture.TestCollection);

        // Act
        await sut.CreateCollectionAsync();

        // Assert
        Assert.True(await sut.CollectionExistsAsync());
    }

    [Theory(Skip = SkipReason)]
    [InlineData(true, true)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(false, false)]
    public async Task ItCanCreateCollectionUpsertAndGetAsync(bool includeVectors, bool useRecordDefinition)
    {
        // Arrange
        const string HotelId = "55555555-5555-5555-5555-555555555555";

        var collectionNamePostfix = useRecordDefinition ? "with-definition" : "with-type";
        var collectionName = $"collection-{collectionNamePostfix}";

        var options = new MongoDBVectorStoreRecordCollectionOptions<MongoDBHotel>
        {
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.HotelVectorStoreRecordDefinition : null
        };

        var sut = new MongoDBVectorStoreRecordCollection<MongoDBHotel>(fixture.MongoDatabase, collectionName);

        var record = this.CreateTestHotel(HotelId);

        // Act
        await sut.CreateCollectionAsync();
        var upsertResult = await sut.UpsertAsync(record);
        var getResult = await sut.GetAsync(HotelId, new() { IncludeVectors = includeVectors });

        // Assert
        Assert.True(await sut.CollectionExistsAsync());
        await sut.DeleteCollectionAsync();

        Assert.Equal(HotelId, upsertResult);
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

    [Fact(Skip = SkipReason)]
    public async Task ItCanDeleteCollectionAsync()
    {
        // Arrange
        const string TempCollectionName = "temp-test";
        await fixture.MongoDatabase.CreateCollectionAsync(TempCollectionName);

        var sut = new MongoDBVectorStoreRecordCollection<MongoDBHotel>(fixture.MongoDatabase, TempCollectionName);

        Assert.True(await sut.CollectionExistsAsync());

        // Act
        await sut.DeleteCollectionAsync();

        // Assert
        Assert.False(await sut.CollectionExistsAsync());
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanGetAndDeleteRecordAsync()
    {
        // Arrange
        const string HotelId = "55555555-5555-5555-5555-555555555555";
        var sut = new MongoDBVectorStoreRecordCollection<MongoDBHotel>(fixture.MongoDatabase, fixture.TestCollection);

        var record = this.CreateTestHotel(HotelId);

        var upsertResult = await sut.UpsertAsync(record);
        var getResult = await sut.GetAsync(HotelId);

        Assert.Equal(HotelId, upsertResult);
        Assert.NotNull(getResult);

        // Act
        await sut.DeleteAsync(HotelId);

        getResult = await sut.GetAsync(HotelId);

        // Assert
        Assert.Null(getResult);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanGetAndDeleteBatchAsync()
    {
        // Arrange
        const string HotelId1 = "11111111-1111-1111-1111-111111111111";
        const string HotelId2 = "22222222-2222-2222-2222-222222222222";
        const string HotelId3 = "33333333-3333-3333-3333-333333333333";

        var sut = new MongoDBVectorStoreRecordCollection<MongoDBHotel>(fixture.MongoDatabase, fixture.TestCollection);

        var record1 = this.CreateTestHotel(HotelId1);
        var record2 = this.CreateTestHotel(HotelId2);
        var record3 = this.CreateTestHotel(HotelId3);

        var upsertResults = await sut.UpsertBatchAsync([record1, record2, record3]).ToListAsync();
        var getResults = await sut.GetBatchAsync([HotelId1, HotelId2, HotelId3]).ToListAsync();

        Assert.Equal([HotelId1, HotelId2, HotelId3], upsertResults);

        Assert.NotNull(getResults.First(l => l.HotelId == HotelId1));
        Assert.NotNull(getResults.First(l => l.HotelId == HotelId2));
        Assert.NotNull(getResults.First(l => l.HotelId == HotelId3));

        // Act
        await sut.DeleteBatchAsync([HotelId1, HotelId2, HotelId3]);

        getResults = await sut.GetBatchAsync([HotelId1, HotelId2, HotelId3]).ToListAsync();

        // Assert
        Assert.Empty(getResults);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanUpsertRecordAsync()
    {
        // Arrange
        const string HotelId = "55555555-5555-5555-5555-555555555555";
        var sut = new MongoDBVectorStoreRecordCollection<MongoDBHotel>(fixture.MongoDatabase, fixture.TestCollection);

        var record = this.CreateTestHotel(HotelId);

        var upsertResult = await sut.UpsertAsync(record);
        var getResult = await sut.GetAsync(HotelId);

        Assert.Equal(HotelId, upsertResult);
        Assert.NotNull(getResult);

        // Act
        record.HotelName = "Updated name";
        record.HotelRating = 10;

        upsertResult = await sut.UpsertAsync(record);
        getResult = await sut.GetAsync(HotelId);

        // Assert
        Assert.NotNull(getResult);
        Assert.Equal("Updated name", getResult.HotelName);
        Assert.Equal(10, getResult.HotelRating);
    }

    [Fact(Skip = SkipReason)]
    public async Task UpsertWithModelWorksCorrectlyAsync()
    {
        // Arrange
        var definition = new VectorStoreRecordDefinition
        {
            Properties = new List<VectorStoreRecordProperty>
            {
                new VectorStoreRecordKeyProperty("Id", typeof(string)),
                new VectorStoreRecordDataProperty("HotelName", typeof(string))
            }
        };

        var model = new TestModel { Id = "key", HotelName = "Test Name" };

        var sut = new MongoDBVectorStoreRecordCollection<TestModel>(
            fixture.MongoDatabase,
            fixture.TestCollection,
            new() { VectorStoreRecordDefinition = definition });

        // Act
        var upsertResult = await sut.UpsertAsync(model);
        var getResult = await sut.GetAsync(model.Id);

        // Assert
        Assert.Equal("key", upsertResult);

        Assert.NotNull(getResult);
        Assert.Equal("key", getResult.Id);
        Assert.Equal("Test Name", getResult.HotelName);
    }

    [Fact(Skip = SkipReason)]
    public async Task UpsertWithVectorStoreModelWorksCorrectlyAsync()
    {
        // Arrange
        var model = new VectorStoreTestModel { HotelId = "key", HotelName = "Test Name" };

        var sut = new MongoDBVectorStoreRecordCollection<VectorStoreTestModel>(fixture.MongoDatabase, fixture.TestCollection);

        // Act
        var upsertResult = await sut.UpsertAsync(model);
        var getResult = await sut.GetAsync(model.HotelId);

        // Assert
        Assert.Equal("key", upsertResult);

        Assert.NotNull(getResult);
        Assert.Equal("key", getResult.HotelId);
        Assert.Equal("Test Name", getResult.HotelName);
    }

    [Fact(Skip = SkipReason)]
    public async Task UpsertWithBsonModelWorksCorrectlyAsync()
    {
        // Arrange
        var definition = new VectorStoreRecordDefinition
        {
            Properties = new List<VectorStoreRecordProperty>
            {
                new VectorStoreRecordKeyProperty("Id", typeof(string)),
                new VectorStoreRecordDataProperty("HotelName", typeof(string))
            }
        };

        var model = new BsonTestModel { Id = "key", HotelName = "Test Name" };

        var sut = new MongoDBVectorStoreRecordCollection<BsonTestModel>(
            fixture.MongoDatabase,
            fixture.TestCollection,
            new() { VectorStoreRecordDefinition = definition });

        // Act
        var upsertResult = await sut.UpsertAsync(model);
        var getResult = await sut.GetAsync(model.Id);

        // Assert
        Assert.Equal("key", upsertResult);

        Assert.NotNull(getResult);
        Assert.Equal("key", getResult.Id);
        Assert.Equal("Test Name", getResult.HotelName);
    }

    [Fact(Skip = SkipReason)]
    public async Task UpsertWithBsonVectorStoreModelWorksCorrectlyAsync()
    {
        // Arrange
        var model = new BsonVectorStoreTestModel { HotelId = "key", HotelName = "Test Name" };

        var sut = new MongoDBVectorStoreRecordCollection<BsonVectorStoreTestModel>(fixture.MongoDatabase, fixture.TestCollection);

        // Act
        var upsertResult = await sut.UpsertAsync(model);
        var getResult = await sut.GetAsync(model.HotelId);

        // Assert
        Assert.Equal("key", upsertResult);

        Assert.NotNull(getResult);
        Assert.Equal("key", getResult.HotelId);
        Assert.Equal("Test Name", getResult.HotelName);
    }

    [Fact(Skip = SkipReason)]
    public async Task UpsertWithBsonVectorStoreWithNameModelWorksCorrectlyAsync()
    {
        // Arrange
        var model = new BsonVectorStoreWithNameTestModel { Id = "key", HotelName = "Test Name" };

        var sut = new MongoDBVectorStoreRecordCollection<BsonVectorStoreWithNameTestModel>(fixture.MongoDatabase, fixture.TestCollection);

        // Act
        var upsertResult = await sut.UpsertAsync(model);
        var getResult = await sut.GetAsync(model.Id);

        // Assert
        Assert.Equal("key", upsertResult);

        Assert.NotNull(getResult);
        Assert.Equal("key", getResult.Id);
        Assert.Equal("Test Name", getResult.HotelName);
    }

    [Fact(Skip = SkipReason)]
    public async Task VectorizedSearchReturnsValidResultsByDefaultAsync()
    {
        // Arrange
        var hotel1 = this.CreateTestHotel(hotelId: "key1", embedding: new[] { 30f, 31f, 32f, 33f });
        var hotel2 = this.CreateTestHotel(hotelId: "key2", embedding: new[] { 31f, 32f, 33f, 34f });
        var hotel3 = this.CreateTestHotel(hotelId: "key3", embedding: new[] { 20f, 20f, 20f, 20f });
        var hotel4 = this.CreateTestHotel(hotelId: "key4", embedding: new[] { -1000f, -1000f, -1000f, -1000f });

        var sut = new MongoDBVectorStoreRecordCollection<MongoDBHotel>(fixture.MongoDatabase, "TestVectorizedSearch");

        await sut.CreateCollectionIfNotExistsAsync();

        await sut.UpsertBatchAsync([hotel4, hotel2, hotel3, hotel1]).ToListAsync();

        // Act
        var actual = await sut.VectorizedSearchAsync(new ReadOnlyMemory<float>([30f, 31f, 32f, 33f]));

        // Assert
        var searchResults = await actual.Results.ToListAsync();
        var ids = searchResults.Select(l => l.Record.HotelId).ToList();

        Assert.Equal("key1", ids[0]);
        Assert.Equal("key2", ids[1]);
        Assert.Equal("key3", ids[2]);

        Assert.DoesNotContain("key4", ids);

        Assert.Equal(1, searchResults.First(l => l.Record.HotelId == "key1").Score);
    }

    [Fact(Skip = SkipReason)]
    public async Task VectorizedSearchReturnsValidResultsWithOffsetAsync()
    {
        // Arrange
        var hotel1 = this.CreateTestHotel(hotelId: "key1", embedding: new[] { 30f, 31f, 32f, 33f });
        var hotel2 = this.CreateTestHotel(hotelId: "key2", embedding: new[] { 31f, 32f, 33f, 34f });
        var hotel3 = this.CreateTestHotel(hotelId: "key3", embedding: new[] { 20f, 20f, 20f, 20f });
        var hotel4 = this.CreateTestHotel(hotelId: "key4", embedding: new[] { -1000f, -1000f, -1000f, -1000f });

        var sut = new MongoDBVectorStoreRecordCollection<MongoDBHotel>(fixture.MongoDatabase, "TestVectorizedSearchWithOffset");

        await sut.CreateCollectionIfNotExistsAsync();

        await sut.UpsertBatchAsync([hotel4, hotel2, hotel3, hotel1]).ToListAsync();

        // Act
        var actual = await sut.VectorizedSearchAsync(new ReadOnlyMemory<float>([30f, 31f, 32f, 33f]), new()
        {
            Top = 2,
            Skip = 2
        });

        // Assert
        var searchResults = await actual.Results.ToListAsync();
        var ids = searchResults.Select(l => l.Record.HotelId).ToList();

        Assert.Equal("key3", ids[0]);
        Assert.Equal("key4", ids[1]);

        Assert.DoesNotContain("key1", ids);
        Assert.DoesNotContain("key2", ids);
    }

    [Fact(Skip = SkipReason)]
    public async Task VectorizedSearchReturnsValidResultsWithFilterAsync()
    {
        // Arrange
        var hotel1 = this.CreateTestHotel(hotelId: "key1", embedding: new[] { 30f, 31f, 32f, 33f });
        var hotel2 = this.CreateTestHotel(hotelId: "key2", embedding: new[] { 31f, 32f, 33f, 34f });
        var hotel3 = this.CreateTestHotel(hotelId: "key3", embedding: new[] { 20f, 20f, 20f, 20f });
        var hotel4 = this.CreateTestHotel(hotelId: "key4", embedding: new[] { -1000f, -1000f, -1000f, -1000f });

        var sut = new MongoDBVectorStoreRecordCollection<MongoDBHotel>(fixture.MongoDatabase, "TestVectorizedSearchWithOffset");

        await sut.CreateCollectionIfNotExistsAsync();

        await sut.UpsertBatchAsync([hotel4, hotel2, hotel3, hotel1]).ToListAsync();

        // Act
        var actual = await sut.VectorizedSearchAsync(new ReadOnlyMemory<float>([30f, 31f, 32f, 33f]), new()
        {
            OldFilter = new VectorSearchFilter().EqualTo(nameof(MongoDBHotel.HotelName), "My Hotel key2")
        });

        // Assert
        var searchResults = await actual.Results.ToListAsync();
        var ids = searchResults.Select(l => l.Record.HotelId).ToList();

        Assert.Equal("key2", ids[0]);

        Assert.DoesNotContain("key1", ids);
        Assert.DoesNotContain("key3", ids);
        Assert.DoesNotContain("key4", ids);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanUpsertAndRetrieveUsingTheGenericMapperAsync()
    {
        // Arrange
        var options = new MongoDBVectorStoreRecordCollectionOptions<VectorStoreGenericDataModel<string>>
        {
            VectorStoreRecordDefinition = fixture.HotelVectorStoreRecordDefinition
        };

        var sut = new MongoDBVectorStoreRecordCollection<VectorStoreGenericDataModel<string>>(fixture.MongoDatabase, fixture.TestCollection, options);

        // Act
        var upsertResult = await sut.UpsertAsync(new VectorStoreGenericDataModel<string>("GenericMapper-1")
        {
            Data =
            {
                { "HotelName", "Generic Mapper Hotel" },
                { "Description", "This is a generic mapper hotel" },
                { "Tags", new string[] { "generic" } },
                { "ParkingIncluded", false },
                { "Timestamp", new DateTime(1970, 1, 18, 0, 0, 0).ToUniversalTime() },
                { "HotelRating", 3.6f }
            },
            Vectors =
            {
                { "DescriptionEmbedding", new ReadOnlyMemory<float>([30f, 31f, 32f, 33f]) }
            }
        });

        var localGetResult = await sut.GetAsync("GenericMapper-1", new GetRecordOptions { IncludeVectors = true });

        // Assert
        Assert.NotNull(upsertResult);
        Assert.Equal("GenericMapper-1", upsertResult);

        Assert.NotNull(localGetResult);
        Assert.Equal("Generic Mapper Hotel", localGetResult.Data["HotelName"]);
        Assert.Equal("This is a generic mapper hotel", localGetResult.Data["Description"]);
        Assert.Equal(new[] { "generic" }, localGetResult.Data["Tags"]);
        Assert.False((bool?)localGetResult.Data["ParkingIncluded"]);
        Assert.Equal(new DateTime(1970, 1, 18, 0, 0, 0).ToUniversalTime(), localGetResult.Data["Timestamp"]);
        Assert.Equal(3.6f, localGetResult.Data["HotelRating"]);
        Assert.Equal(new[] { 30f, 31f, 32f, 33f }, ((ReadOnlyMemory<float>)localGetResult.Vectors["DescriptionEmbedding"]!).ToArray());
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
        [VectorStoreRecordKey]
        public string? HotelId { get; set; }

        [VectorStoreRecordData(StoragePropertyName = "hotel_name")]
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
        [VectorStoreRecordKey]
        public string? HotelId { get; set; }

        [BsonElement("hotel_name")]
        [VectorStoreRecordData]
        public string? HotelName { get; set; }
    }

    private sealed class BsonVectorStoreWithNameTestModel
    {
        [BsonId]
        [VectorStoreRecordKey]
        public string? Id { get; set; }

        [BsonElement("bson_hotel_name")]
        [VectorStoreRecordData(StoragePropertyName = "storage_hotel_name")]
        public string? HotelName { get; set; }
    }

    #endregion
}
