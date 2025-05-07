// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Redis;
using NRedisStack.RedisStackCommands;
using NRedisStack.Search;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Redis;

#pragma warning disable CS0618 // VectorSearchFilter is obsolete

/// <summary>
/// Contains tests for the <see cref="RedisHashSetVectorStoreRecordCollection{TKey, TRecord}"/> class.
/// </summary>
/// <param name="output">Used for logging.</param>
/// <param name="fixture">Redis setup and teardown.</param>
[Collection("RedisVectorStoreCollection")]
public sealed class RedisHashSetVectorStoreRecordCollectionTests(ITestOutputHelper output, RedisVectorStoreFixture fixture)
{
    // If null, all tests will be enabled
    private const string SkipReason = "Redis tests fail intermittently on build server";

    private const string TestCollectionName = "hashhotels";

    [Theory(Skip = SkipReason)]
    [InlineData(TestCollectionName, true)]
    [InlineData("nonexistentcollection", false)]
    public async Task CollectionExistsReturnsCollectionStateAsync(string collectionName, bool expectedExists)
    {
        // Arrange.
        var sut = new RedisHashSetVectorStoreRecordCollection<string, RedisBasicFloat32Hotel>(fixture.Database, collectionName);

        // Act.
        var actual = await sut.CollectionExistsAsync();

        // Assert.
        Assert.Equal(expectedExists, actual);
    }

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanCreateACollectionUpsertGetAndSearchAsync(bool useRecordDefinition)
    {
        // Arrange
        var record = CreateTestHotel("HUpsert-1", 1);
        var collectionNamePostfix = useRecordDefinition ? "WithDefinition" : "WithType";
        var testCollectionName = $"hashsetcreatetest{collectionNamePostfix}";

        var options = new RedisHashSetVectorStoreRecordCollectionOptions<RedisBasicFloat32Hotel>
        {
            PrefixCollectionNameToKeyNames = true,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.BasicVectorStoreRecordDefinition : null
        };
        var sut = new RedisHashSetVectorStoreRecordCollection<string, RedisBasicFloat32Hotel>(fixture.Database, testCollectionName, options);

        // Act
        await sut.CreateCollectionAsync();
        var upsertResult = await sut.UpsertAsync(record);
        var getResult = await sut.GetAsync("HUpsert-1", new GetRecordOptions { IncludeVectors = true });
        var searchResults = await sut
            .VectorizedSearchAsync(
                new ReadOnlyMemory<float>(new[] { 30f, 31f, 32f, 33f }),
                top: 3,
                new() { OldFilter = new VectorSearchFilter().EqualTo("HotelCode", 1), IncludeVectors = true }).ToListAsync();

        // Assert
        var collectionExistResult = await sut.CollectionExistsAsync();
        Assert.True(collectionExistResult);
        await sut.DeleteCollectionAsync();

        Assert.Equal("HUpsert-1", upsertResult);
        Assert.Equal(record.HotelId, getResult?.HotelId);
        Assert.Equal(record.HotelName, getResult?.HotelName);
        Assert.Equal(record.HotelCode, getResult?.HotelCode);
        Assert.Equal(record.ParkingIncluded, getResult?.ParkingIncluded);
        Assert.Equal(record.Rating, getResult?.Rating);
        Assert.Equal(record.Description, getResult?.Description);
        Assert.Equal(record.DescriptionEmbedding?.ToArray(), getResult?.DescriptionEmbedding?.ToArray());

        Assert.Single(searchResults);
        Assert.Equal(1, searchResults.First().Score);
        var searchResultRecord = searchResults.First().Record;
        Assert.Equal(record.HotelId, searchResultRecord?.HotelId);
        Assert.Equal(record.HotelName, searchResultRecord?.HotelName);
        Assert.Equal(record.HotelCode, searchResultRecord?.HotelCode);
        Assert.Equal(record.ParkingIncluded, searchResultRecord?.ParkingIncluded);
        Assert.Equal(record.Rating, searchResultRecord?.Rating);
        Assert.Equal(record.Description, searchResultRecord?.Description);
        Assert.Equal(record.DescriptionEmbedding?.ToArray(), searchResultRecord?.DescriptionEmbedding?.ToArray());

        // Output
        output.WriteLine(collectionExistResult.ToString());
        output.WriteLine(upsertResult);
        output.WriteLine(getResult?.ToString());
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanDeleteCollectionAsync()
    {
        // Arrange
        var tempCollectionName = "temp-test";
        var schema = new Schema();
        schema.AddTextField("HotelName");
        var createParams = new FTCreateParams();
        createParams.AddPrefix(tempCollectionName);
        await fixture.Database.FT().CreateAsync(tempCollectionName, createParams, schema);

        var sut = new RedisHashSetVectorStoreRecordCollection<string, RedisBasicFloat32Hotel>(fixture.Database, tempCollectionName);

        // Act
        await sut.DeleteCollectionAsync();

        // Assert
        Assert.False(await sut.CollectionExistsAsync());
    }

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanUpsertDocumentToVectorStoreAsync(bool useRecordDefinition)
    {
        // Arrange.
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<RedisBasicFloat32Hotel>
        {
            PrefixCollectionNameToKeyNames = true,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.BasicVectorStoreRecordDefinition : null
        };
        var sut = new RedisHashSetVectorStoreRecordCollection<string, RedisBasicFloat32Hotel>(fixture.Database, TestCollectionName, options);
        var record = CreateTestHotel("HUpsert-2", 2);

        // Act.
        var upsertResult = await sut.UpsertAsync(record);

        // Assert.
        var getResult = await sut.GetAsync("HUpsert-2", new GetRecordOptions { IncludeVectors = true });
        Assert.Equal("HUpsert-2", upsertResult);
        Assert.Equal(record.HotelId, getResult?.HotelId);
        Assert.Equal(record.HotelName, getResult?.HotelName);
        Assert.Equal(record.HotelCode, getResult?.HotelCode);
        Assert.Equal(record.ParkingIncluded, getResult?.ParkingIncluded);
        Assert.Equal(record.Rating, getResult?.Rating);
        Assert.Equal(record.Description, getResult?.Description);
        Assert.Equal(record.DescriptionEmbedding?.ToArray(), getResult?.DescriptionEmbedding?.ToArray());

        // Output.
        output.WriteLine(upsertResult);
        output.WriteLine(getResult?.ToString());
    }

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanUpsertManyDocumentsToVectorStoreAsync(bool useRecordDefinition)
    {
        // Arrange.
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<RedisBasicFloat32Hotel>
        {
            PrefixCollectionNameToKeyNames = true,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.BasicVectorStoreRecordDefinition : null
        };
        var sut = new RedisHashSetVectorStoreRecordCollection<string, RedisBasicFloat32Hotel>(fixture.Database, TestCollectionName, options);

        // Act.
        var results = sut.UpsertAsync(
            [
                CreateTestHotel("HUpsertMany-1", 1),
                CreateTestHotel("HUpsertMany-2", 2),
                CreateTestHotel("HUpsertMany-3", 3),
            ]);

        // Assert.
        Assert.NotNull(results);
        var resultsList = await results;

        Assert.Equal(3, resultsList.Count);
        Assert.Contains("HUpsertMany-1", resultsList);
        Assert.Contains("HUpsertMany-2", resultsList);
        Assert.Contains("HUpsertMany-3", resultsList);

        // Output
        foreach (var result in resultsList)
        {
            output.WriteLine(result);
        }
    }

    [Theory(Skip = SkipReason)]
    [InlineData(true, true)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(false, false)]
    public async Task ItCanGetDocumentFromVectorStoreAsync(bool includeVectors, bool useRecordDefinition)
    {
        // Arrange.
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<RedisBasicFloat32Hotel>
        {
            PrefixCollectionNameToKeyNames = true,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.BasicVectorStoreRecordDefinition : null
        };
        var sut = new RedisHashSetVectorStoreRecordCollection<string, RedisBasicFloat32Hotel>(fixture.Database, TestCollectionName, options);

        // Act.
        var getResult = await sut.GetAsync("HBaseSet-1", new GetRecordOptions { IncludeVectors = includeVectors });

        // Assert.
        Assert.Equal("HBaseSet-1", getResult?.HotelId);
        Assert.Equal("My Hotel 1", getResult?.HotelName);
        Assert.Equal(1, getResult?.HotelCode);
        Assert.True(getResult?.ParkingIncluded);
        Assert.Equal(3.6, getResult?.Rating);
        Assert.Equal("This is a great hotel.", getResult?.Description);
        if (includeVectors)
        {
            Assert.Equal(new[] { 30f, 31f, 32f, 33f }, getResult?.DescriptionEmbedding?.ToArray());
        }
        else
        {
            Assert.Null(getResult?.DescriptionEmbedding);
        }

        // Output.
        output.WriteLine(getResult?.ToString());
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanGetManyDocumentsFromVectorStoreAsync()
    {
        // Arrange
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<RedisBasicFloat32Hotel> { PrefixCollectionNameToKeyNames = true };
        var sut = new RedisHashSetVectorStoreRecordCollection<string, RedisBasicFloat32Hotel>(fixture.Database, TestCollectionName, options);

        // Act
        // Also include one non-existing key to test that the operation does not fail for these and returns only the found ones.
        var hotels = sut.GetAsync(["HBaseSet-1", "HBaseSet-5", "HBaseSet-2"], new GetRecordOptions { IncludeVectors = true });

        // Assert
        Assert.NotNull(hotels);
        var hotelsList = await hotels.ToListAsync();
        Assert.Equal(2, hotelsList.Count);

        // Output
        foreach (var hotel in hotelsList)
        {
            output.WriteLine(hotel?.ToString() ?? "Null");
        }
    }

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanRemoveDocumentFromVectorStoreAsync(bool useRecordDefinition)
    {
        // Arrange.
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<RedisBasicFloat32Hotel>
        {
            PrefixCollectionNameToKeyNames = true,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.BasicVectorStoreRecordDefinition : null
        };
        var sut = new RedisHashSetVectorStoreRecordCollection<string, RedisBasicFloat32Hotel>(fixture.Database, TestCollectionName, options);
        var record = new RedisBasicFloat32Hotel
        {
            HotelId = "HRemove-1",
            HotelName = "Remove Test Hotel",
            HotelCode = 20,
            Description = "This is a great hotel.",
            DescriptionEmbedding = new[] { 30f, 31f, 32f, 33f }
        };

        await sut.UpsertAsync(record);

        // Act.
        await sut.DeleteAsync("HRemove-1");
        // Also delete a non-existing key to test that the operation does not fail for these.
        await sut.DeleteAsync("HRemove-2");

        // Assert.
        Assert.Null(await sut.GetAsync("HRemove-1"));
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanRemoveManyDocumentsFromVectorStoreAsync()
    {
        // Arrange
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<RedisBasicFloat32Hotel> { PrefixCollectionNameToKeyNames = true };
        var sut = new RedisHashSetVectorStoreRecordCollection<string, RedisBasicFloat32Hotel>(fixture.Database, TestCollectionName, options);
        await sut.UpsertAsync(CreateTestHotel("HRemoveMany-1", 1));
        await sut.UpsertAsync(CreateTestHotel("HRemoveMany-2", 2));
        await sut.UpsertAsync(CreateTestHotel("HRemoveMany-3", 3));

        // Act
        // Also include a non-existing key to test that the operation does not fail for these.
        await sut.DeleteAsync(["HRemoveMany-1", "HRemoveMany-2", "HRemoveMany-3", "HRemoveMany-4"]);

        // Assert
        Assert.Null(await sut.GetAsync("HRemoveMany-1", new GetRecordOptions { IncludeVectors = true }));
        Assert.Null(await sut.GetAsync("HRemoveMany-2", new GetRecordOptions { IncludeVectors = true }));
        Assert.Null(await sut.GetAsync("HRemoveMany-3", new GetRecordOptions { IncludeVectors = true }));
    }

    [Theory(Skip = SkipReason)]
    [InlineData("hotelCode", true)]
    [InlineData("hotelName", false)]
    public async Task ItCanSearchWithFloat32VectorAndFilterAsync(string filterType, bool includeVectors)
    {
        // Arrange
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<RedisBasicFloat32Hotel> { PrefixCollectionNameToKeyNames = true };
        var sut = new RedisHashSetVectorStoreRecordCollection<string, RedisBasicFloat32Hotel>(fixture.Database, TestCollectionName, options);
        var vector = new ReadOnlyMemory<float>(new[] { 30f, 31f, 32f, 33f });
        var filter = filterType == "equality" ? new VectorSearchFilter().EqualTo("HotelCode", 1) : new VectorSearchFilter().EqualTo("HotelName", "My Hotel 1");

        // Act
        var searchResults = await sut.VectorizedSearchAsync(
            vector,
            top: 3,
            new()
            {
                IncludeVectors = includeVectors,
                OldFilter = filter
            }).ToListAsync();

        // Assert
        Assert.Single(searchResults);
        Assert.Equal(1, searchResults.First().Score);
        var searchResult = searchResults.First().Record;
        Assert.Equal("HBaseSet-1", searchResult?.HotelId);
        Assert.Equal("My Hotel 1", searchResult?.HotelName);
        Assert.Equal(1, searchResult?.HotelCode);
        Assert.True(searchResult?.ParkingIncluded);
        Assert.Equal(3.6, searchResult?.Rating);
        Assert.Equal("This is a great hotel.", searchResult?.Description);
        if (includeVectors)
        {
            Assert.Equal(new[] { 30f, 31f, 32f, 33f }, searchResult?.DescriptionEmbedding?.ToArray());
        }
        else
        {
            Assert.Null(searchResult?.DescriptionEmbedding);
        }
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanSearchWithFloat32VectorAndTopSkipAsync()
    {
        // Arrange
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<RedisBasicFloat32Hotel> { PrefixCollectionNameToKeyNames = true };
        var sut = new RedisHashSetVectorStoreRecordCollection<string, RedisBasicFloat32Hotel>(fixture.Database, TestCollectionName + "TopSkip", options);
        await sut.CreateCollectionIfNotExistsAsync();
        await sut.UpsertAsync(new RedisBasicFloat32Hotel { HotelId = "HTopSkip_1", HotelName = "1", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<float>([1.0f, 1.0f, 1.0f, 1.0f]) });
        await sut.UpsertAsync(new RedisBasicFloat32Hotel { HotelId = "HTopSkip_2", HotelName = "2", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<float>([1.0f, 1.0f, 1.0f, 2.0f]) });
        await sut.UpsertAsync(new RedisBasicFloat32Hotel { HotelId = "HTopSkip_3", HotelName = "3", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<float>([1.0f, 1.0f, 1.0f, 3.0f]) });
        await sut.UpsertAsync(new RedisBasicFloat32Hotel { HotelId = "HTopSkip_4", HotelName = "4", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<float>([1.0f, 1.0f, 1.0f, 4.0f]) });
        await sut.UpsertAsync(new RedisBasicFloat32Hotel { HotelId = "HTopSkip_5", HotelName = "5", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<float>([1.0f, 1.0f, 1.0f, 5.0f]) });
        var vector = new ReadOnlyMemory<float>([1.0f, 1.0f, 1.0f, 1.0f]);

        // Act
        var searchResults = await sut.VectorizedSearchAsync(
            vector,
            top: 3,
            new()
            {
                Skip = 2
            }).ToListAsync();

        // Assert
        Assert.Equal(3, searchResults.Count);
        Assert.True(searchResults.Select(x => x.Record.HotelId).SequenceEqual(["HTopSkip_3", "HTopSkip_4", "HTopSkip_5"]));
    }

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanSearchWithFloat64VectorAsync(bool includeVectors)
    {
        // Arrange
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<RedisBasicFloat64Hotel> { PrefixCollectionNameToKeyNames = true };
        var sut = new RedisHashSetVectorStoreRecordCollection<string, RedisBasicFloat64Hotel>(fixture.Database, TestCollectionName + "Float64", options);
        await sut.CreateCollectionIfNotExistsAsync();
        await sut.UpsertAsync(new RedisBasicFloat64Hotel { HotelId = "HFloat64_1", HotelName = "1", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<double>([1.0d, 1.1d, 1.2d, 1.3d]) });
        await sut.UpsertAsync(new RedisBasicFloat64Hotel { HotelId = "HFloat64_2", HotelName = "2", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<double>([2.0d, 2.1d, 2.2d, 2.3d]) });
        await sut.UpsertAsync(new RedisBasicFloat64Hotel { HotelId = "HFloat64_3", HotelName = "3", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<double>([3.0d, 3.1d, 3.2d, 3.3d]) });

        var vector = new ReadOnlyMemory<double>([2.0d, 2.1d, 2.2d, 2.3d]);

        // Act
        var searchResults = await sut.VectorizedSearchAsync(
            vector,
            top: 1,
            new()
            {
                IncludeVectors = includeVectors,
            }).ToListAsync();

        // Assert
        Assert.Single(searchResults);
        var searchResult = searchResults.First().Record;
        Assert.Equal("HFloat64_2", searchResult?.HotelId);
        Assert.Equal("2", searchResult?.HotelName);
        Assert.Equal("Nice hotel", searchResult?.Description);
        if (includeVectors)
        {
            Assert.Equal<double[]>([2.0d, 2.1d, 2.2d, 2.3d], searchResult?.DescriptionEmbedding?.ToArray());
        }
        else
        {
            Assert.Null(searchResult?.DescriptionEmbedding);
        }
    }

    [Fact(Skip = SkipReason)]
    public async Task ItReturnsNullWhenGettingNonExistentRecordAsync()
    {
        // Arrange
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<RedisBasicFloat32Hotel> { PrefixCollectionNameToKeyNames = true };
        var sut = new RedisHashSetVectorStoreRecordCollection<string, RedisBasicFloat32Hotel>(fixture.Database, TestCollectionName, options);

        // Act & Assert
        Assert.Null(await sut.GetAsync("HBaseSet-5", new GetRecordOptions { IncludeVectors = true }));
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanUpsertAndRetrieveUsingTheDynamicMapperAsync()
    {
        // Arrange
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<Dictionary<string, object?>>
        {
            PrefixCollectionNameToKeyNames = true,
            VectorStoreRecordDefinition = fixture.BasicVectorStoreRecordDefinition
        };
        var sut = new RedisHashSetVectorStoreRecordCollection<object, Dictionary<string, object?>>(fixture.Database, TestCollectionName, options);

        // Act
        var baseSetGetResult = await sut.GetAsync("HBaseSet-1", new GetRecordOptions { IncludeVectors = true });
        var upsertResult = await sut.UpsertAsync(new Dictionary<string, object?>
        {
            ["HotelId"] = "HDynamicMapper-1",

            ["HotelName"] = "Dynamic Mapper Hotel",
            ["HotelCode"] = 40,
            ["ParkingIncluded"] = true,
            ["Rating"] = 3.6d,
            ["Description"] = "This is a dynamic mapper hotel",

            ["DescriptionEmbedding"] = new ReadOnlyMemory<float>(new[] { 30f, 31f, 32f, 33f })
        });
        var localGetResult = await sut.GetAsync("HDynamicMapper-1", new GetRecordOptions { IncludeVectors = true });

        // Assert
        Assert.NotNull(baseSetGetResult);
        Assert.Equal("HBaseSet-1", baseSetGetResult["HotelId"]);
        Assert.Equal("My Hotel 1", baseSetGetResult["HotelName"]);
        Assert.Equal(1, baseSetGetResult["HotelCode"]);
        Assert.True((bool)baseSetGetResult["ParkingIncluded"]!);
        Assert.Equal(3.6d, baseSetGetResult["Rating"]);
        Assert.Equal("This is a great hotel.", baseSetGetResult["Description"]);
        Assert.NotNull(baseSetGetResult["DescriptionEmbedding"]);
        Assert.Equal(new[] { 30f, 31f, 32f, 33f }, ((ReadOnlyMemory<float>)baseSetGetResult["DescriptionEmbedding"]!).ToArray());

        Assert.Equal("HGenericMapper-1", upsertResult);

        Assert.NotNull(localGetResult);
        Assert.Equal("HDynamicMapper-1", localGetResult["HotelId"]);
        Assert.Equal("Dynamic Mapper Hotel", localGetResult["HotelName"]);
        Assert.Equal(40, localGetResult["HotelCode"]);
        Assert.True((bool)localGetResult["ParkingIncluded"]!);
        Assert.Equal(3.6d, localGetResult["Rating"]);
        Assert.Equal("This is a dynamic mapper hotel", localGetResult["Description"]);
        Assert.Equal(new[] { 30f, 31f, 32f, 33f }, ((ReadOnlyMemory<float>)localGetResult["DescriptionEmbedding"]!).ToArray());
    }

    private static RedisBasicFloat32Hotel CreateTestHotel(string hotelId, int hotelCode)
    {
        var record = new RedisBasicFloat32Hotel
        {
            HotelId = hotelId,
            HotelName = $"My Hotel {hotelCode}",
            HotelCode = 1,
            ParkingIncluded = true,
            Rating = 3.6,
            Description = "This is a great hotel.",
            DescriptionEmbedding = new[] { 30f, 31f, 32f, 33f }
        };
        return record;
    }
}
