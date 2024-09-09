// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Weaviate;
using Microsoft.SemanticKernel.Data;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Weaviate;

[Collection("WeaviateVectorStoreCollection")]
public sealed class WeaviateVectorStoreRecordCollectionTests(WeaviateVectorStoreFixture fixture)
{
    private const string SkipReason = "Tests are disabled during batch/object request problem investigation.";

    [Fact(Skip = SkipReason)]
    public async Task ItCanCreateCollectionAsync()
    {
        // Arrange
        var sut = new WeaviateVectorStoreRecordCollection<WeaviateHotel>(fixture.HttpClient!, "TestCreateCollection");

        // Act
        await sut.CreateCollectionAsync();

        // Assert
        Assert.True(await sut.CollectionExistsAsync());
    }

    [Theory(Skip = SkipReason)]
    [InlineData("ExistingCollection", true)]
    [InlineData("NonExistentCollection", false)]
    public async Task ItCanCheckIfCollectionExistsAsync(string collectionName, bool collectionExists)
    {
        // Arrange
        var sut = new WeaviateVectorStoreRecordCollection<WeaviateHotel>(fixture.HttpClient!, collectionName);

        if (collectionExists)
        {
            await sut.CreateCollectionAsync();
        }

        // Act
        var result = await sut.CollectionExistsAsync();

        // Assert
        Assert.Equal(collectionExists, result);
    }

    [Theory(Skip = SkipReason)]
    [InlineData("CollectionWithVectorAndDefinition", true, true)]
    [InlineData("CollectionWithVector", true, false)]
    [InlineData("CollectionWithDefinition", false, true)]
    [InlineData("CollectionWithoutVectorAndDefinition", false, false)]
    public async Task ItCanUpsertAndGetRecordAsync(string collectionName, bool includeVectors, bool useRecordDefinition)
    {
        // Arrange
        var hotelId = new Guid("55555555-5555-5555-5555-555555555555");

        var options = new WeaviateVectorStoreRecordCollectionOptions<WeaviateHotel>
        {
            VectorStoreRecordDefinition = useRecordDefinition ? this.GetTestHotelRecordDefinition() : null
        };

        var sut = new WeaviateVectorStoreRecordCollection<WeaviateHotel>(fixture.HttpClient!, collectionName, options);

        var record = this.CreateTestHotel(hotelId);

        // Act && Assert
        await sut.CreateCollectionAsync();

        var upsertResult = await sut.UpsertAsync(record);

        Assert.Equal(hotelId, upsertResult);

        var getResult = await sut.GetAsync(hotelId, new() { IncludeVectors = includeVectors });

        Assert.NotNull(getResult);

        Assert.Equal(record.HotelId, getResult.HotelId);
        Assert.Equal(record.HotelName, getResult.HotelName);
        Assert.Equal(record.HotelCode, getResult.HotelCode);
        Assert.Equal(record.HotelRating, getResult.HotelRating);
        Assert.Equal(record.ParkingIncluded, getResult.ParkingIncluded);
        Assert.Equal(record.Tags.ToArray(), getResult.Tags.ToArray());
        Assert.Equal(record.Description, getResult.Description);
        Assert.Equal(record.Timestamp, getResult.Timestamp);

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
        const string CollectionName = "TestDeleteCollection";

        var sut = new WeaviateVectorStoreRecordCollection<WeaviateHotel>(fixture.HttpClient!, CollectionName);

        await sut.CreateCollectionAsync();

        Assert.True(await sut.CollectionExistsAsync());

        // Act
        await sut.DeleteCollectionAsync();

        // Assert
        Assert.False(await sut.CollectionExistsAsync());
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanDeleteRecordAsync()
    {
        // Arrange
        var hotelId = new Guid("55555555-5555-5555-5555-555555555555");

        var sut = new WeaviateVectorStoreRecordCollection<WeaviateHotel>(fixture.HttpClient!, "TestDeleteRecord");

        var record = this.CreateTestHotel(hotelId);

        var upsertResult = await sut.UpsertAsync(record);
        var getResult = await sut.GetAsync(hotelId);

        Assert.Equal(hotelId, upsertResult);
        Assert.NotNull(getResult);

        // Act
        await sut.DeleteAsync(hotelId);

        getResult = await sut.GetAsync(hotelId);

        // Assert
        Assert.Null(getResult);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanUpsertAndGetAndDeleteBatchAsync()
    {
        // Arrange
        var hotelId1 = new Guid("11111111-1111-1111-1111-111111111111");
        var hotelId2 = new Guid("22222222-2222-2222-2222-222222222222");
        var hotelId3 = new Guid("33333333-3333-3333-3333-333333333333");

        var sut = new WeaviateVectorStoreRecordCollection<WeaviateHotel>(fixture.HttpClient!, "TestBatch");

        await sut.CreateCollectionAsync();

        var record1 = this.CreateTestHotel(hotelId1);
        var record2 = this.CreateTestHotel(hotelId2);
        var record3 = this.CreateTestHotel(hotelId3);

        var upsertResults = await sut.UpsertBatchAsync([record1, record2, record3]).ToListAsync();
        var getResults = await sut.GetBatchAsync([hotelId1, hotelId2, hotelId3]).ToListAsync();

        Assert.Equal([hotelId1, hotelId2, hotelId3], upsertResults);

        Assert.NotNull(getResults.First(l => l.HotelId == hotelId1));
        Assert.NotNull(getResults.First(l => l.HotelId == hotelId2));
        Assert.NotNull(getResults.First(l => l.HotelId == hotelId3));

        // Act
        await sut.DeleteBatchAsync([hotelId1, hotelId2, hotelId3]);

        getResults = await sut.GetBatchAsync([hotelId1, hotelId2, hotelId3]).ToListAsync();

        // Assert
        Assert.Empty(getResults);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanUpsertRecordAsync()
    {
        // Arrange
        var hotelId = new Guid("55555555-5555-5555-5555-555555555555");
        var sut = new WeaviateVectorStoreRecordCollection<WeaviateHotel>(fixture.HttpClient!, "TestUpsert");

        await sut.CreateCollectionAsync();

        var record = this.CreateTestHotel(hotelId);

        var upsertResult = await sut.UpsertAsync(record);
        var getResult = await sut.GetAsync(hotelId);

        Assert.Equal(hotelId, upsertResult);
        Assert.NotNull(getResult);

        // Act
        record.HotelName = "Updated name";
        record.HotelRating = 10;

        upsertResult = await sut.UpsertAsync(record);
        getResult = await sut.GetAsync(hotelId);

        // Assert
        Assert.NotNull(getResult);
        Assert.Equal("Updated name", getResult.HotelName);
        Assert.Equal(10, getResult.HotelRating);
    }

    #region private

    private WeaviateHotel CreateTestHotel(Guid hotelId, string? hotelName = null)
    {
        return new WeaviateHotel
        {
            HotelId = hotelId,
            HotelName = hotelName ?? $"My Hotel {hotelId}",
            HotelCode = 42,
            HotelRating = 4.5f,
            ParkingIncluded = true,
            Tags = { "t1", "t2" },
            Description = "This is a great hotel.",
            DescriptionEmbedding = new[] { 30f, 31f, 32f, 33f },
            Timestamp = new DateTime(2024, 8, 28, 10, 11, 12)
        };
    }

    private VectorStoreRecordDefinition GetTestHotelRecordDefinition()
    {
        return new()
        {
            Properties =
            [
                new VectorStoreRecordKeyProperty("HotelId", typeof(Guid)),
                new VectorStoreRecordDataProperty("HotelName", typeof(string)),
                new VectorStoreRecordDataProperty("HotelCode", typeof(int)),
                new VectorStoreRecordDataProperty("parking_is_included", typeof(bool)),
                new VectorStoreRecordDataProperty("HotelRating", typeof(float)),
                new VectorStoreRecordDataProperty("Tags", typeof(List<string>)),
                new VectorStoreRecordDataProperty("Description", typeof(string)),
                new VectorStoreRecordDataProperty("Timestamp", typeof(DateTime)),
                new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?)) { Dimensions = 4, IndexKind = IndexKind.Hnsw, DistanceFunction = DistanceFunction.CosineDistance }
            ]
        };
    }

    #endregion
}
