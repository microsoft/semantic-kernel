﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Sqlite;
using Microsoft.SemanticKernel.Data;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Sqlite;

/// <summary>
/// Integration tests for <see cref="SqliteVectorStoreRecordCollection{TRecord}"/> class.
/// </summary>
[Collection("SqliteVectorStoreCollection")]
public sealed class SqliteVectorStoreRecordCollectionTests(SqliteVectorStoreFixture fixture)
{
    //private const string? SkipReason = "SQLite vector search extension is required";
    private const string? SkipReason = null;

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CollectionExistsReturnsCollectionStateAsync(bool createCollection)
    {
        // Arrange
        var sut = fixture.GetCollection<SqliteHotel<ulong>>("CollectionExists");

        if (createCollection)
        {
            await sut.CreateCollectionAsync();
        }

        // Act
        var collectionExists = await sut.CollectionExistsAsync();

        // Assert
        Assert.Equal(createCollection, collectionExists);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanCreateCollectionAsync()
    {
        // Arrange
        var sut = fixture.GetCollection<SqliteHotel<ulong>>("CreateCollection");

        // Act
        await sut.CreateCollectionAsync();

        // Assert
        Assert.True(await sut.CollectionExistsAsync());
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanCreateCollectionForSupportedDistanceFunctionsAsync()
    {
        // Arrange
        var sut = fixture.GetCollection<RecordWithSupportedDistanceFunctions>("CreateCollectionForSupportedDistanceFunctions");

        // Act
        await sut.CreateCollectionAsync();

        // Assert
        Assert.True(await sut.CollectionExistsAsync());
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanDeleteCollectionAsync()
    {
        // Arrange
        var sut = fixture.GetCollection<SqliteHotel<ulong>>("DeleteCollection");

        await sut.CreateCollectionAsync();

        Assert.True(await sut.CollectionExistsAsync());

        // Act
        await sut.DeleteCollectionAsync();

        // Assert
        Assert.False(await sut.CollectionExistsAsync());
    }

    [Theory(Skip = SkipReason)]
    [InlineData(true, true)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(false, false)]
    public async Task ItCanCreateCollectionUpsertAndGetAsync(bool includeVectors, bool useRecordDefinition)
    {
        // Arrange
        const ulong HotelId = 5;

        var collectionNamePostfix = useRecordDefinition ? "WithDefinition" : "WithType";
        var collectionName = $"Collection{collectionNamePostfix}";

        var options = new SqliteVectorStoreRecordCollectionOptions<SqliteHotel<ulong>>
        {
            VectorStoreRecordDefinition = useRecordDefinition ? GetVectorStoreRecordDefinition<ulong>() : null
        };

        var sut = fixture.GetCollection<SqliteHotel<ulong>>("DeleteCollection", options);

        var record = CreateTestHotel(HotelId);

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
    public async Task ItCanGetAndDeleteRecordAsync()
    {
        // Arrange
        const ulong HotelId = 5;
        var sut = fixture.GetCollection<SqliteHotel<ulong>>("DeleteRecord");

        await sut.CreateCollectionAsync();

        var record = CreateTestHotel(HotelId);

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
    public async Task ItCanGetUpsertDeleteBatchWithNumericKeyAsync()
    {
        // Arrange
        const ulong HotelId1 = 1;
        const ulong HotelId2 = 2;
        const ulong HotelId3 = 3;

        var sut = fixture.GetCollection<SqliteHotel<ulong>>("GetUpsertDeleteBatchWithNumericKey");

        await sut.CreateCollectionAsync();

        var record1 = CreateTestHotel(HotelId1);
        var record2 = CreateTestHotel(HotelId2);
        var record3 = CreateTestHotel(HotelId3);

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
    public async Task ItCanGetUpsertDeleteBatchWithStringKeyAsync()
    {
        // Arrange
        const string HotelId1 = "11111111-1111-1111-1111-111111111111";
        const string HotelId2 = "22222222-2222-2222-2222-222222222222";
        const string HotelId3 = "33333333-3333-3333-3333-333333333333";

        var sut = fixture.GetCollection<SqliteHotel<string>>("GetUpsertDeleteBatchWithStringKey") as IVectorStoreRecordCollection<string, SqliteHotel<string>>;

        await sut.CreateCollectionAsync();

        var record1 = CreateTestHotel(HotelId1);
        var record2 = CreateTestHotel(HotelId2);
        var record3 = CreateTestHotel(HotelId3);

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
        const ulong HotelId = 5;
        var sut = fixture.GetCollection<SqliteHotel<ulong>>("UpsertRecord");

        await sut.CreateCollectionAsync();

        var record = CreateTestHotel(HotelId);

        var upsertResult = await sut.UpsertAsync(record);
        var getResult = await sut.GetAsync(HotelId);

        Assert.Equal(HotelId, upsertResult);
        Assert.NotNull(getResult);

        // Act
        record.HotelName = "Updated name";
        record.HotelRating = 10;
        record.DescriptionEmbedding = new[] { 1f, 2f, 3f, 4f };

        upsertResult = await sut.UpsertAsync(record);
        getResult = await sut.GetAsync(HotelId, new() { IncludeVectors = true });

        // Assert
        Assert.NotNull(getResult);
        Assert.Equal("Updated name", getResult.HotelName);
        Assert.Equal(10, getResult.HotelRating);

        Assert.NotNull(getResult.DescriptionEmbedding);
        Assert.Equal(record.DescriptionEmbedding!.Value.ToArray(), getResult.DescriptionEmbedding.Value.ToArray());
    }

    [Fact(Skip = SkipReason)]
    public async Task VectorizedSearchReturnsValidResultsByDefaultAsync()
    {
        // Arrange
        var hotel1 = CreateTestHotel(hotelId: "key1", embedding: new[] { 30f, 31f, 32f, 33f });
        var hotel2 = CreateTestHotel(hotelId: "key2", embedding: new[] { 31f, 32f, 33f, 34f });
        var hotel3 = CreateTestHotel(hotelId: "key3", embedding: new[] { 20f, 20f, 20f, 20f });
        var hotel4 = CreateTestHotel(hotelId: "key4", embedding: new[] { -1000f, -1000f, -1000f, -1000f });

        var sut = fixture.GetCollection<SqliteHotel<string>>("VectorizedSearch");

        await sut.CreateCollectionIfNotExistsAsync();

        await sut.UpsertBatchAsync([hotel4, hotel2, hotel3, hotel1]).ToListAsync();

        // Act
        var searchResults = await sut.VectorizedSearchAsync(new ReadOnlyMemory<float>([30f, 31f, 32f, 33f])).ToListAsync();

        // Assert
        var ids = searchResults.Select(l => l.Record.HotelId).ToList();

        Assert.Equal("key1", ids[0]);
        Assert.Equal("key2", ids[1]);
        Assert.Equal("key3", ids[2]);

        Assert.DoesNotContain("key4", ids);

        Assert.Equal(0, searchResults.First(l => l.Record.HotelId == "key1").Score);
    }

    [Fact(Skip = SkipReason)]
    public async Task VectorizedSearchReturnsValidResultsWithOffsetAsync()
    {
        // Arrange
        var hotel1 = CreateTestHotel(hotelId: "key1", embedding: new[] { 30f, 31f, 32f, 33f });
        var hotel2 = CreateTestHotel(hotelId: "key2", embedding: new[] { 31f, 32f, 33f, 34f });
        var hotel3 = CreateTestHotel(hotelId: "key3", embedding: new[] { 20f, 20f, 20f, 20f });
        var hotel4 = CreateTestHotel(hotelId: "key4", embedding: new[] { -1000f, -1000f, -1000f, -1000f });

        var sut = fixture.GetCollection<SqliteHotel<string>>("VectorizedSearchWithOffset");

        await sut.CreateCollectionIfNotExistsAsync();

        await sut.UpsertBatchAsync([hotel4, hotel2, hotel3, hotel1]).ToListAsync();

        // Act
        var searchResults = await sut.VectorizedSearchAsync(new ReadOnlyMemory<float>([30f, 31f, 32f, 33f]), new()
        {
            Top = 2,
            Skip = 2
        }).ToListAsync();

        // Assert
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
        var hotel1 = CreateTestHotel(hotelId: "key1", embedding: new[] { 30f, 31f, 32f, 33f });
        var hotel2 = CreateTestHotel(hotelId: "key2", embedding: new[] { 31f, 32f, 33f, 34f });
        var hotel3 = CreateTestHotel(hotelId: "key3", embedding: new[] { 20f, 20f, 20f, 20f });
        var hotel4 = CreateTestHotel(hotelId: "key4", embedding: new[] { -1000f, -1000f, -1000f, -1000f });

        var sut = fixture.GetCollection<SqliteHotel<string>>("VectorizedSearchWithFilter");

        await sut.CreateCollectionIfNotExistsAsync();

        await sut.UpsertBatchAsync([hotel4, hotel2, hotel3, hotel1]).ToListAsync();

        // Act
        var searchResults = await sut.VectorizedSearchAsync(new ReadOnlyMemory<float>([30f, 31f, 32f, 33f]), new()
        {
            Filter = new VectorSearchFilter().EqualTo(nameof(SqliteHotel<string>.HotelName), "My Hotel key2")
        }).ToListAsync();

        // Assert
        var ids = searchResults.Select(l => l.Record.HotelId).ToList();

        Assert.Equal("key2", ids[0]);

        Assert.DoesNotContain("key1", ids);
        Assert.DoesNotContain("key3", ids);
        Assert.DoesNotContain("key4", ids);
    }

    #region

    private static VectorStoreRecordDefinition GetVectorStoreRecordDefinition<TKey>() => new()
    {
        Properties =
        [
            new VectorStoreRecordKeyProperty("HotelId", typeof(TKey)),
            new VectorStoreRecordDataProperty("HotelName", typeof(string)),
            new VectorStoreRecordDataProperty("HotelCode", typeof(int)),
            new VectorStoreRecordDataProperty("ParkingIncluded", typeof(bool)) { StoragePropertyName = "parking_is_included" },
            new VectorStoreRecordDataProperty("HotelRating", typeof(float)),
            new VectorStoreRecordDataProperty("Timestamp", typeof(DateTime)),
            new VectorStoreRecordDataProperty("Description", typeof(string)),
            new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?)) { Dimensions = 4, IndexKind = IndexKind.IvfFlat, DistanceFunction = DistanceFunction.CosineDistance }
        ]
    };

    private static SqliteHotel<TKey> CreateTestHotel<TKey>(TKey hotelId, ReadOnlyMemory<float>? embedding = null)
    {
        return new SqliteHotel<TKey>
        {
            HotelId = hotelId,
            HotelName = $"My Hotel {hotelId}",
            HotelCode = 42,
            HotelRating = 4.5f,
            ParkingIncluded = true,
            Description = "This is a great hotel.",
            Timestamp = new DateTime(2024, 09, 23, 15, 32, 33),
            DescriptionEmbedding = embedding ?? new[] { 30f, 31f, 32f, 33f },
        };
    }

    private sealed class RecordWithSupportedDistanceFunctions
    {
        [VectorStoreRecordKey]
        public ulong Id { get; set; }

        [VectorStoreRecordVector(Dimensions: 4, DistanceFunction: DistanceFunction.CosineDistance)]
        public ReadOnlyMemory<float>? Embedding1 { get; set; }

        [VectorStoreRecordVector(Dimensions: 4, DistanceFunction: DistanceFunction.EuclideanDistance)]
        public ReadOnlyMemory<float>? Embedding2 { get; set; }

        [VectorStoreRecordVector(Dimensions: 4, DistanceFunction: DistanceFunction.ManhattanDistance)]
        public ReadOnlyMemory<float>? Embedding3 { get; set; }
    }

    #endregion
}
