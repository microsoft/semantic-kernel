// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Threading.Tasks;
using Microsoft.Data.Sqlite;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.SqliteVec;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.SqliteVec;

#pragma warning disable CA1859 // Use concrete types when possible for improved performance
#pragma warning disable CS0618 // VectorSearchFilter is obsolete

/// <summary>
/// Integration tests for <see cref="SqliteCollection{TKey, TRecord}"/> class.
/// </summary>
[Collection("SqliteVectorStoreCollection")]
public sealed class SqliteVectorStoreRecordCollectionTests(SqliteVectorStoreFixture fixture)
{
    private const string? SkipReason = null;

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CollectionExistsReturnsCollectionStateAsync(bool createCollection)
    {
        // Arrange
        using var sut = fixture.GetCollection<long, SqliteHotel<long>>("CollectionExists");

        if (createCollection)
        {
            await sut.EnsureCollectionExistsAsync();
        }

        // Act
        var collectionExists = await sut.CollectionExistsAsync();

        // Assert
        Assert.Equal(createCollection, collectionExists);

        // Cleanup
        await sut.EnsureCollectionDeletedAsync();
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanEnsureCollectionExistsAsync()
    {
        // Arrange
        using var sut = fixture.GetCollection<long, SqliteHotel<long>>("CreateCollection");

        // Act
        await sut.EnsureCollectionExistsAsync();

        // Assert
        Assert.True(await sut.CollectionExistsAsync());
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanCreateCollectionForSupportedDistanceFunctionsAsync()
    {
        // Arrange
        using var sut = fixture.GetCollection<long, RecordWithSupportedDistanceFunctions>("CreateCollectionForSupportedDistanceFunctions");

        // Act
        await sut.EnsureCollectionExistsAsync();

        // Assert
        Assert.True(await sut.CollectionExistsAsync());
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanDeleteCollectionAsync()
    {
        // Arrange
        using var sut = fixture.GetCollection<long, SqliteHotel<long>>("DeleteCollection");

        await sut.EnsureCollectionExistsAsync();

        Assert.True(await sut.CollectionExistsAsync());

        // Act
        await sut.EnsureCollectionDeletedAsync();

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
        const long HotelId = 5;

        var collectionNamePostfix = useRecordDefinition ? "WithDefinition" : "WithType";
        var collectionName = $"Collection{collectionNamePostfix}";

        var options = new SqliteCollectionOptions
        {
            Definition = useRecordDefinition ? GetVectorStoreRecordDefinition<long>() : null
        };

        using var sut = fixture.GetCollection<long, SqliteHotel<long>>("DeleteCollection", options);

        var record = CreateTestHotel(HotelId);

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
        const long HotelId = 5;
        using var sut = fixture.GetCollection<long, SqliteHotel<long>>("DeleteRecord");

        await sut.EnsureCollectionExistsAsync();

        var record = CreateTestHotel(HotelId);

        await sut.UpsertAsync(record);
        var getResult = await sut.GetAsync(HotelId);

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
        const long HotelId1 = 1;
        const long HotelId2 = 2;
        const long HotelId3 = 3;

        using var sut = fixture.GetCollection<long, SqliteHotel<long>>("GetUpsertDeleteBatchWithNumericKey");

        await sut.EnsureCollectionExistsAsync();

        var record1 = CreateTestHotel(HotelId1);
        var record2 = CreateTestHotel(HotelId2);
        var record3 = CreateTestHotel(HotelId3);

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

    [Fact(Skip = SkipReason)]
    public async Task ItCanGetUpsertDeleteBatchWithStringKeyAsync()
    {
        // Arrange
        const string HotelId1 = "11111111-1111-1111-1111-111111111111";
        const string HotelId2 = "22222222-2222-2222-2222-222222222222";
        const string HotelId3 = "33333333-3333-3333-3333-333333333333";

        using var sut = fixture.GetCollection<string, SqliteHotel<string>>("GetUpsertDeleteBatchWithStringKey") as VectorStoreCollection<string, SqliteHotel<string>>;

        await sut.EnsureCollectionExistsAsync();

        var record1 = CreateTestHotel(HotelId1);
        var record2 = CreateTestHotel(HotelId2);
        var record3 = CreateTestHotel(HotelId3);

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

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanGetExistingRecordAsync(bool includeVectors)
    {
        // Arrange
        var collectionNamePostfix = includeVectors ? "WithVectors" : "WithoutVectors";
        var collectionName = $"Collection{collectionNamePostfix}";

        const long HotelId = 5;
        using var sut = fixture.GetCollection<long, SqliteHotel<long>>(collectionName);

        await sut.EnsureCollectionExistsAsync();

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
        const long HotelId = 5;
        using var sut = fixture.GetCollection<long, SqliteHotel<long>>("UpsertRecord");

        await sut.EnsureCollectionExistsAsync();

        var record = CreateTestHotel(HotelId);

        await sut.UpsertAsync(record);
        var getResult = await sut.GetAsync(HotelId);

        Assert.NotNull(getResult);

        // Act
        record.HotelName = "Updated name";
        record.HotelRating = 10;
        record.DescriptionEmbedding = new[] { 1f, 2f, 3f, 4f };

        await sut.UpsertAsync(record);
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
    public async Task SearchReturnsValidResultsByDefaultAsync(bool includeVectors)
    {
        // Arrange
        var hotel1 = CreateTestHotel(hotelId: "key1", embedding: new[] { 30f, 31f, 32f, 33f });
        var hotel2 = CreateTestHotel(hotelId: "key2", embedding: new[] { 31f, 32f, 33f, 34f });
        var hotel3 = CreateTestHotel(hotelId: "key3", embedding: new[] { 20f, 20f, 20f, 20f });
        var hotel4 = CreateTestHotel(hotelId: "key4", embedding: new[] { -1000f, -1000f, -1000f, -1000f });

        using var sut = fixture.GetCollection<string, SqliteHotel<string>>("VectorizedSearch");

        await sut.EnsureCollectionExistsAsync();

        await sut.UpsertAsync([hotel4, hotel2, hotel3, hotel1]);

        // Act
        var results = await sut.SearchAsync(new ReadOnlyMemory<float>([30f, 31f, 32f, 33f]), top: 3, new()
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
    public async Task SearchReturnsValidResultsWithOffsetAsync()
    {
        // Arrange
        var hotel1 = CreateTestHotel(hotelId: "key1", embedding: new[] { 30f, 31f, 32f, 33f });
        var hotel2 = CreateTestHotel(hotelId: "key2", embedding: new[] { 31f, 32f, 33f, 34f });
        var hotel3 = CreateTestHotel(hotelId: "key3", embedding: new[] { 20f, 20f, 20f, 20f });
        var hotel4 = CreateTestHotel(hotelId: "key4", embedding: new[] { -1000f, -1000f, -1000f, -1000f });

        using var sut = fixture.GetCollection<string, SqliteHotel<string>>("SearchWithOffset");

        await sut.EnsureCollectionExistsAsync();

        await sut.UpsertAsync([hotel4, hotel2, hotel3, hotel1]);

        // Act
        var results = await sut.SearchAsync(new ReadOnlyMemory<float>([30f, 31f, 32f, 33f]), top: 2, new()
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
    public async Task SearchReturnsValidResultsWithFilterAsync()
    {
        // Arrange
        var hotel1 = CreateTestHotel(hotelId: "key1", embedding: new[] { 30f, 31f, 32f, 33f });
        var hotel2 = CreateTestHotel(hotelId: "key2", embedding: new[] { 31f, 32f, 33f, 34f });
        var hotel3 = CreateTestHotel(hotelId: "key3", embedding: new[] { 20f, 20f, 20f, 20f });
        var hotel4 = CreateTestHotel(hotelId: "key4", embedding: new[] { -1000f, -1000f, -1000f, -1000f });

        using var sut = fixture.GetCollection<string, SqliteHotel<string>>("SearchWithFilter");

        await sut.EnsureCollectionExistsAsync();

        await sut.UpsertAsync([hotel4, hotel2, hotel3, hotel1]);

        // Act
        var results = await sut.SearchAsync(new ReadOnlyMemory<float>([30f, 31f, 32f, 33f]), top: 3, new()
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

        var options = new SqliteCollectionOptions
        {
            Definition = GetVectorStoreRecordDefinition<long>()
        };

        using var sut = fixture.GetDynamicCollection("DynamicMapperWithNumericKey", options);

        await sut.EnsureCollectionExistsAsync();

        var record = CreateTestHotel(HotelId);

        // Act
        await sut.UpsertAsync(new Dictionary<string, object?>
        {
            ["HotelId"] = HotelId,

            ["HotelName"] = "Dynamic Mapper Hotel",
            ["Description"] = "This is a dynamic mapper hotel",
            ["ParkingIncluded"] = true,
            ["HotelRating"] = 3.6f,

            ["DescriptionEmbedding"] = new ReadOnlyMemory<float>([30f, 31f, 32f, 33f])
        });

        var localGetResult = await sut.GetAsync(HotelId, new RecordRetrievalOptions { IncludeVectors = true });

        // Assert
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

        var options = new SqliteCollectionOptions
        {
            Definition = GetVectorStoreRecordDefinition<string>()
        };

        using var sut = fixture.GetDynamicCollection("DynamicMapperWithStringKey", options)
            as VectorStoreCollection<object, Dictionary<string, object?>>;

        await sut.EnsureCollectionExistsAsync();

        var record = CreateTestHotel(HotelId);

        // Act
        await sut.UpsertAsync(new Dictionary<string, object?>
        {
            ["HotelId"] = HotelId,

            ["HotelName"] = "Dynamic Mapper Hotel",
            ["Description"] = "This is a dynamic mapper hotel",
            ["ParkingIncluded"] = true,
            ["HotelRating"] = 3.6f,

            ["DescriptionEmbedding"] = new ReadOnlyMemory<float>([30f, 31f, 32f, 33f])
        });

        var localGetResult = await sut.GetAsync(HotelId, new RecordRetrievalOptions { IncludeVectors = true });

        // Assert
        Assert.NotNull(localGetResult);
        Assert.Equal("Dynamic Mapper Hotel", localGetResult["HotelName"]);
        Assert.Equal("This is a dynamic mapper hotel", localGetResult["Description"]);
        Assert.True((bool?)localGetResult["ParkingIncluded"]);
        Assert.Equal(3.6f, localGetResult["HotelRating"]);
        Assert.Equal(new[] { 30f, 31f, 32f, 33f }, ((ReadOnlyMemory<float>)localGetResult["DescriptionEmbedding"]!).ToArray());
    }

    #region

    private static VectorStoreCollectionDefinition GetVectorStoreRecordDefinition<TKey>() => new()
    {
        Properties =
        [
            new VectorStoreKeyProperty("HotelId", typeof(TKey)),
            new VectorStoreDataProperty("HotelName", typeof(string)),
            new VectorStoreDataProperty("HotelCode", typeof(int)),
            new VectorStoreDataProperty("ParkingIncluded", typeof(bool)) { StorageName = "parking_is_included" },
            new VectorStoreDataProperty("HotelRating", typeof(float)),
            new VectorStoreDataProperty("Description", typeof(string)),
            new VectorStoreVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?), 4) { IndexKind = IndexKind.IvfFlat, DistanceFunction = DistanceFunction.CosineDistance }
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
        [VectorStoreKey]
        public long Id { get; set; }

        [VectorStoreVector(Dimensions: 4, DistanceFunction = DistanceFunction.CosineDistance)]
        public ReadOnlyMemory<float>? Embedding1 { get; set; }

        [VectorStoreVector(Dimensions: 4, DistanceFunction = DistanceFunction.EuclideanDistance)]
        public ReadOnlyMemory<float>? Embedding2 { get; set; }

        [VectorStoreVector(Dimensions: 4, DistanceFunction = DistanceFunction.ManhattanDistance)]
        public ReadOnlyMemory<float>? Embedding3 { get; set; }
    }
#pragma warning restore CA1812

    #endregion
}
