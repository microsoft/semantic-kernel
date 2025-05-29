// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.CosmosNoSql;
using SemanticKernel.IntegrationTests.Connectors.Memory.Xunit;
using Xunit;
using DistanceFunction = Microsoft.Extensions.VectorData.DistanceFunction;
using IndexKind = Microsoft.Extensions.VectorData.IndexKind;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.CosmosNoSql;

#pragma warning disable CA1859 // Use concrete types when possible for improved performance
#pragma warning disable CS0618 // VectorSearchFilter is obsolete

/// <summary>
/// Integration tests for <see cref="CosmosNoSqlCollection{TKey, TRecord}"/> class.
/// </summary>
[Collection("CosmosNoSqlCollection")]
[CosmosNoSqlConnectionStringSetCondition]
public sealed class CosmosNoSqlCollectionTests(CosmosNoSqlVectorStoreFixture fixture)
{
    [VectorStoreFact]
    public async Task ItCanEnsureCollectionExistsAsync()
    {
        // Arrange
        using var sut = new CosmosNoSqlCollection<string, CosmosNoSqlHotel>(fixture.Database!, "test-create-collection");

        // Act
        await sut.EnsureCollectionExistsAsync();

        // Assert
        Assert.True(await sut.CollectionExistsAsync());
    }

    [VectorStoreTheory]
    [InlineData("sk-test-hotels", true)]
    [InlineData("nonexistentcollection", false)]
    public async Task CollectionExistsReturnsCollectionStateAsync(string collectionName, bool expectedExists)
    {
        // Arrange
        using var sut = new CosmosNoSqlCollection<string, CosmosNoSqlHotel>(fixture.Database!, collectionName);

        if (expectedExists)
        {
            await fixture.Database!.CreateContainerIfNotExistsAsync(new ContainerProperties(collectionName, "/id"));
        }

        // Act
        var actual = await sut.CollectionExistsAsync();

        // Assert
        Assert.Equal(expectedExists, actual);
    }

    [VectorStoreTheory]
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

        var options = new CosmosNoSqlCollectionOptions
        {
            Definition = useRecordDefinition ? this.GetTestHotelRecordDefinition() : null
        };

        using var sut = new CosmosNoSqlCollection<string, CosmosNoSqlHotel>(fixture.Database!, collectionName);

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

    [VectorStoreFact]
    public async Task ItCanDeleteCollectionAsync()
    {
        // Arrange
        const string TempCollectionName = "test-delete-collection";
        await fixture.Database!.CreateContainerAsync(new ContainerProperties(TempCollectionName, "/id"));

        using var sut = new CosmosNoSqlCollection<string, CosmosNoSqlHotel>(fixture.Database!, TempCollectionName);

        Assert.True(await sut.CollectionExistsAsync());

        // Act
        await sut.EnsureCollectionDeletedAsync();

        // Assert
        Assert.False(await sut.CollectionExistsAsync());
    }

    [VectorStoreTheory]
    [InlineData("consistent-mode-collection", IndexingMode.Consistent)]
    [InlineData("lazy-mode-collection", IndexingMode.Lazy)]
    [InlineData("none-mode-collection", IndexingMode.None)]
    public async Task ItCanGetAndDeleteRecordAsync(string collectionName, IndexingMode indexingMode)
    {
        // Arrange
        const string HotelId = "55555555-5555-5555-5555-555555555555";
        using var sut = new CosmosNoSqlCollection<string, CosmosNoSqlHotel>(
            fixture.Database!,
            collectionName,
            new() { IndexingMode = indexingMode, Automatic = indexingMode != IndexingMode.None });

        await sut.EnsureCollectionExistsAsync();

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

    [VectorStoreFact]
    public async Task ItCanGetAndDeleteRecordWithPartitionKeyAsync()
    {
        // Arrange
        const string HotelId = "55555555-5555-5555-5555-555555555555";
        const string HotelName = "Test Hotel Name";

        using VectorStoreCollection<CosmosNoSqlCompositeKey, CosmosNoSqlHotel> sut =
            new CosmosNoSqlCollection<CosmosNoSqlCompositeKey, CosmosNoSqlHotel>(
                fixture.Database!,
                "delete-with-partition-key",
                new() { PartitionKeyPropertyName = "HotelName" });

        await sut.EnsureCollectionExistsAsync();

        var record = this.CreateTestHotel(HotelId, HotelName);

        await sut.UpsertAsync(record);

        var key = new CosmosNoSqlCompositeKey(record.HotelId, record.HotelName!);
        var getResult = await sut.GetAsync(key);

        Assert.NotNull(getResult);

        // Act
        await sut.DeleteAsync(key);

        getResult = await sut.GetAsync(key);

        // Assert
        Assert.Null(getResult);
    }

    [VectorStoreFact]
    public async Task ItCanGetAndDeleteBatchAsync()
    {
        // Arrange
        const string HotelId1 = "11111111-1111-1111-1111-111111111111";
        const string HotelId2 = "22222222-2222-2222-2222-222222222222";
        const string HotelId3 = "33333333-3333-3333-3333-333333333333";

        using var sut = new CosmosNoSqlCollection<string, CosmosNoSqlHotel>(fixture.Database!, "get-and-delete-batch");

        await sut.EnsureCollectionExistsAsync();

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

    [VectorStoreFact]
    public async Task ItCanUpsertRecordAsync()
    {
        // Arrange
        const string HotelId = "55555555-5555-5555-5555-555555555555";
        using var sut = new CosmosNoSqlCollection<string, CosmosNoSqlHotel>(fixture.Database!, "upsert-record");

        await sut.EnsureCollectionExistsAsync();

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

    [VectorStoreFact]
    public async Task SearchReturnsValidResultsByDefaultAsync()
    {
        // Arrange
        var hotel1 = this.CreateTestHotel(hotelId: "key1", embedding: new[] { 30f, 31f, 32f, 33f });
        var hotel2 = this.CreateTestHotel(hotelId: "key2", embedding: new[] { 31f, 32f, 33f, 34f });
        var hotel3 = this.CreateTestHotel(hotelId: "key3", embedding: new[] { 20f, 20f, 20f, 20f });
        var hotel4 = this.CreateTestHotel(hotelId: "key4", embedding: new[] { -1000f, -1000f, -1000f, -1000f });

        using var sut = new CosmosNoSqlCollection<string, CosmosNoSqlHotel>(fixture.Database!, "vector-search-default");

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

    [VectorStoreFact]
    public async Task SearchReturnsValidResultsWithOffsetAsync()
    {
        // Arrange
        var hotel1 = this.CreateTestHotel(hotelId: "key1", embedding: new[] { 30f, 31f, 32f, 33f });
        var hotel2 = this.CreateTestHotel(hotelId: "key2", embedding: new[] { 31f, 32f, 33f, 34f });
        var hotel3 = this.CreateTestHotel(hotelId: "key3", embedding: new[] { 20f, 20f, 20f, 20f });
        var hotel4 = this.CreateTestHotel(hotelId: "key4", embedding: new[] { -1000f, -1000f, -1000f, -1000f });

        using var sut = new CosmosNoSqlCollection<string, CosmosNoSqlHotel>(fixture.Database!, "vector-search-with-offset");

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

    [VectorStoreTheory]
    [MemberData(nameof(SearchWithFilterData))]
    public async Task SearchReturnsValidResultsWithFilterAsync(VectorSearchFilter filter, List<string> expectedIds)
    {
        // Arrange
        var hotel1 = this.CreateTestHotel(hotelId: "key1", embedding: new[] { 30f, 31f, 32f, 33f });
        var hotel2 = this.CreateTestHotel(hotelId: "key2", embedding: new[] { 31f, 32f, 33f, 34f });
        var hotel3 = this.CreateTestHotel(hotelId: "key3", embedding: new[] { 20f, 20f, 20f, 20f });
        var hotel4 = this.CreateTestHotel(hotelId: "key4", embedding: new[] { -1000f, -1000f, -1000f, -1000f });

        using var sut = new CosmosNoSqlCollection<string, CosmosNoSqlHotel>(fixture.Database!, "vector-search-with-filter");

        await sut.EnsureCollectionExistsAsync();

        await sut.UpsertAsync([hotel4, hotel2, hotel3, hotel1]);

        // Act
        var searchResults = await sut.SearchAsync(new ReadOnlyMemory<float>([30f, 31f, 32f, 33f]), top: 4, new()
        {
            OldFilter = filter,
        }).ToListAsync();

        // Assert
        var actualIds = searchResults.Select(l => l.Record.HotelId).ToList();

        Assert.Equal(expectedIds, actualIds);
    }

    [VectorStoreFact]
    public async Task ItCanUpsertAndRetrieveUsingTheDynamicMapperAsync()
    {
        // Arrange
        const string HotelId = "55555555-5555-5555-5555-555555555555";
        var options = new CosmosNoSqlCollectionOptions
        {
            Definition = this.GetTestHotelRecordDefinition()
        };

        using var sut = new CosmosNoSqlDynamicCollection(fixture.Database!, "dynamic-mapper", options);

        await sut.EnsureCollectionExistsAsync();

        // Act
        await sut.UpsertAsync(new Dictionary<string, object?>
        {
            ["HotelId"] = HotelId,

            ["HotelName"] = "Dynamic Mapper Hotel",
            ["Description"] = "This is a dynamic mapper hotel",
            ["Tags"] = new List<string> { "dynamic" },
            ["parking_is_included"] = false,
            ["Timestamp"] = new DateTimeOffset(1970, 1, 18, 0, 0, 0, TimeSpan.Zero),
            ["HotelRating"] = 3.6f,

            ["DescriptionEmbedding"] = new ReadOnlyMemory<float>([30f, 31f, 32f, 33f])
        });

        var localGetResult = await sut.GetAsync(HotelId, new RecordRetrievalOptions { IncludeVectors = true });

        // Assert
        Assert.NotNull(localGetResult);
        Assert.Equal("Dynamic Mapper Hotel", localGetResult["HotelName"]);
        Assert.Equal("This is a dynamic mapper hotel", localGetResult["Description"]);
        Assert.Equal(new List<string> { "dynamic" }, localGetResult["Tags"]);
        Assert.False((bool?)localGetResult["parking_is_included"]);
        Assert.Equal(new DateTimeOffset(1970, 1, 18, 0, 0, 0, TimeSpan.Zero), localGetResult["Timestamp"]);
        Assert.Equal(3.6f, localGetResult["HotelRating"]);
        Assert.Equal(new[] { 30f, 31f, 32f, 33f }, ((ReadOnlyMemory<float>)localGetResult["DescriptionEmbedding"]!).ToArray());
    }

    public static TheoryData<VectorSearchFilter, List<string>> SearchWithFilterData => new()
    {
        {
            new VectorSearchFilter()
                .EqualTo(nameof(CosmosNoSqlHotel.HotelName), "My Hotel key2"),
            ["key2"]
        },
        {
            new VectorSearchFilter()
                .AnyTagEqualTo(nameof(CosmosNoSqlHotel.Tags), "t2"),
            ["key1", "key2", "key3", "key4"]
        },
        {
            new VectorSearchFilter()
                .EqualTo(nameof(CosmosNoSqlHotel.HotelName), "My Hotel key2")
                .AnyTagEqualTo(nameof(CosmosNoSqlHotel.Tags), "t2"),
            ["key2"]
        },
        {
            new VectorSearchFilter()
                .EqualTo(nameof(CosmosNoSqlHotel.HotelName), "non-existent-hotel")
                .AnyTagEqualTo(nameof(CosmosNoSqlHotel.Tags), "non-existent-tag"),
            []
        },
    };

    #region private

    private CosmosNoSqlHotel CreateTestHotel(
        string hotelId,
        string? hotelName = null,
        ReadOnlyMemory<float>? embedding = null)
    {
        return new CosmosNoSqlHotel
        {
            HotelId = hotelId,
            HotelName = hotelName ?? $"My Hotel {hotelId}",
            HotelCode = 42,
            HotelRating = 4.5f,
            ParkingIncluded = true,
            Tags = { "t1", "t2" },
            Description = "This is a great hotel.",
            DescriptionEmbedding = embedding ?? new[] { 30f, 31f, 32f, 33f },
            Timestamp = new DateTimeOffset(2024, 9, 24, 17, 28, 32, TimeSpan.Zero),
        };
    }

    private VectorStoreCollectionDefinition GetTestHotelRecordDefinition()
    {
        return new()
        {
            Properties =
            [
                new VectorStoreKeyProperty("HotelId", typeof(string)),
                new VectorStoreDataProperty("HotelName", typeof(string)),
                new VectorStoreDataProperty("HotelCode", typeof(int)),
                new VectorStoreDataProperty("parking_is_included", typeof(bool)),
                new VectorStoreDataProperty("HotelRating", typeof(float)),
                new VectorStoreDataProperty("Tags", typeof(List<string>)),
                new VectorStoreDataProperty("Description", typeof(string)),
                new VectorStoreDataProperty("Timestamp", typeof(DateTimeOffset)),
                new VectorStoreVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?), 4) { IndexKind = IndexKind.Flat, DistanceFunction = DistanceFunction.CosineSimilarity }
            ]
        };
    }

    #endregion
}
