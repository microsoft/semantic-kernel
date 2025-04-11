// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Npgsql;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Postgres;

#pragma warning disable CS0618 // VectorSearchFilter is obsolete

[Collection("PostgresVectorStoreCollection")]
public sealed class PostgresVectorStoreRecordCollectionTests(PostgresVectorStoreFixture fixture)
{
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CollectionExistsReturnsCollectionStateAsync(bool createCollection)
    {
        // Arrange
        var sut = fixture.GetCollection<int, PostgresHotel<int>>("CollectionExists");

        if (createCollection)
        {
            await sut.CreateCollectionAsync();
        }

        try
        {
            // Act
            var collectionExists = await sut.CollectionExistsAsync();

            // Assert
            Assert.Equal(createCollection, collectionExists);
        }
        finally
        {
            // Cleanup
            if (createCollection)
            {
                await sut.DeleteCollectionAsync();
            }
        }
    }

    [Fact]
    public async Task CanCreateCollectionWithSpecialCharactersInNameAsync()
    {
        // Arrange
        var sut = fixture.GetCollection<int, PostgresHotel<int>>("Special-Char");

        try
        {
            // Act
            await sut.CreateCollectionAsync();
        }
        finally
        {
            // Cleanup
            await sut.DeleteCollectionAsync();
        }
    }

    [Fact]
    public async Task CollectionCanUpsertAndGetAsync()
    {
        // Arrange
        var sut = fixture.GetCollection<int, PostgresHotel<int>>("CollectionCanUpsertAndGet");
        if (await sut.CollectionExistsAsync())
        {
            await sut.DeleteCollectionAsync();
        }

        await sut.CreateCollectionAsync();

        var writtenHotel1 = new PostgresHotel<int> { HotelId = 1, HotelName = "Hotel 1", HotelCode = 1, ParkingIncluded = true, HotelRating = 4.5f, Tags = ["tag1", "tag2"] };
        var writtenHotel2 = new PostgresHotel<int> { HotelId = 2, HotelName = "Hotel 2", HotelCode = 2, ParkingIncluded = false, HotelRating = 2.5f, ListInts = [1, 2] };

        try
        {
            // Act

            await sut.UpsertAsync(writtenHotel1);

            await sut.UpsertAsync(writtenHotel2);

            var fetchedHotel1 = await sut.GetAsync(1);
            var fetchedHotel2 = await sut.GetAsync(2);

            // Assert
            Assert.NotNull(fetchedHotel1);
            Assert.Equal(1, fetchedHotel1!.HotelId);
            Assert.Equal("Hotel 1", fetchedHotel1!.HotelName);
            Assert.Equal(1, fetchedHotel1!.HotelCode);
            Assert.True(fetchedHotel1!.ParkingIncluded);
            Assert.Equal(4.5f, fetchedHotel1!.HotelRating);
            Assert.NotNull(fetchedHotel1!.Tags);
            Assert.Equal(2, fetchedHotel1!.Tags!.Count);
            Assert.Equal("tag1", fetchedHotel1!.Tags![0]);
            Assert.Equal("tag2", fetchedHotel1!.Tags![1]);
            Assert.Null(fetchedHotel1!.ListInts);

            // Since these values are updated in the database, they will not match existly, but should be very close to each other.
            Assert.True(TruncateMilliseconds(fetchedHotel1.CreatedAt) >= TruncateMilliseconds(writtenHotel1.CreatedAt) && TruncateMilliseconds(fetchedHotel1.CreatedAt) <= TruncateMilliseconds(writtenHotel1.CreatedAt).AddSeconds(1));
            Assert.True(TruncateMilliseconds(fetchedHotel1.UpdatedAt) >= TruncateMilliseconds(writtenHotel1.UpdatedAt) && TruncateMilliseconds(fetchedHotel1.UpdatedAt) <= TruncateMilliseconds(writtenHotel1.UpdatedAt).AddSeconds(1));

            Assert.NotNull(fetchedHotel2);
            Assert.Equal(2, fetchedHotel2!.HotelId);
            Assert.Equal("Hotel 2", fetchedHotel2!.HotelName);
            Assert.Equal(2, fetchedHotel2!.HotelCode);
            Assert.False(fetchedHotel2!.ParkingIncluded);
            Assert.Equal(2.5f, fetchedHotel2!.HotelRating);
            Assert.NotNull(fetchedHotel2!.Tags);
            Assert.Empty(fetchedHotel2!.Tags);
            Assert.NotNull(fetchedHotel2!.ListInts);
            Assert.Equal(2, fetchedHotel2!.ListInts!.Count);
            Assert.Equal(1, fetchedHotel2!.ListInts![0]);
            Assert.Equal(2, fetchedHotel2!.ListInts![1]);

            // Since these values are updated in the database, they will not match existly, but should be very close to each other.
            Assert.True(TruncateMilliseconds(fetchedHotel2.CreatedAt) >= TruncateMilliseconds(writtenHotel2.CreatedAt) && TruncateMilliseconds(fetchedHotel2.CreatedAt) <= TruncateMilliseconds(writtenHotel2.CreatedAt).AddSeconds(1));
            Assert.True(TruncateMilliseconds(fetchedHotel2.UpdatedAt) >= TruncateMilliseconds(writtenHotel2.UpdatedAt) && TruncateMilliseconds(fetchedHotel2.UpdatedAt) <= TruncateMilliseconds(writtenHotel2.UpdatedAt).AddSeconds(1));
        }
        finally
        {
            // Cleanup
            await sut.DeleteCollectionAsync();
        }
    }

    public static IEnumerable<object[]> ItCanGetAndDeleteRecordParameters =>
        new List<object[]>
        {
            new object[] { typeof(short), (short)3 },
            new object[] { typeof(int), 5 },
            new object[] { typeof(long), 7L },
            new object[] { typeof(string), "key1" },
            new object[] { typeof(Guid), Guid.NewGuid() }
        };

    [Theory]
    [MemberData(nameof(ItCanGetAndDeleteRecordParameters))]
    public async Task ItCanGetAndDeleteRecordAsync<TKey>(Type idType, TKey? key)
    {
        // Arrange
        var collectionName = "DeleteRecord";
        var sut = this.GetCollection(idType, collectionName);

        await sut.CreateCollectionAsync();

        try
        {
            var record = this.CreateRecord<TKey>(idType, key!);
            var recordKey = record.HotelId;
            var upsertResult = await sut.UpsertAsync(record);
            var getResult = await sut.GetAsync(recordKey);

            Assert.Equal(key, upsertResult);
            Assert.NotNull(getResult);

            // Act
            await sut.DeleteAsync(recordKey);

            getResult = await sut.GetAsync(recordKey);

            // Assert
            Assert.Null(getResult);
        }
        finally
        {
            // Cleanup
            await sut.DeleteCollectionAsync();
        }
    }

    [Fact]
    public async Task ItCanGetUpsertDeleteBatchAsync()
    {
        // Arrange
        const int HotelId1 = 1;
        const int HotelId2 = 2;
        const int HotelId3 = 3;

        var sut = fixture.GetCollection<int, PostgresHotel<int>>("GetUpsertDeleteBatch");

        await sut.CreateCollectionAsync();

        var record1 = new PostgresHotel<int> { HotelId = HotelId1, HotelName = "Hotel 1", HotelCode = 1, ParkingIncluded = true, HotelRating = 4.5f, Tags = ["tag1", "tag2"] };
        var record2 = new PostgresHotel<int> { HotelId = HotelId2, HotelName = "Hotel 2", HotelCode = 1, ParkingIncluded = false, HotelRating = 3.5f, Tags = ["tag1", "tag3"] };
        var record3 = new PostgresHotel<int> { HotelId = HotelId3, HotelName = "Hotel 3", HotelCode = 1, ParkingIncluded = true, HotelRating = 2.5f, Tags = ["tag1", "tag4"] };

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

    [Fact]
    public async Task ItCanUpsertExistingRecordAsync()
    {
        // Arrange
        const int HotelId = 5;
        var sut = fixture.GetCollection<int, PostgresHotel<int>>("UpsertRecord");

        await sut.CreateCollectionAsync();

        var record = new PostgresHotel<int> { HotelId = HotelId, HotelName = "Hotel 1", HotelCode = 1, ParkingIncluded = true, HotelRating = 4.5f, Tags = ["tag1", "tag2"] };

        var upsertResult = await sut.UpsertAsync(record);
        var getResult = await sut.GetAsync(HotelId, new() { IncludeVectors = true });

        Assert.Equal(HotelId, upsertResult);
        Assert.NotNull(getResult);
        Assert.Null(getResult!.DescriptionEmbedding);

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

    [Fact]
    public async Task ItCanReadManuallyInsertedRecordAsync()
    {
        const string CollectionName = "ItCanReadManuallyInsertedRecordAsync";
        // Arrange
        var sut = fixture.GetCollection<int, PostgresHotel<int>>(CollectionName);
        await sut.CreateCollectionAsync().ConfigureAwait(true);
        Assert.True(await sut.CollectionExistsAsync().ConfigureAwait(true));
        await using (var connection = fixture.GetConnection())
        {
            using NpgsqlCommand cmd = connection.CreateCommand();
            cmd.CommandText = @$"
                INSERT INTO public.""{CollectionName}"" (
                    ""HotelId"", ""HotelName"", ""HotelCode"", ""HotelRating"", ""parking_is_included"", ""Tags"", ""Description"", ""DescriptionEmbedding""
                ) VALUES (
                    215, 'Divine Lorraine', 215, 5, false, ARRAY['historic', 'philly'], 'An iconic building on broad street', '[10,20,30,40]'
                );";
            await cmd.ExecuteNonQueryAsync().ConfigureAwait(true);
        }

        // Act
        var getResult = await sut.GetAsync(215, new GetRecordOptions { IncludeVectors = true });

        // Assert
        Assert.NotNull(getResult);
        Assert.Equal(215, getResult!.HotelId);
        Assert.Equal("Divine Lorraine", getResult.HotelName);
        Assert.Equal(215, getResult.HotelCode);
        Assert.Equal(5, getResult.HotelRating);
        Assert.False(getResult.ParkingIncluded);
        Assert.Equal(new List<string> { "historic", "philly" }, getResult.Tags);
        Assert.Equal("An iconic building on broad street", getResult.Description);
        Assert.Equal([10f, 20f, 30f, 40f], getResult.DescriptionEmbedding!.Value.ToArray());
    }

    [Fact]
    public async Task ItCanUpsertAndRetrieveUsingTheDynamicMapperAsync()
    {
        const int HotelId = 5;

        var sut = fixture.GetCollection<object, Dictionary<string, object?>>("DynamicMapperWithNumericKey", GetVectorStoreRecordDefinition<int>());

        await sut.CreateCollectionAsync();

        var record = new PostgresHotel<int> { HotelId = (int)HotelId, HotelName = "Hotel 1", HotelCode = 1, ParkingIncluded = true, HotelRating = 4.5f, Tags = ["tag1", "tag2"] };

        // Act
        var upsertResult = await sut.UpsertAsync(new Dictionary<string, object?>
        {
            ["HotelId"] = HotelId,

            ["HotelName"] = "Dynamic Mapper Hotel",
            ["Description"] = "This is a dynamic mapper hotel",
            ["HotelCode"] = 1,
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
        Assert.Equal([30f, 31f, 32f, 33f], ((ReadOnlyMemory<float>)localGetResult["DescriptionEmbedding"]!).ToArray());

        // Act - update with null embeddings
        // Act
        var upsertResult2 = await sut.UpsertAsync(new Dictionary<string, object?>
        {
            ["HotelId"] = HotelId,

            ["HotelName"] = "Dynamic Mapper Hotel",
            ["Description"] = "This is a dynamic mapper hotel",
            ["HotelCode"] = 1,
            ["ParkingIncluded"] = true,
            ["HotelRating"] = 3.6f,

            ["DescriptionEmbedding"] = null
        });

        var localGetResult2 = await sut.GetAsync(HotelId, new GetRecordOptions { IncludeVectors = true });

        // Assert
        Assert.NotNull(localGetResult2);
        Assert.Null(localGetResult2["DescriptionEmbedding"]);
    }

    [Theory]
    [InlineData(true, DistanceFunction.CosineDistance)]
    [InlineData(false, DistanceFunction.CosineDistance)]
    [InlineData(false, DistanceFunction.CosineSimilarity)]
    [InlineData(false, DistanceFunction.EuclideanDistance)]
    [InlineData(false, DistanceFunction.ManhattanDistance)]
    [InlineData(false, DistanceFunction.DotProductSimilarity)]
    public async Task VectorizedSearchReturnsValidResultsByDefaultAsync(bool includeVectors, string distanceFunction)
    {
        // Arrange
        var hotel1 = new PostgresHotel<int> { HotelId = 1, HotelName = "Hotel 1", HotelCode = 1, ParkingIncluded = true, HotelRating = 4.5f, Tags = ["tag1", "tag2"], DescriptionEmbedding = new[] { 1f, 0f, 0f, 0f } };
        var hotel2 = new PostgresHotel<int> { HotelId = 2, HotelName = "Hotel 2", HotelCode = 2, ParkingIncluded = false, HotelRating = 2.5f, Tags = ["tag1", "tag3"], DescriptionEmbedding = new[] { 0f, 1f, 0f, 0f } };
        var hotel3 = new PostgresHotel<int> { HotelId = 3, HotelName = "Hotel 3", HotelCode = 3, ParkingIncluded = true, HotelRating = 3.5f, Tags = ["tag1", "tag4"], DescriptionEmbedding = new[] { 0f, 0f, 1f, 0f } };
        var hotel4 = new PostgresHotel<int> { HotelId = 4, HotelName = "Hotel 4", HotelCode = 4, ParkingIncluded = false, HotelRating = 1.5f, Tags = ["tag1", "tag5"], DescriptionEmbedding = new[] { 0f, 0f, 0f, 1f } };

        var sut = fixture.GetCollection<int, PostgresHotel<int>>($"VectorizedSearch_{includeVectors}_{distanceFunction}", GetVectorStoreRecordDefinition<int>(distanceFunction));

        await sut.CreateCollectionAsync();

        await sut.UpsertAsync([hotel4, hotel2, hotel3, hotel1]);

        // Act
        var results = await sut.VectorizedSearchAsync(new ReadOnlyMemory<float>([0.9f, 0.1f, 0.5f, 0.8f]), top: 3, new()
        {
            IncludeVectors = includeVectors
        }).ToListAsync();

        // Assert
        var ids = results.Select(l => l.Record.HotelId).ToList();

        Assert.Equal(1, ids[0]);
        Assert.Equal(4, ids[1]);
        Assert.Equal(3, ids[2]);

        // Default limit is 3
        Assert.DoesNotContain(2, ids);

        Assert.True(0 < results.First(l => l.Record.HotelId == 1).Score);

        Assert.Equal(includeVectors, results.All(result => result.Record.DescriptionEmbedding is not null));
    }

    [Fact]
    public async Task VectorizedSearchWithEqualToFilterReturnsValidResultsAsync()
    {
        // Arrange
        var hotel1 = new PostgresHotel<int> { HotelId = 1, HotelName = "Hotel 1", HotelCode = 1, ParkingIncluded = true, HotelRating = 2.5f, Tags = ["tag1", "tag2"], DescriptionEmbedding = new[] { 30f, 31f, 32f, 33f } };
        var hotel2 = new PostgresHotel<int> { HotelId = 2, HotelName = "Hotel 2", HotelCode = 2, ParkingIncluded = false, HotelRating = 2.5f, Tags = ["tag1", "tag3"], DescriptionEmbedding = new[] { 10f, 10f, 10f, 10f } };
        var hotel3 = new PostgresHotel<int> { HotelId = 3, HotelName = "Hotel 3", HotelCode = 3, ParkingIncluded = true, HotelRating = 2.5f, Tags = ["tag1", "tag4"], DescriptionEmbedding = new[] { 20f, 20f, 20f, 20f } };
        var hotel4 = new PostgresHotel<int> { HotelId = 4, HotelName = "Hotel 4", HotelCode = 4, ParkingIncluded = false, HotelRating = 3.5f, Tags = ["tag1", "tag5"], DescriptionEmbedding = new[] { 40f, 40f, 40f, 40f } };

        var sut = fixture.GetCollection<int, PostgresHotel<int>>("VectorizedSearchWithEqualToFilter");

        await sut.CreateCollectionAsync();

        await sut.UpsertAsync([hotel4, hotel2, hotel3, hotel1]);

        // Act
        var results = await sut.VectorizedSearchAsync(new ReadOnlyMemory<float>([30f, 29f, 28f, 27f]), top: 5, new()
        {
            IncludeVectors = false,
            OldFilter = new([
                new EqualToFilterClause("HotelRating", 2.5f)
            ])
        }).ToListAsync();

        // Assert
        var ids = results.Select(l => l.Record.HotelId).ToList();

        Assert.Equal([1, 3, 2], ids);
    }

    [Fact]
    public async Task VectorizedSearchWithAnyTagFilterReturnsValidResultsAsync()
    {
        // Arrange
        var hotel1 = new PostgresHotel<int> { HotelId = 1, HotelName = "Hotel 1", HotelCode = 1, ParkingIncluded = true, HotelRating = 2.5f, Tags = ["tag1", "tag2"], DescriptionEmbedding = new[] { 30f, 31f, 32f, 33f } };
        var hotel2 = new PostgresHotel<int> { HotelId = 2, HotelName = "Hotel 2", HotelCode = 2, ParkingIncluded = false, HotelRating = 2.5f, Tags = ["tag1", "tag3"], DescriptionEmbedding = new[] { 10f, 10f, 10f, 10f } };
        var hotel3 = new PostgresHotel<int> { HotelId = 3, HotelName = "Hotel 3", HotelCode = 3, ParkingIncluded = true, HotelRating = 2.5f, Tags = ["tag2", "tag4"], DescriptionEmbedding = new[] { 20f, 20f, 20f, 20f } };
        var hotel4 = new PostgresHotel<int> { HotelId = 4, HotelName = "Hotel 4", HotelCode = 4, ParkingIncluded = false, HotelRating = 3.5f, Tags = ["tag1", "tag5"], DescriptionEmbedding = new[] { 40f, 40f, 40f, 40f } };

        var sut = fixture.GetCollection<int, PostgresHotel<int>>("VectorizedSearchWithAnyTagEqualToFilter");

        await sut.CreateCollectionAsync();

        await sut.UpsertAsync([hotel4, hotel2, hotel3, hotel1]);

        // Act
        var results = await sut.VectorizedSearchAsync(new ReadOnlyMemory<float>([30f, 29f, 28f, 27f]), top: 5, new()
        {
            IncludeVectors = false,
            OldFilter = new([
                new AnyTagEqualToFilterClause("Tags", "tag2")
            ])
        }).ToListAsync();

        // Assert
        var ids = results.Select(l => l.Record.HotelId).ToList();

        Assert.Equal([1, 3], ids);
    }

    [Fact]
    public async Task ItCanUpsertAndGetEnumerableTypesAsync()
    {
        // Arrange
        var sut = fixture.GetCollection<int, RecordWithEnumerables>("UpsertAndGetEnumerableTypes");

        await sut.CreateCollectionAsync();

        var record = new RecordWithEnumerables
        {
            Id = 1,
            ListInts = new() { 1, 2, 3 },
            CollectionInts = new HashSet<int>() { 4, 5, 6 },
            EnumerableInts = [7, 8, 9],
            ReadOnlyCollectionInts = new List<int> { 10, 11, 12 },
            ReadOnlyListInts = new List<int> { 13, 14, 15 }
        };

        // Act
        await sut.UpsertAsync(record);

        var getResult = await sut.GetAsync(1);

        // Assert
        Assert.NotNull(getResult);
        Assert.Equal(1, getResult!.Id);
        Assert.NotNull(getResult.ListInts);
        Assert.Equal(3, getResult.ListInts!.Count);
        Assert.Equal(1, getResult.ListInts![0]);
        Assert.Equal(2, getResult.ListInts![1]);
        Assert.Equal(3, getResult.ListInts![2]);
        Assert.NotNull(getResult.CollectionInts);
        Assert.Equal(3, getResult.CollectionInts!.Count);
        Assert.Contains(4, getResult.CollectionInts);
        Assert.Contains(5, getResult.CollectionInts);
        Assert.Contains(6, getResult.CollectionInts);
        Assert.NotNull(getResult.EnumerableInts);
        Assert.Equal(3, getResult.EnumerableInts!.Count());
        Assert.Equal(7, getResult.EnumerableInts.ElementAt(0));
        Assert.Equal(8, getResult.EnumerableInts.ElementAt(1));
        Assert.Equal(9, getResult.EnumerableInts.ElementAt(2));
        Assert.NotNull(getResult.ReadOnlyCollectionInts);
        Assert.Equal(3, getResult.ReadOnlyCollectionInts!.Count);
        var readOnlyCollectionIntsList = getResult.ReadOnlyCollectionInts.ToList();
        Assert.Equal(10, readOnlyCollectionIntsList[0]);
        Assert.Equal(11, readOnlyCollectionIntsList[1]);
        Assert.Equal(12, readOnlyCollectionIntsList[2]);
        Assert.NotNull(getResult.ReadOnlyListInts);
        Assert.Equal(3, getResult.ReadOnlyListInts!.Count);
        Assert.Equal(13, getResult.ReadOnlyListInts[0]);
        Assert.Equal(14, getResult.ReadOnlyListInts[1]);
        Assert.Equal(15, getResult.ReadOnlyListInts[2]);
    }

    #region private ==================================================================================

    private static VectorStoreRecordDefinition GetVectorStoreRecordDefinition<TKey>(string distanceFunction = DistanceFunction.CosineDistance) => new()
    {
        Properties =
        [
            new VectorStoreRecordKeyProperty("HotelId", typeof(TKey)),
            new VectorStoreRecordDataProperty("HotelName", typeof(string)),
            new VectorStoreRecordDataProperty("HotelCode", typeof(int)),
            new VectorStoreRecordDataProperty("HotelRating", typeof(float?)),
            new VectorStoreRecordDataProperty("ParkingIncluded", typeof(bool)) { StoragePropertyName = "parking_is_included" },
            new VectorStoreRecordDataProperty("Tags", typeof(List<string>)),
            new VectorStoreRecordDataProperty("ListInts", typeof(List<int>)),
            new VectorStoreRecordDataProperty("Description", typeof(string)),
            new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?), 4) { IndexKind = IndexKind.Hnsw, DistanceFunction = distanceFunction }
        ]
    };

    private dynamic GetCollection(Type idType, string collectionName)
    {
        var method = typeof(PostgresVectorStoreFixture).GetMethod("GetCollection");
        var genericMethod = method!.MakeGenericMethod(idType, typeof(PostgresHotel<>).MakeGenericType(idType));
        return genericMethod.Invoke(fixture, [collectionName, null])!;
    }

    private PostgresHotel<TKey> CreateRecord<TKey>(Type idType, TKey key)
    {
        var recordType = typeof(PostgresHotel<>).MakeGenericType(idType);
        var record = (PostgresHotel<TKey>)Activator.CreateInstance(recordType, key)!;
        record.HotelName = "Hotel 1";
        record.HotelCode = 1;
        record.ParkingIncluded = true;
        record.HotelRating = 4.5f;
        record.Tags = new List<string> { "tag1", "tag2" };
        return record;
    }
    private static DateTime TruncateMilliseconds(DateTime dateTime)
    {
        return new DateTime(dateTime.Ticks - (dateTime.Ticks % TimeSpan.TicksPerSecond), dateTime.Kind);
    }

    private static DateTimeOffset TruncateMilliseconds(DateTimeOffset dateTimeOffset)
    {
        return new DateTimeOffset(dateTimeOffset.Ticks - (dateTimeOffset.Ticks % TimeSpan.TicksPerSecond), dateTimeOffset.Offset);
    }

#pragma warning disable CA1812, CA1859
    private sealed class RecordWithEnumerables
    {
        [VectorStoreRecordKey]
        public int Id { get; set; }

        [VectorStoreRecordVector(Dimensions: 4, DistanceFunction = DistanceFunction.CosineDistance)]
        public ReadOnlyMemory<float>? Embedding { get; set; }

        [VectorStoreRecordData]
        public List<int>? ListInts { get; set; }

        [VectorStoreRecordData]
        public ICollection<int>? CollectionInts { get; set; }

        [VectorStoreRecordData]
        public IEnumerable<int>? EnumerableInts { get; set; }

        [VectorStoreRecordData]
        public IReadOnlyCollection<int>? ReadOnlyCollectionInts { get; set; }

        [VectorStoreRecordData]
        public IReadOnlyList<int>? ReadOnlyListInts { get; set; }
    }
#pragma warning restore CA1812, CA1859

    #endregion

}
