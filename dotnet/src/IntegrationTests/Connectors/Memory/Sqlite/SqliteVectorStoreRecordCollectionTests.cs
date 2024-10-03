// Copyright (c) Microsoft. All rights reserved.

using System;
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
        var sut = new SqliteVectorStoreRecordCollection<SqliteHotel<ulong>>(fixture.Connection, "CollectionExists");

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
        var sut = new SqliteVectorStoreRecordCollection<SqliteHotel<ulong>>(fixture.Connection, "CreateCollection");

        // Act
        await sut.CreateCollectionAsync();

        // Assert
        Assert.True(await sut.CollectionExistsAsync());
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanDeleteCollectionAsync()
    {
        // Arrange
        var sut = new SqliteVectorStoreRecordCollection<SqliteHotel<ulong>>(fixture.Connection, "DeleteCollection");

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

        var sut = new SqliteVectorStoreRecordCollection<SqliteHotel<ulong>>(fixture.Connection, collectionName);

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

    #endregion
}
