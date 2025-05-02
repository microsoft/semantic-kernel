// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Weaviate;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Weaviate;

#pragma warning disable CS0618 // VectorSearchFilter is obsolete

[Collection("WeaviateVectorStoreCollection")]
public sealed class WeaviateVectorStoreRecordCollectionTests(WeaviateVectorStoreFixture fixture)
{
    private const string SkipReason = "Weaviate tests are failing on the build server with connection reset errors, but passing locally.";

    [Fact(Skip = SkipReason)]
    public async Task ItCanCreateCollectionAsync()
    {
        // Arrange
        var sut = new WeaviateVectorStoreRecordCollection<Guid, WeaviateHotel>(fixture.HttpClient!, "TestCreateCollection");

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
        var sut = new WeaviateVectorStoreRecordCollection<Guid, WeaviateHotel>(fixture.HttpClient!, collectionName);

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

        var sut = new WeaviateVectorStoreRecordCollection<Guid, WeaviateHotel>(fixture.HttpClient!, collectionName, options);

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

        var sut = new WeaviateVectorStoreRecordCollection<Guid, WeaviateHotel>(fixture.HttpClient!, CollectionName);

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

        var sut = new WeaviateVectorStoreRecordCollection<Guid, WeaviateHotel>(fixture.HttpClient!, "TestDeleteRecord");

        await sut.CreateCollectionAsync();

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

        var sut = new WeaviateVectorStoreRecordCollection<Guid, WeaviateHotel>(fixture.HttpClient!, "TestBatch");

        await sut.CreateCollectionAsync();

        var record1 = this.CreateTestHotel(hotelId1);
        var record2 = this.CreateTestHotel(hotelId2);
        var record3 = this.CreateTestHotel(hotelId3);

        var upsertResults = await sut.UpsertAsync([record1, record2, record3]);
        var getResults = await sut.GetAsync([hotelId1, hotelId2, hotelId3]).ToListAsync();

        Assert.Equal([hotelId1, hotelId2, hotelId3], upsertResults);

        Assert.NotNull(getResults.First(l => l.HotelId == hotelId1));
        Assert.NotNull(getResults.First(l => l.HotelId == hotelId2));
        Assert.NotNull(getResults.First(l => l.HotelId == hotelId3));

        // Act
        await sut.DeleteAsync([hotelId1, hotelId2, hotelId3]);

        getResults = await sut.GetAsync([hotelId1, hotelId2, hotelId3]).ToListAsync();

        // Assert
        Assert.Empty(getResults);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanUpsertRecordAsync()
    {
        // Arrange
        var hotelId = new Guid("55555555-5555-5555-5555-555555555555");
        var sut = new WeaviateVectorStoreRecordCollection<Guid, WeaviateHotel>(fixture.HttpClient!, "TestUpsert");

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

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task VectorizedSearchReturnsValidResultsByDefaultAsync(bool includeVectors)
    {
        // Arrange
        var hotel1 = this.CreateTestHotel(hotelId: new Guid("11111111-1111-1111-1111-111111111111"), embedding: new[] { 30f, 31f, 32f, 33f });
        var hotel2 = this.CreateTestHotel(hotelId: new Guid("22222222-2222-2222-2222-222222222222"), embedding: new[] { 31f, 32f, 33f, 34f });
        var hotel3 = this.CreateTestHotel(hotelId: new Guid("33333333-3333-3333-3333-333333333333"), embedding: new[] { 20f, 20f, 20f, 20f });
        var hotel4 = this.CreateTestHotel(hotelId: new Guid("44444444-4444-4444-4444-444444444444"), embedding: new[] { -1000f, -1000f, -1000f, -1000f });

        var sut = new WeaviateVectorStoreRecordCollection<Guid, WeaviateHotel>(fixture.HttpClient!, "VectorSearchDefault");

        await sut.CreateCollectionIfNotExistsAsync();

        await sut.UpsertAsync([hotel4, hotel2, hotel3, hotel1]);

        // Act
        var searchResults = await sut.VectorizedSearchAsync(new ReadOnlyMemory<float>([30f, 31f, 32f, 33f]), top: 3, new()
        {
            IncludeVectors = includeVectors
        }).ToListAsync();

        // Assert
        var ids = searchResults.Select(l => l.Record.HotelId.ToString()).ToList();

        Assert.Equal("11111111-1111-1111-1111-111111111111", ids[0]);
        Assert.Equal("22222222-2222-2222-2222-222222222222", ids[1]);
        Assert.Equal("33333333-3333-3333-3333-333333333333", ids[2]);

        Assert.DoesNotContain("44444444-4444-4444-4444-444444444444", ids);

        Assert.True(
            searchResults[0].Score < searchResults[1].Score &&
            searchResults[1].Score < searchResults[2].Score);

        Assert.Equal(includeVectors, searchResults.All(l => l.Record.DescriptionEmbedding is not null));
    }

    [Fact(Skip = SkipReason)]
    public async Task VectorizedSearchReturnsValidResultsWithOffsetAsync()
    {
        // Arrange
        var hotel1 = this.CreateTestHotel(hotelId: new Guid("11111111-1111-1111-1111-111111111111"), embedding: new[] { 30f, 31f, 32f, 33f });
        var hotel2 = this.CreateTestHotel(hotelId: new Guid("22222222-2222-2222-2222-222222222222"), embedding: new[] { 31f, 32f, 33f, 34f });
        var hotel3 = this.CreateTestHotel(hotelId: new Guid("33333333-3333-3333-3333-333333333333"), embedding: new[] { 20f, 20f, 20f, 20f });
        var hotel4 = this.CreateTestHotel(hotelId: new Guid("44444444-4444-4444-4444-444444444444"), embedding: new[] { -1000f, -1000f, -1000f, -1000f });

        var sut = new WeaviateVectorStoreRecordCollection<Guid, WeaviateHotel>(fixture.HttpClient!, "VectorSearchWithOffset");

        await sut.CreateCollectionIfNotExistsAsync();

        await sut.UpsertAsync([hotel4, hotel2, hotel3, hotel1]);

        // Act
        var searchResults = await sut.VectorizedSearchAsync(new ReadOnlyMemory<float>([30f, 31f, 32f, 33f]), top: 2, new()
        {
            Skip = 2
        }).ToListAsync();

        // Assert
        var ids = searchResults.Select(l => l.Record.HotelId.ToString()).ToList();

        Assert.Equal("33333333-3333-3333-3333-333333333333", ids[0]);
        Assert.Equal("44444444-4444-4444-4444-444444444444", ids[1]);

        Assert.DoesNotContain("11111111-1111-1111-1111-111111111111", ids);
        Assert.DoesNotContain("22222222-2222-2222-2222-222222222222", ids);
    }

    [Theory(Skip = SkipReason)]
    [MemberData(nameof(VectorizedSearchWithFilterData))]
    public async Task VectorizedSearchReturnsValidResultsWithFilterAsync(VectorSearchFilter filter, List<string> expectedIds)
    {
        // Arrange
        var hotel1 = this.CreateTestHotel(hotelId: new Guid("11111111-1111-1111-1111-111111111111"), embedding: new[] { 30f, 31f, 32f, 33f });
        var hotel2 = this.CreateTestHotel(hotelId: new Guid("22222222-2222-2222-2222-222222222222"), embedding: new[] { 31f, 32f, 33f, 34f });
        var hotel3 = this.CreateTestHotel(hotelId: new Guid("33333333-3333-3333-3333-333333333333"), embedding: new[] { 20f, 20f, 20f, 20f });
        var hotel4 = this.CreateTestHotel(hotelId: new Guid("44444444-4444-4444-4444-444444444444"), embedding: new[] { -1000f, -1000f, -1000f, -1000f });

        var sut = new WeaviateVectorStoreRecordCollection<Guid, WeaviateHotel>(fixture.HttpClient!, "VectorSearchWithFilter");

        await sut.CreateCollectionIfNotExistsAsync();

        await sut.UpsertAsync([hotel4, hotel2, hotel3, hotel1]);

        // Act
        var searchResults = await sut.VectorizedSearchAsync(new ReadOnlyMemory<float>([30f, 31f, 32f, 33f]), top: 4, new()
        {
            OldFilter = filter,
        }).ToListAsync();

        // Assert
        var actualIds = searchResults.Select(l => l.Record.HotelId.ToString()).ToList();

        Assert.Equal(expectedIds, actualIds);
    }

    [Theory(Skip = SkipReason)]
    [MemberData(nameof(VectorizedSearchWithFilterAndDifferentDataTypesData))]
    public async Task VectorizedSearchReturnsValidResultsWithFilterAndDifferentDataTypesAsync(VectorSearchFilter filter)
    {
        // Arrange
        var expectedId = "55555555-5555-5555-5555-555555555555";

        var hotel1 = this.CreateTestHotel(hotelId: new Guid("11111111-1111-1111-1111-111111111111"), embedding: new[] { 30f, 31f, 32f, 33f });
        var hotel2 = this.CreateTestHotel(hotelId: new Guid("22222222-2222-2222-2222-222222222222"), embedding: new[] { 31f, 32f, 33f, 34f });
        var hotel3 = this.CreateTestHotel(hotelId: new Guid("33333333-3333-3333-3333-333333333333"), embedding: new[] { 20f, 20f, 20f, 20f });
        var hotel4 = this.CreateTestHotel(hotelId: new Guid("44444444-4444-4444-4444-444444444444"), embedding: new[] { -1000f, -1000f, -1000f, -1000f });

        var hotel5 = new WeaviateHotel
        {
            HotelId = new Guid("55555555-5555-5555-5555-555555555555"),
            HotelName = "Test hotel name",
            HotelCode = 88,
            HotelRating = 7.9f,
            ParkingIncluded = false,
            Tags = { "tag1", "tag2" },
            Description = "Hotel description",
            DescriptionEmbedding = new[] { 40f, 40f, 40f, 40f },
            Timestamp = new DateTime(2024, 9, 22, 15, 59, 42)
        };

        var sut = new WeaviateVectorStoreRecordCollection<Guid, WeaviateHotel>(fixture.HttpClient!, "VectorSearchWithFilterAndDataTypes");

        await sut.CreateCollectionIfNotExistsAsync();

        await sut.UpsertAsync([hotel4, hotel2, hotel5, hotel3, hotel1]);

        // Act
        var searchResults = await sut.VectorizedSearchAsync(new ReadOnlyMemory<float>([40f, 40f, 40f, 40f]), top: 4, new()
        {
            OldFilter = filter,
        }).ToListAsync();

        // Assert
        var actualIds = searchResults.Select(l => l.Record.HotelId.ToString()).ToList();

        Assert.Single(actualIds);

        Assert.Equal(expectedId, actualIds[0]);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanUpsertAndRetrieveUsingDynamicMappingAsync()
    {
        // Arrange
        var hotelId = new Guid("55555555-5555-5555-5555-555555555555");
        var options = new WeaviateVectorStoreRecordCollectionOptions<Dictionary<string, object?>>
        {
            VectorStoreRecordDefinition = this.GetTestHotelRecordDefinition()
        };

        var sut = new WeaviateVectorStoreRecordCollection<object, Dictionary<string, object?>>(fixture.HttpClient!, "TestDynamicMapper", options);

        await sut.CreateCollectionAsync();

        // Act
        var upsertResult = await sut.UpsertAsync(new Dictionary<string, object?>
        {
            ["HotelId"] = hotelId,

            ["HotelName"] = "Dynamic Mapper Hotel",
            ["Description"] = "This is a dynamic mapper hotel",
            ["Tags"] = new List<string> { "dynamic" },
            ["ParkingIncluded"] = false,
            ["Timestamp"] = new DateTimeOffset(1970, 1, 18, 0, 0, 0, TimeSpan.Zero),
            ["HotelRating"] = 3.6f,

            ["DescriptionEmbedding"] = new ReadOnlyMemory<float>([30f, 31f, 32f, 33f])
        });

        var localGetResult = await sut.GetAsync(hotelId, new GetRecordOptions { IncludeVectors = true });

        // Assert
        Assert.Equal(hotelId, upsertResult);

        Assert.NotNull(localGetResult);
        Assert.Equal("Dynamic Mapper Hotel", localGetResult["HotelName"]);
        Assert.Equal("This is a dynamic mapper hotel", localGetResult["Description"]);
        Assert.Equal(new List<string> { "dynamic" }, localGetResult["Tags"]);
        Assert.False((bool?)localGetResult["ParkingIncluded"]);
        Assert.Equal(new DateTimeOffset(1970, 1, 18, 0, 0, 0, TimeSpan.Zero), localGetResult["Timestamp"]);
        Assert.Equal(3.6f, localGetResult["HotelRating"]);
        Assert.Equal(new[] { 30f, 31f, 32f, 33f }, ((ReadOnlyMemory<float>)localGetResult["DescriptionEmbedding"]!).ToArray());
    }

    public static TheoryData<VectorSearchFilter, List<string>> VectorizedSearchWithFilterData => new()
    {
        {
            new VectorSearchFilter().EqualTo(nameof(WeaviateHotel.HotelName), "My Hotel 22222222-2222-2222-2222-222222222222"),
            ["22222222-2222-2222-2222-222222222222"]
        },
        {
            new VectorSearchFilter().AnyTagEqualTo(nameof(WeaviateHotel.Tags), "t2"),
            [
                "11111111-1111-1111-1111-111111111111",
                "22222222-2222-2222-2222-222222222222",
                "33333333-3333-3333-3333-333333333333",
                "44444444-4444-4444-4444-444444444444"
            ]
        },
        {
            new VectorSearchFilter()
                .EqualTo(nameof(WeaviateHotel.HotelName), "My Hotel 22222222-2222-2222-2222-222222222222")
                .AnyTagEqualTo(nameof(WeaviateHotel.Tags), "t2"),
            ["22222222-2222-2222-2222-222222222222"]
        },
        {
            new VectorSearchFilter()
                .EqualTo(nameof(WeaviateHotel.HotelName), "non-existent-hotel")
                .AnyTagEqualTo(nameof(WeaviateHotel.Tags), "non-existent-tag"),
            []
        }
    };

    public static TheoryData<VectorSearchFilter> VectorizedSearchWithFilterAndDifferentDataTypesData => new()
    {
        { new VectorSearchFilter().EqualTo(nameof(WeaviateHotel.HotelId), new Guid("55555555-5555-5555-5555-555555555555")) },
        { new VectorSearchFilter().EqualTo(nameof(WeaviateHotel.HotelName), "Test hotel name") },
        { new VectorSearchFilter().EqualTo(nameof(WeaviateHotel.HotelCode), 88) },
        { new VectorSearchFilter().EqualTo(nameof(WeaviateHotel.HotelRating), 7.9f) },
        { new VectorSearchFilter().EqualTo(nameof(WeaviateHotel.ParkingIncluded), false) },
        { new VectorSearchFilter().EqualTo(nameof(WeaviateHotel.Timestamp), new DateTimeOffset(new DateTime(2024, 9, 22, 15, 59, 42))) }
    };

    #region private

    private WeaviateHotel CreateTestHotel(
        Guid hotelId,
        string? hotelName = null,
        ReadOnlyMemory<float>? embedding = null)
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
            DescriptionEmbedding = embedding ?? new[] { 30f, 31f, 32f, 33f },
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
                new VectorStoreRecordDataProperty("ParkingIncluded", typeof(bool)) { StoragePropertyName = "parking_is_included" },
                new VectorStoreRecordDataProperty("HotelRating", typeof(float)),
                new VectorStoreRecordDataProperty("Tags", typeof(List<string>)),
                new VectorStoreRecordDataProperty("Description", typeof(string)),
                new VectorStoreRecordDataProperty("Timestamp", typeof(DateTimeOffset)),
                new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?), 4) { IndexKind = IndexKind.Hnsw, DistanceFunction = DistanceFunction.CosineDistance }
            ]
        };
    }

    #endregion
}
