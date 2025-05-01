// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Threading.Tasks;
using Microsoft.Data.Sqlite;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Sqlite;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Sqlite;

#pragma warning disable CA1859 // Use concrete types when possible for improved performance
#pragma warning disable CS0618 // VectorSearchFilter is obsolete

/// <summary>
/// Integration tests for <see cref="SqliteVectorStoreRecordCollection{TKey, TRecord}"/> class.
/// </summary>
[Collection("SqliteVectorStoreCollection")]
public sealed class SqliteVectorStoreRecordCollectionTests(SqliteVectorStoreFixture fixture)
{
    private const string? SkipReason = "SQLite vector search extension is required";

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CollectionExistsReturnsCollectionStateAsync(bool createCollection)
    {
        // Arrange
        var sut = fixture.GetCollection<ulong, SqliteHotel<ulong>>("CollectionExists");

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
        var sut = fixture.GetCollection<ulong, SqliteHotel<ulong>>("CreateCollection");

        // Act
        await sut.CreateCollectionAsync();

        // Assert
        Assert.True(await sut.CollectionExistsAsync());
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanCreateCollectionForSupportedDistanceFunctionsAsync()
    {
        // Arrange
        var sut = fixture.GetCollection<ulong, RecordWithSupportedDistanceFunctions>("CreateCollectionForSupportedDistanceFunctions");

        // Act
        await sut.CreateCollectionAsync();

        // Assert
        Assert.True(await sut.CollectionExistsAsync());
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanDeleteCollectionAsync()
    {
        // Arrange
        var sut = fixture.GetCollection<ulong, SqliteHotel<ulong>>("DeleteCollection");

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

        var sut = fixture.GetCollection<ulong, SqliteHotel<ulong>>("DeleteCollection", options);

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
        var sut = fixture.GetCollection<ulong, SqliteHotel<ulong>>("DeleteRecord");

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

        var sut = fixture.GetCollection<ulong, SqliteHotel<ulong>>("GetUpsertDeleteBatchWithNumericKey");

        await sut.CreateCollectionAsync();

        var record1 = CreateTestHotel(HotelId1);
        var record2 = CreateTestHotel(HotelId2);
        var record3 = CreateTestHotel(HotelId3);

        var upsertResults = await sut.UpsertAsync([record1, record2, record3]);
        var getResults = await sut.GetAsync([HotelId1, HotelId2, HotelId3]).ToListAsync();

        Assert.Equal([HotelId1, HotelId2, HotelId3], upsertResults);

        Assert.NotNull(getResults.First(l => l.HotelId == HotelId1));
        Assert.NotNull(getResults.First(l => l.HotelId == HotelId2));
        Assert.NotNull(getResults.First(l => l.HotelId == HotelId3));

        // Act
        await sut.DeleteAsync([HotelId1, HotelId2, HotelId3]);

        getResults = await sut.GetAsync([HotelId1, HotelId2, HotelId3]).ToListAsync();

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

        var sut = fixture.GetCollection<string, SqliteHotel<string>>("GetUpsertDeleteBatchWithStringKey") as IVectorStoreRecordCollection<string, SqliteHotel<string>>;

        await sut.CreateCollectionAsync();

        var record1 = CreateTestHotel(HotelId1);
        var record2 = CreateTestHotel(HotelId2);
        var record3 = CreateTestHotel(HotelId3);

        var upsertResults = await sut.UpsertAsync([record1, record2, record3]);
        var getResults = await sut.GetAsync([HotelId1, HotelId2, HotelId3]).ToListAsync();

        Assert.Equal([HotelId1, HotelId2, HotelId3], upsertResults);

        Assert.NotNull(getResults.First(l => l.HotelId == HotelId1));
        Assert.NotNull(getResults.First(l => l.HotelId == HotelId2));
        Assert.NotNull(getResults.First(l => l.HotelId == HotelId3));

        // Act
        await sut.DeleteAsync([HotelId1, HotelId2, HotelId3]);

        getResults = await sut.GetAsync([HotelId1, HotelId2, HotelId3]).ToListAsync();

        // Assert
        Assert.Empty(getResults);
    }

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanGetExistingRecordAsync(bool includeVectors)
    {
        // Arrange
        var collectionNamePostfix = includeVectors ? "WithVectors" : "WithoutVectors";
        var collectionName = $"Collection{collectionNamePostfix}";

        const ulong HotelId = 5;
        var sut = fixture.GetCollection<ulong, SqliteHotel<ulong>>(collectionName);

        await sut.CreateCollectionAsync();

        var record = CreateTestHotel(HotelId);

        using var connection = new SqliteConnection(fixture.ConnectionString);
        await connection.OpenAsync();
        var commandData = connection.CreateCommand();

        commandData.CommandText =
            $"INSERT INTO {collectionName} " +
            "VALUES (@HotelId0, @HotelName0, @HotelCode0, @HotelRating0, @parking_is_included0, @Description0)";

        commandData.Parameters.AddWithValue("@HotelId0", record.HotelId);
        commandData.Parameters.AddWithValue("@HotelName0", record.HotelName);
        commandData.Parameters.AddWithValue("@HotelCode0", record.HotelCode);
        commandData.Parameters.AddWithValue("@HotelRating0", record.HotelRating);
        commandData.Parameters.AddWithValue("@parking_is_included0", record.ParkingIncluded);
        commandData.Parameters.AddWithValue("@Description0", record.Description);

        await commandData.ExecuteNonQueryAsync();

        if (includeVectors)
        {
            var commandVector = connection.CreateCommand();

            commandVector.CommandText =
                $"INSERT INTO vec_{collectionName} " +
                "VALUES (@HotelId0, @DescriptionEmbedding0)";

            commandVector.Parameters.AddWithValue("@HotelId0", record.HotelId);
            commandVector.Parameters.AddWithValue("@DescriptionEmbedding0", GetVectorForStorageModel(record.DescriptionEmbedding!.Value));

            await commandVector.ExecuteNonQueryAsync();
        }

        // Act
        var getResult = await sut.GetAsync(HotelId, new() { IncludeVectors = includeVectors });

        // Assert
        Assert.NotNull(getResult);

        Assert.Equal(record.HotelId, getResult.HotelId);
        Assert.Equal(record.HotelName, getResult.HotelName);
        Assert.Equal(record.HotelCode, getResult.HotelCode);
        Assert.Equal(record.HotelRating, getResult.HotelRating);
        Assert.Equal(record.ParkingIncluded, getResult.ParkingIncluded);
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
    public async Task ItCanUpsertExistingRecordAsync()
    {
        // Arrange
        const ulong HotelId = 5;
        var sut = fixture.GetCollection<ulong, SqliteHotel<ulong>>("UpsertRecord");

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

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task VectorizedSearchReturnsValidResultsByDefaultAsync(bool includeVectors)
    {
        // Arrange
        var hotel1 = CreateTestHotel(hotelId: "key1", embedding: new[] { 30f, 31f, 32f, 33f });
        var hotel2 = CreateTestHotel(hotelId: "key2", embedding: new[] { 31f, 32f, 33f, 34f });
        var hotel3 = CreateTestHotel(hotelId: "key3", embedding: new[] { 20f, 20f, 20f, 20f });
        var hotel4 = CreateTestHotel(hotelId: "key4", embedding: new[] { -1000f, -1000f, -1000f, -1000f });

        var sut = fixture.GetCollection<string, SqliteHotel<string>>("VectorizedSearch");

        await sut.CreateCollectionIfNotExistsAsync();

        await sut.UpsertAsync([hotel4, hotel2, hotel3, hotel1]);

        // Act
        var results = await sut.VectorizedSearchAsync(new ReadOnlyMemory<float>([30f, 31f, 32f, 33f]), top: 3, new()
        {
            IncludeVectors = includeVectors
        }).ToListAsync();

        // Assert
        var ids = results.Select(l => l.Record.HotelId).ToList();

        Assert.Equal("key1", ids[0]);
        Assert.Equal("key2", ids[1]);
        Assert.Equal("key3", ids[2]);

        Assert.DoesNotContain("key4", ids);

        Assert.Equal(0, results.First(l => l.Record.HotelId == "key1").Score);

        Assert.Equal(includeVectors, results.All(result => result.Record.DescriptionEmbedding is not null));
    }

    [Fact(Skip = SkipReason)]
    public async Task VectorizedSearchReturnsValidResultsWithOffsetAsync()
    {
        // Arrange
        var hotel1 = CreateTestHotel(hotelId: "key1", embedding: new[] { 30f, 31f, 32f, 33f });
        var hotel2 = CreateTestHotel(hotelId: "key2", embedding: new[] { 31f, 32f, 33f, 34f });
        var hotel3 = CreateTestHotel(hotelId: "key3", embedding: new[] { 20f, 20f, 20f, 20f });
        var hotel4 = CreateTestHotel(hotelId: "key4", embedding: new[] { -1000f, -1000f, -1000f, -1000f });

        var sut = fixture.GetCollection<string, SqliteHotel<string>>("VectorizedSearchWithOffset");

        await sut.CreateCollectionIfNotExistsAsync();

        await sut.UpsertAsync([hotel4, hotel2, hotel3, hotel1]);

        // Act
        var results = await sut.VectorizedSearchAsync(new ReadOnlyMemory<float>([30f, 31f, 32f, 33f]), top: 2, new()
        {
            Skip = 2
        }).ToListAsync();

        // Assert
        var ids = results.Select(l => l.Record.HotelId).ToList();

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

        var sut = fixture.GetCollection<string, SqliteHotel<string>>("VectorizedSearchWithFilter");

        await sut.CreateCollectionIfNotExistsAsync();

        await sut.UpsertAsync([hotel4, hotel2, hotel3, hotel1]);

        // Act
        var results = await sut.VectorizedSearchAsync(new ReadOnlyMemory<float>([30f, 31f, 32f, 33f]), top: 3, new()
        {
            OldFilter = new VectorSearchFilter().EqualTo(nameof(SqliteHotel<string>.HotelName), "My Hotel key2")
        }).ToListAsync();

        // Assert
        var ids = results.Select(l => l.Record.HotelId).ToList();

        Assert.Equal("key2", ids[0]);

        Assert.DoesNotContain("key1", ids);
        Assert.DoesNotContain("key3", ids);
        Assert.DoesNotContain("key4", ids);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanUpsertAndRetrieveUsingTheDynamicMapperWithNumericKeyAsync()
    {
        const long HotelId = 5;

        var options = new SqliteVectorStoreRecordCollectionOptions<Dictionary<string, object?>>
        {
            VectorStoreRecordDefinition = GetVectorStoreRecordDefinition<ulong>()
        };

        var sut = fixture.GetCollection<object, Dictionary<string, object?>>("DynamicMapperWithNumericKey", options);

        await sut.CreateCollectionAsync();

        var record = CreateTestHotel(HotelId);

        // Act
        var upsertResult = await sut.UpsertAsync(new Dictionary<string, object?>
        {
            ["HotelId"] = HotelId,

            ["HotelName"] = "Dynamic Mapper Hotel",
            ["Description"] = "This is a dynamic mapper hotel",
            ["ParkingIncluded"] = true,
            ["HotelRating"] = 3.6f,

            ["DescriptionEmbedding"] = new ReadOnlyMemory<float>([30f, 31f, 32f, 33f])
        });

        var localGetResult = await sut.GetAsync(HotelId, new GetRecordOptions { IncludeVectors = true });

        // Assert
        Assert.Equal(HotelId, (long)upsertResult);

        Assert.NotNull(localGetResult);
        Assert.Equal("Dynamic Mapper Hotel", localGetResult["HotelName"]);
        Assert.Equal("This is a dynamic mapper hotel", localGetResult["Description"]);
        Assert.True((bool?)localGetResult["ParkingIncluded"]);
        Assert.Equal(3.6f, localGetResult["HotelRating"]);
        Assert.Equal(new[] { 30f, 31f, 32f, 33f }, ((ReadOnlyMemory<float>)localGetResult["DescriptionEmbedding"]!).ToArray());
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanUpsertAndRetrieveUsingTheDynamicMapperWithStringKeyAsync()
    {
        const string HotelId = "key";

        var options = new SqliteVectorStoreRecordCollectionOptions<Dictionary<string, object?>>
        {
            VectorStoreRecordDefinition = GetVectorStoreRecordDefinition<string>()
        };

        var sut = fixture.GetCollection<object, Dictionary<string, object?>>("DynamicMapperWithStringKey", options)
            as IVectorStoreRecordCollection<object, Dictionary<string, object?>>;

        await sut.CreateCollectionAsync();

        var record = CreateTestHotel(HotelId);

        // Act
        var upsertResult = await sut.UpsertAsync(new Dictionary<string, object?>
        {
            ["HotelId"] = HotelId,

            ["HotelName"] = "Dynamic Mapper Hotel",
            ["Description"] = "This is a dynamic mapper hotel",
            ["ParkingIncluded"] = true,
            ["HotelRating"] = 3.6f,

            ["DescriptionEmbedding"] = new ReadOnlyMemory<float>([30f, 31f, 32f, 33f])
        });

        var localGetResult = await sut.GetAsync(HotelId, new GetRecordOptions { IncludeVectors = true });

        // Assert
        Assert.Equal(HotelId, upsertResult);

        Assert.NotNull(localGetResult);
        Assert.Equal("Dynamic Mapper Hotel", localGetResult["HotelName"]);
        Assert.Equal("This is a dynamic mapper hotel", localGetResult["Description"]);
        Assert.True((bool?)localGetResult["ParkingIncluded"]);
        Assert.Equal(3.6f, localGetResult["HotelRating"]);
        Assert.Equal(new[] { 30f, 31f, 32f, 33f }, ((ReadOnlyMemory<float>)localGetResult["DescriptionEmbedding"]!).ToArray());
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
            new VectorStoreRecordDataProperty("Description", typeof(string)),
            new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?), 4) { IndexKind = IndexKind.IvfFlat, DistanceFunction = DistanceFunction.CosineDistance }
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
            DescriptionEmbedding = embedding ?? new[] { 30f, 31f, 32f, 33f },
        };
    }

    private static byte[] GetVectorForStorageModel(ReadOnlyMemory<float> vector)
    {
        ReadOnlySpan<float> floatSpan = vector.Span;

        byte[] byteArray = new byte[floatSpan.Length * sizeof(float)];

        MemoryMarshal.AsBytes(floatSpan).CopyTo(byteArray);

        return byteArray;
    }

#pragma warning disable CA1812
    private sealed class RecordWithSupportedDistanceFunctions
    {
        [VectorStoreRecordKey]
        public ulong Id { get; set; }

        [VectorStoreRecordVector(Dimensions: 4, DistanceFunction = DistanceFunction.CosineDistance)]
        public ReadOnlyMemory<float>? Embedding1 { get; set; }

        [VectorStoreRecordVector(Dimensions: 4, DistanceFunction = DistanceFunction.EuclideanDistance)]
        public ReadOnlyMemory<float>? Embedding2 { get; set; }

        [VectorStoreRecordVector(Dimensions: 4, DistanceFunction = DistanceFunction.ManhattanDistance)]
        public ReadOnlyMemory<float>? Embedding3 { get; set; }
    }
#pragma warning restore CA1812

    #endregion
}
