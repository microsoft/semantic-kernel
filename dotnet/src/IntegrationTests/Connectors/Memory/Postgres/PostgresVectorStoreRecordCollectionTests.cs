// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Postgres;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Postgres;

[Collection("PostgresVectorStoreCollection")]
public sealed class PostgresVectorStoreRecordCollectionTests(PostgresVectorStoreFixture fixture)
{
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CollectionExistsReturnsCollectionStateAsync(bool createCollection)
    {
        // Arrange
        var sut = fixture.GetCollection<int, PostgresHotel>("CollectionExists");

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
    public async Task CollectionCanUpsertAndGetAsync()
    {
        // Arrange
        var sut = fixture.GetCollection<int, PostgresHotel>("CollectionCanUpsertAndGet");
        if (await sut.CollectionExistsAsync())
        {
            await sut.DeleteCollectionAsync();
        }

        await sut.CreateCollectionAsync();

        try
        {
            // Act
            await sut.UpsertAsync(new PostgresHotel { HotelId = 1, HotelName = "Hotel 1", HotelCode = 1, ParkingIncluded = true, HotelRating = 4.5f, Tags = ["tag1", "tag2"] });
            await sut.UpsertAsync(new PostgresHotel { HotelId = 2, HotelName = "Hotel 2", HotelCode = 2, ParkingIncluded = false, HotelRating = 2.5f, ListInts = [1, 2] });

            var hotel1 = await sut.GetAsync(1);
            var hotel2 = await sut.GetAsync(2);

            // Assert
            Assert.NotNull(hotel1);
            Assert.Equal(1, hotel1!.HotelId);
            Assert.Equal("Hotel 1", hotel1!.HotelName);
            Assert.Equal(1, hotel1!.HotelCode);
            Assert.True(hotel1!.ParkingIncluded);
            Assert.Equal(4.5f, hotel1!.HotelRating);
            Assert.NotNull(hotel1!.Tags);
            Assert.Equal(2, hotel1!.Tags!.Count);
            Assert.Equal("tag1", hotel1!.Tags![0]);
            Assert.Equal("tag2", hotel1!.Tags![1]);
            Assert.Null(hotel1!.ListInts);

            Assert.NotNull(hotel2);
            Assert.Equal(2, hotel2!.HotelId);
            Assert.Equal("Hotel 2", hotel2!.HotelName);
            Assert.Equal(2, hotel2!.HotelCode);
            Assert.False(hotel2!.ParkingIncluded);
            Assert.Equal(2.5f, hotel2!.HotelRating);
            Assert.NotNull(hotel2!.Tags);
            Assert.Empty(hotel2!.Tags);
            Assert.NotNull(hotel2!.ListInts);
            Assert.Equal(2, hotel2!.ListInts!.Count);
            Assert.Equal(1, hotel2!.ListInts![0]);
            Assert.Equal(2, hotel2!.ListInts![1]);
        }
        finally
        {
            // Cleanup
            await sut.DeleteCollectionAsync();
        }
    }

    [Fact]
    public async Task ItCanGetAndDeleteRecordAsync()
    {
        // Arrange
        const int HotelId = 5;
        var sut = fixture.GetCollection<int, PostgresHotel>("DeleteRecord");

        await sut.CreateCollectionAsync();

        try
        {
            var record = new PostgresHotel { HotelId = HotelId, HotelName = "Hotel 1", HotelCode = 1, ParkingIncluded = true, HotelRating = 4.5f, Tags = ["tag1", "tag2"] };

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

        var sut = fixture.GetCollection<int, PostgresHotel>("GetUpsertDeleteBatch");

        await sut.CreateCollectionAsync();

        var record1 = new PostgresHotel { HotelId = HotelId1, HotelName = "Hotel 1", HotelCode = 1, ParkingIncluded = true, HotelRating = 4.5f, Tags = ["tag1", "tag2"] };
        var record2 = new PostgresHotel { HotelId = HotelId2, HotelName = "Hotel 2", HotelCode = 1, ParkingIncluded = false, HotelRating = 3.5f, Tags = ["tag1", "tag3"] };
        var record3 = new PostgresHotel { HotelId = HotelId3, HotelName = "Hotel 3", HotelCode = 1, ParkingIncluded = true, HotelRating = 2.5f, Tags = ["tag1", "tag4"] };

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

    [Fact]
    public async Task ItCanUpsertExistingRecordAsync()
    {
        // Arrange
        const int HotelId = 5;
        var sut = fixture.GetCollection<int, PostgresHotel>("UpsertRecord");

        await sut.CreateCollectionAsync();

        var record = new PostgresHotel { HotelId = HotelId, HotelName = "Hotel 1", HotelCode = 1, ParkingIncluded = true, HotelRating = 4.5f, Tags = ["tag1", "tag2"] };

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
    public async Task ItCanUpsertAndRetrieveUsingTheGenericMapperAsync()
    {
        const int HotelId = 5;

        var options = new PostgresVectorStoreRecordCollectionOptions<VectorStoreGenericDataModel<int>>
        {
            VectorStoreRecordDefinition = GetVectorStoreRecordDefinition<int>()
        };

        var sut = fixture.GetCollection<int, VectorStoreGenericDataModel<int>>("GenericMapperWithNumericKey", options);

        await sut.CreateCollectionAsync();

        var record = new PostgresHotel { HotelId = (int)HotelId, HotelName = "Hotel 1", HotelCode = 1, ParkingIncluded = true, HotelRating = 4.5f, Tags = ["tag1", "tag2"] };

        // Act
        var upsertResult = await sut.UpsertAsync(new VectorStoreGenericDataModel<int>(HotelId)
        {
            Data =
            {
                { "HotelName", "Generic Mapper Hotel" },
                { "Description", "This is a generic mapper hotel" },
                { "HotelCode", 1 },
                { "ParkingIncluded", true },
                { "HotelRating", 3.6f }
            },
            Vectors =
            {
                { "DescriptionEmbedding", new ReadOnlyMemory<float>([30f, 31f, 32f, 33f]) }
            }
        });

        var localGetResult = await sut.GetAsync(HotelId, new GetRecordOptions { IncludeVectors = true });

        // Assert
        Assert.Equal(HotelId, upsertResult);

        Assert.NotNull(localGetResult);
        Assert.Equal("Generic Mapper Hotel", localGetResult.Data["HotelName"]);
        Assert.Equal("This is a generic mapper hotel", localGetResult.Data["Description"]);
        Assert.True((bool?)localGetResult.Data["ParkingIncluded"]);
        Assert.Equal(3.6f, localGetResult.Data["HotelRating"]);
        Assert.Equal([30f, 31f, 32f, 33f], ((ReadOnlyMemory<float>)localGetResult.Vectors["DescriptionEmbedding"]!).ToArray());

        // Act - update with null embeddings
        // Act
        var upsertResult2 = await sut.UpsertAsync(new VectorStoreGenericDataModel<int>(HotelId)
        {
            Data =
            {
                { "HotelName", "Generic Mapper Hotel" },
                { "Description", "This is a generic mapper hotel" },
                { "HotelCode", 1 },
                { "ParkingIncluded", true },
                { "HotelRating", 3.6f }
            },
            Vectors =
            {
                { "DescriptionEmbedding", null }
            }
        });

        var localGetResult2 = await sut.GetAsync(HotelId, new GetRecordOptions { IncludeVectors = true });

        // Assert
        Assert.NotNull(localGetResult2);
        Assert.Null(localGetResult2.Vectors["DescriptionEmbedding"]);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task VectorizedSearchReturnsValidResultsByDefaultAsync(bool includeVectors)
    {
        // Arrange
        var hotel1 = new PostgresHotel { HotelId = 1, HotelName = "Hotel 1", HotelCode = 1, ParkingIncluded = true, HotelRating = 4.5f, Tags = ["tag1", "tag2"], DescriptionEmbedding = new[] { 30f, 31f, 32f, 33f } };
        var hotel2 = new PostgresHotel { HotelId = 2, HotelName = "Hotel 2", HotelCode = 2, ParkingIncluded = false, HotelRating = 2.5f, Tags = ["tag1", "tag3"], DescriptionEmbedding = new[] { 10f, 10f, 10f, 10f } };
        var hotel3 = new PostgresHotel { HotelId = 3, HotelName = "Hotel 3", HotelCode = 3, ParkingIncluded = true, HotelRating = 3.5f, Tags = ["tag1", "tag4"], DescriptionEmbedding = new[] { 20f, 20f, 20f, 20f } };
        var hotel4 = new PostgresHotel { HotelId = 4, HotelName = "Hotel 4", HotelCode = 4, ParkingIncluded = false, HotelRating = 1.5f, Tags = ["tag1", "tag5"], DescriptionEmbedding = new[] { 40f, 40f, 40f, 40f } };

        var sut = fixture.GetCollection<int, PostgresHotel>($"VectorizedSearch_{includeVectors}");

        await sut.CreateCollectionAsync();

        await sut.UpsertBatchAsync([hotel4, hotel2, hotel3, hotel1]).ToListAsync();

        // Act
        var searchResults = await sut.VectorizedSearchAsync(new ReadOnlyMemory<float>([30f, 31f, 32f, 33f]), new()
        {
            IncludeVectors = includeVectors
        });

        var results = await searchResults.Results.ToListAsync();

        // Assert
        var ids = results.Select(l => l.Record.HotelId).ToList();

        Assert.Equal(1, ids[0]);
        Assert.Equal(4, ids[1]);
        Assert.Equal(3, ids[2]);

        // Default limit is 3
        Assert.DoesNotContain(2, ids);

        Assert.Equal(0, results.First(l => l.Record.HotelId == 1).Score);

        Assert.Equal(includeVectors, results.All(result => result.Record.DescriptionEmbedding is not null));
    }

    [Fact]
    public async Task VectorizedSearchWithEqualToFilterReturnsValidResultsAsync()
    {
        // Arrange
        var hotel1 = new PostgresHotel { HotelId = 1, HotelName = "Hotel 1", HotelCode = 1, ParkingIncluded = true, HotelRating = 2.5f, Tags = ["tag1", "tag2"], DescriptionEmbedding = new[] { 30f, 31f, 32f, 33f } };
        var hotel2 = new PostgresHotel { HotelId = 2, HotelName = "Hotel 2", HotelCode = 2, ParkingIncluded = false, HotelRating = 2.5f, Tags = ["tag1", "tag3"], DescriptionEmbedding = new[] { 10f, 10f, 10f, 10f } };
        var hotel3 = new PostgresHotel { HotelId = 3, HotelName = "Hotel 3", HotelCode = 3, ParkingIncluded = true, HotelRating = 2.5f, Tags = ["tag1", "tag4"], DescriptionEmbedding = new[] { 20f, 20f, 20f, 20f } };
        var hotel4 = new PostgresHotel { HotelId = 4, HotelName = "Hotel 4", HotelCode = 4, ParkingIncluded = false, HotelRating = 3.5f, Tags = ["tag1", "tag5"], DescriptionEmbedding = new[] { 40f, 40f, 40f, 40f } };

        var sut = fixture.GetCollection<int, PostgresHotel>("VectorizedSearchWithEqualToFilter");

        await sut.CreateCollectionAsync();

        await sut.UpsertBatchAsync([hotel4, hotel2, hotel3, hotel1]).ToListAsync();

        // Act
        var searchResults = await sut.VectorizedSearchAsync(new ReadOnlyMemory<float>([30f, 29f, 28f, 27f]), new()
        {
            IncludeVectors = false,
            Top = 5,
            Filter = new([
                new EqualToFilterClause("HotelRating", 2.5f)
            ])
        });

        var results = await searchResults.Results.ToListAsync();

        // Assert
        var ids = results.Select(l => l.Record.HotelId).ToList();

        Assert.Equal([1, 3, 2], ids);
    }

    [Fact]
    public async Task VectorizedSearchWithAnyTagFilterReturnsValidResultsAsync()
    {
        // Arrange
        var hotel1 = new PostgresHotel { HotelId = 1, HotelName = "Hotel 1", HotelCode = 1, ParkingIncluded = true, HotelRating = 2.5f, Tags = ["tag1", "tag2"], DescriptionEmbedding = new[] { 30f, 31f, 32f, 33f } };
        var hotel2 = new PostgresHotel { HotelId = 2, HotelName = "Hotel 2", HotelCode = 2, ParkingIncluded = false, HotelRating = 2.5f, Tags = ["tag1", "tag3"], DescriptionEmbedding = new[] { 10f, 10f, 10f, 10f } };
        var hotel3 = new PostgresHotel { HotelId = 3, HotelName = "Hotel 3", HotelCode = 3, ParkingIncluded = true, HotelRating = 2.5f, Tags = ["tag2", "tag4"], DescriptionEmbedding = new[] { 20f, 20f, 20f, 20f } };
        var hotel4 = new PostgresHotel { HotelId = 4, HotelName = "Hotel 4", HotelCode = 4, ParkingIncluded = false, HotelRating = 3.5f, Tags = ["tag1", "tag5"], DescriptionEmbedding = new[] { 40f, 40f, 40f, 40f } };

        var sut = fixture.GetCollection<int, PostgresHotel>("VectorizedSearchWithEqualToFilter");

        await sut.CreateCollectionAsync();

        await sut.UpsertBatchAsync([hotel4, hotel2, hotel3, hotel1]).ToListAsync();

        // Act
        var searchResults = await sut.VectorizedSearchAsync(new ReadOnlyMemory<float>([30f, 29f, 28f, 27f]), new()
        {
            IncludeVectors = false,
            Top = 5,
            Filter = new([
                new AnyTagEqualToFilterClause("Tags", "tag2")
            ])
        });

        var results = await searchResults.Results.ToListAsync();

        // Assert
        var ids = results.Select(l => l.Record.HotelId).ToList();

        Assert.Equal([1, 3], ids);
    }

    #region private ==================================================================================

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
            new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?)) { Dimensions = 4, IndexKind = IndexKind.IvfFlat, DistanceFunction = DistanceFunction.CosineDistance }
        ]
    };

    #endregion

}