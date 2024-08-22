// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;
using Microsoft.SemanticKernel.Data;
using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;
using Xunit;
using static SemanticKernel.IntegrationTests.Connectors.AzureCosmosDBMongoDB.AzureCosmosDBMongoDBVectorStoreFixture;

namespace SemanticKernel.IntegrationTests.Connectors.AzureCosmosDBMongoDB;

[Collection("AzureCosmosDBMongoDBVectorStoreCollection")]
public class AzureCosmosDBMongoDBVectorStoreRecordCollectionTests(AzureCosmosDBMongoDBVectorStoreFixture fixture)
{
    private const string? SkipReason = "Azure CosmosDB MongoDB cluster is required";

    [Theory(Skip = SkipReason)]
    [InlineData("sk-test-hotels", true)]
    [InlineData("nonexistentcollection", false)]
    public async Task CollectionExistsReturnsCollectionStateAsync(string collectionName, bool expectedExists)
    {
        // Arrange
        var sut = new AzureCosmosDBMongoDBVectorStoreRecordCollection<AzureCosmosDBMongoDBHotel>(fixture.MongoDatabase, collectionName);

        // Act
        var actual = await sut.CollectionExistsAsync();

        // Assert
        Assert.Equal(expectedExists, actual);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanCreateCollectionAsync()
    {
        // Arrange
        var sut = new AzureCosmosDBMongoDBVectorStoreRecordCollection<AzureCosmosDBMongoDBHotel>(fixture.MongoDatabase, fixture.TestCollection);

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

        var options = new AzureCosmosDBMongoDBVectorStoreRecordCollectionOptions<AzureCosmosDBMongoDBHotel>
        {
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.HotelVectorStoreRecordDefinition : null
        };

        var sut = new AzureCosmosDBMongoDBVectorStoreRecordCollection<AzureCosmosDBMongoDBHotel>(fixture.MongoDatabase, collectionName);

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

        var sut = new AzureCosmosDBMongoDBVectorStoreRecordCollection<AzureCosmosDBMongoDBHotel>(fixture.MongoDatabase, TempCollectionName);

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
        var sut = new AzureCosmosDBMongoDBVectorStoreRecordCollection<AzureCosmosDBMongoDBHotel>(fixture.MongoDatabase, fixture.TestCollection);

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

        var sut = new AzureCosmosDBMongoDBVectorStoreRecordCollection<AzureCosmosDBMongoDBHotel>(fixture.MongoDatabase, fixture.TestCollection);

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
        var sut = new AzureCosmosDBMongoDBVectorStoreRecordCollection<AzureCosmosDBMongoDBHotel>(fixture.MongoDatabase, fixture.TestCollection);

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

        var sut = new AzureCosmosDBMongoDBVectorStoreRecordCollection<TestModel>(
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
        var model = new VectorStoreTestModel { Id = "key", HotelName = "Test Name" };

        var sut = new AzureCosmosDBMongoDBVectorStoreRecordCollection<VectorStoreTestModel>(fixture.MongoDatabase, fixture.TestCollection);

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

        var sut = new AzureCosmosDBMongoDBVectorStoreRecordCollection<BsonTestModel>(
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
        var model = new BsonVectorStoreTestModel { Id = "key", HotelName = "Test Name" };

        var sut = new AzureCosmosDBMongoDBVectorStoreRecordCollection<BsonVectorStoreTestModel>(fixture.MongoDatabase, fixture.TestCollection);

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
    public async Task UpsertWithBsonVectorStoreWithNameModelWorksCorrectlyAsync()
    {
        // Arrange
        var model = new BsonVectorStoreWithNameTestModel { Id = "key", HotelName = "Test Name" };

        var sut = new AzureCosmosDBMongoDBVectorStoreRecordCollection<BsonVectorStoreWithNameTestModel>(fixture.MongoDatabase, fixture.TestCollection);

        // Act
        var upsertResult = await sut.UpsertAsync(model);
        var getResult = await sut.GetAsync(model.Id);

        // Assert
        Assert.Equal("key", upsertResult);

        Assert.NotNull(getResult);
        Assert.Equal("key", getResult.Id);
        Assert.Equal("Test Name", getResult.HotelName);
    }

    #region private

    private AzureCosmosDBMongoDBHotel CreateTestHotel(string hotelId)
    {
        return new AzureCosmosDBMongoDBHotel
        {
            HotelId = hotelId,
            HotelName = $"My Hotel {hotelId}",
            HotelCode = 42,
            HotelRating = 4.5f,
            ParkingIncluded = true,
            Tags = { "t1", "t2" },
            Description = "This is a great hotel.",
            DescriptionEmbedding = new[] { 30f, 31f, 32f, 33f },
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
        public string? Id { get; set; }

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
        public string? Id { get; set; }

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
