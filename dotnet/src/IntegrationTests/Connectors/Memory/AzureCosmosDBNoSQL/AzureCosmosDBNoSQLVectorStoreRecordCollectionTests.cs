// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Azure.Cosmos;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;
using Microsoft.SemanticKernel.Data;
using Xunit;
using DistanceFunction = Microsoft.SemanticKernel.Data.DistanceFunction;
using IndexKind = Microsoft.SemanticKernel.Data.IndexKind;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.AzureCosmosDBNoSQL;

/// <summary>
/// Integration tests for <see cref="AzureCosmosDBNoSQLVectorStoreRecordCollection{TRecord}"/> class.
/// </summary>
[Collection("AzureCosmosDBNoSQLVectorStoreCollection")]
public sealed class AzureCosmosDBNoSQLVectorStoreRecordCollectionTests(AzureCosmosDBNoSQLVectorStoreFixture fixture)
{
    private const string? SkipReason = "Azure CosmosDB NoSQL cluster is required";

    [Fact(Skip = SkipReason)]
    public async Task ItCanCreateCollectionAsync()
    {
        // Arrange
        var sut = new AzureCosmosDBNoSQLVectorStoreRecordCollection<AzureCosmosDBNoSQLHotel>(fixture.Database!, "test-create-collection");

        // Act
        await sut.CreateCollectionAsync();

        // Assert
        Assert.True(await sut.CollectionExistsAsync());
    }

    [Theory(Skip = SkipReason)]
    [InlineData("sk-test-hotels", true)]
    [InlineData("nonexistentcollection", false)]
    public async Task CollectionExistsReturnsCollectionStateAsync(string collectionName, bool expectedExists)
    {
        // Arrange
        var sut = new AzureCosmosDBNoSQLVectorStoreRecordCollection<AzureCosmosDBNoSQLHotel>(fixture.Database!, collectionName);

        if (expectedExists)
        {
            await fixture.Database!.CreateContainerIfNotExistsAsync(new ContainerProperties(collectionName, "/id"));
        }

        // Act
        var actual = await sut.CollectionExistsAsync();

        // Assert
        Assert.Equal(expectedExists, actual);
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
        collectionNamePostfix = includeVectors ? $"{collectionNamePostfix}-with-vectors" : $"{collectionNamePostfix}-without-vectors";
        var collectionName = $"collection-{collectionNamePostfix}";

        var options = new AzureCosmosDBNoSQLVectorStoreRecordCollectionOptions<AzureCosmosDBNoSQLHotel>
        {
            VectorStoreRecordDefinition = useRecordDefinition ? this.GetTestHotelRecordDefinition() : null
        };

        var sut = new AzureCosmosDBNoSQLVectorStoreRecordCollection<AzureCosmosDBNoSQLHotel>(fixture.Database!, collectionName);

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
        const string TempCollectionName = "test-delete-collection";
        await fixture.Database!.CreateContainerAsync(new ContainerProperties(TempCollectionName, "/id"));

        var sut = new AzureCosmosDBNoSQLVectorStoreRecordCollection<AzureCosmosDBNoSQLHotel>(fixture.Database!, TempCollectionName);

        Assert.True(await sut.CollectionExistsAsync());

        // Act
        await sut.DeleteCollectionAsync();

        // Assert
        Assert.False(await sut.CollectionExistsAsync());
    }

    [Theory(Skip = SkipReason)]
    [InlineData("consistent-mode-collection", IndexingMode.Consistent)]
    [InlineData("lazy-mode-collection", IndexingMode.Lazy)]
    [InlineData("none-mode-collection", IndexingMode.None)]
    public async Task ItCanGetAndDeleteRecordAsync(string collectionName, IndexingMode indexingMode)
    {
        // Arrange
        const string HotelId = "55555555-5555-5555-5555-555555555555";
        var sut = new AzureCosmosDBNoSQLVectorStoreRecordCollection<AzureCosmosDBNoSQLHotel>(
            fixture.Database!,
            collectionName,
            new() { IndexingMode = indexingMode, Automatic = indexingMode != IndexingMode.None });

        await sut.CreateCollectionAsync();

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
    public async Task ItCanGetAndDeleteRecordWithPartitionKeyAsync()
    {
        // Arrange
        const string HotelId = "55555555-5555-5555-5555-555555555555";
        const string HotelName = "Test Hotel Name";

        IVectorStoreRecordCollection<AzureCosmosDBNoSQLCompositeKey, AzureCosmosDBNoSQLHotel> sut =
            new AzureCosmosDBNoSQLVectorStoreRecordCollection<AzureCosmosDBNoSQLHotel>(
                fixture.Database!,
                "delete-with-partition-key",
                new() { PartitionKeyPropertyName = "HotelName" });

        await sut.CreateCollectionAsync();

        var record = this.CreateTestHotel(HotelId, HotelName);

        var upsertResult = await sut.UpsertAsync(record);

        var key = new AzureCosmosDBNoSQLCompositeKey(record.HotelId, record.HotelName!);
        var getResult = await sut.GetAsync(key);

        Assert.Equal(HotelId, upsertResult.RecordKey);
        Assert.Equal(HotelName, upsertResult.PartitionKey);
        Assert.NotNull(getResult);

        // Act
        await sut.DeleteAsync(key);

        getResult = await sut.GetAsync(key);

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

        var sut = new AzureCosmosDBNoSQLVectorStoreRecordCollection<AzureCosmosDBNoSQLHotel>(fixture.Database!, "get-and-delete-batch");

        await sut.CreateCollectionAsync();

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
        var sut = new AzureCosmosDBNoSQLVectorStoreRecordCollection<AzureCosmosDBNoSQLHotel>(fixture.Database!, "upsert-record");

        await sut.CreateCollectionAsync();

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

    #region private

    private AzureCosmosDBNoSQLHotel CreateTestHotel(string hotelId, string? hotelName = null)
    {
        return new AzureCosmosDBNoSQLHotel
        {
            HotelId = hotelId,
            HotelName = hotelName ?? $"My Hotel {hotelId}",
            HotelCode = 42,
            HotelRating = 4.5f,
            ParkingIncluded = true,
            Tags = { "t1", "t2" },
            Description = "This is a great hotel.",
            DescriptionEmbedding = new[] { 30f, 31f, 32f, 33f },
        };
    }

    private VectorStoreRecordDefinition GetTestHotelRecordDefinition()
    {
        return new()
        {
            Properties =
            [
                new VectorStoreRecordKeyProperty("HotelId", typeof(string)),
                new VectorStoreRecordDataProperty("HotelName", typeof(string)),
                new VectorStoreRecordDataProperty("HotelCode", typeof(int)),
                new VectorStoreRecordDataProperty("parking_is_included", typeof(bool)),
                new VectorStoreRecordDataProperty("HotelRating", typeof(float)),
                new VectorStoreRecordDataProperty("Tags", typeof(List<string>)),
                new VectorStoreRecordDataProperty("Description", typeof(string)),
                new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?)) { Dimensions = 4, IndexKind = IndexKind.Flat, DistanceFunction = DistanceFunction.CosineDistance }
            ]
        };
    }

    #endregion
}
