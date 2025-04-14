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
/// Contains tests for the <see cref="RedisJsonVectorStoreRecordCollection{TKey, TRecord}"/> class.
/// </summary>
/// <param name="output">Used for logging.</param>
/// <param name="fixture">Redis setup and teardown.</param>
[Collection("RedisVectorStoreCollection")]
public sealed class RedisJsonVectorStoreRecordCollectionTests(ITestOutputHelper output, RedisVectorStoreFixture fixture)
{
    // If null, all tests will be enabled
    private const string SkipReason = null;

    private const string TestCollectionName = "jsonhotels";

    [Theory(Skip = SkipReason)]
    [InlineData(TestCollectionName, true)]
    [InlineData("nonexistentcollection", false)]
    public async Task CollectionExistsReturnsCollectionStateAsync(string collectionName, bool expectedExists)
    {
        // Arrange.
        var sut = new RedisJsonVectorStoreRecordCollection<string, RedisHotel>(fixture.Database, collectionName);

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
        var record = CreateTestHotel("Upsert-10", 10);
        var collectionNamePostfix = useRecordDefinition ? "WithDefinition" : "WithType";
        var testCollectionName = $"jsoncreatetest{collectionNamePostfix}";

        var options = new RedisJsonVectorStoreRecordCollectionOptions<RedisHotel>
        {
            PrefixCollectionNameToKeyNames = true,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.VectorStoreRecordDefinition : null
        };
        var sut = new RedisJsonVectorStoreRecordCollection<string, RedisHotel>(fixture.Database, testCollectionName, options);

        // Act
        await sut.CreateCollectionAsync();
        var upsertResult = await sut.UpsertAsync(record);
        var getResult = await sut.GetAsync("Upsert-10", new GetRecordOptions { IncludeVectors = true });
        var searchResults = await sut.VectorizedSearchAsync(
            new ReadOnlyMemory<float>(new[] { 30f, 31f, 32f, 33f }),
            top: 3,
            new() { OldFilter = new VectorSearchFilter().EqualTo("HotelCode", 10) }).ToListAsync();

        // Assert
        var collectionExistResult = await sut.CollectionExistsAsync();
        Assert.True(collectionExistResult);
        await sut.DeleteCollectionAsync();

        Assert.Equal("Upsert-10", upsertResult);
        Assert.Equal(record.HotelId, getResult?.HotelId);
        Assert.Equal(record.HotelName, getResult?.HotelName);
        Assert.Equal(record.HotelCode, getResult?.HotelCode);
        Assert.Equal(record.Tags, getResult?.Tags);
        Assert.Equal(record.FTSTags, getResult?.FTSTags);
        Assert.Equal(record.ParkingIncluded, getResult?.ParkingIncluded);
        Assert.Equal(record.LastRenovationDate, getResult?.LastRenovationDate);
        Assert.Equal(record.Rating, getResult?.Rating);
        Assert.Equal(record.Address.Country, getResult?.Address.Country);
        Assert.Equal(record.Address.City, getResult?.Address.City);
        Assert.Equal(record.Description, getResult?.Description);
        Assert.Equal(record.DescriptionEmbedding?.ToArray(), getResult?.DescriptionEmbedding?.ToArray());

        Assert.Single(searchResults);
        Assert.Equal(1, searchResults.First().Score);
        var searchResultRecord = searchResults.First().Record;
        Assert.Equal(record.HotelId, searchResultRecord?.HotelId);
        Assert.Equal(record.HotelName, searchResultRecord?.HotelName);
        Assert.Equal(record.HotelCode, searchResultRecord?.HotelCode);
        Assert.Equal(record.Tags, searchResultRecord?.Tags);
        Assert.Equal(record.FTSTags, searchResultRecord?.FTSTags);
        Assert.Equal(record.ParkingIncluded, searchResultRecord?.ParkingIncluded);
        Assert.Equal(record.LastRenovationDate, searchResultRecord?.LastRenovationDate);
        Assert.Equal(record.Rating, searchResultRecord?.Rating);
        Assert.Equal(record.Address.Country, searchResultRecord?.Address.Country);
        Assert.Equal(record.Address.City, searchResultRecord?.Address.City);
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

        var sut = new RedisJsonVectorStoreRecordCollection<string, RedisHotel>(fixture.Database, tempCollectionName);

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
        var options = new RedisJsonVectorStoreRecordCollectionOptions<RedisHotel>
        {
            PrefixCollectionNameToKeyNames = true,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.VectorStoreRecordDefinition : null
        };
        var sut = new RedisJsonVectorStoreRecordCollection<string, RedisHotel>(fixture.Database, TestCollectionName, options);
        RedisHotel record = CreateTestHotel("Upsert-2", 2);

        // Act.
        var upsertResult = await sut.UpsertAsync(record);

        // Assert.
        var getResult = await sut.GetAsync("Upsert-2", new GetRecordOptions { IncludeVectors = true });
        Assert.Equal("Upsert-2", upsertResult);
        Assert.Equal(record.HotelId, getResult?.HotelId);
        Assert.Equal(record.HotelName, getResult?.HotelName);
        Assert.Equal(record.HotelCode, getResult?.HotelCode);
        Assert.Equal(record.Tags, getResult?.Tags);
        Assert.Equal(record.FTSTags, getResult?.FTSTags);
        Assert.Equal(record.ParkingIncluded, getResult?.ParkingIncluded);
        Assert.Equal(record.LastRenovationDate, getResult?.LastRenovationDate);
        Assert.Equal(record.Rating, getResult?.Rating);
        Assert.Equal(record.Address.Country, getResult?.Address.Country);
        Assert.Equal(record.Address.City, getResult?.Address.City);
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
        var options = new RedisJsonVectorStoreRecordCollectionOptions<RedisHotel>
        {
            PrefixCollectionNameToKeyNames = true,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.VectorStoreRecordDefinition : null
        };
        var sut = new RedisJsonVectorStoreRecordCollection<string, RedisHotel>(fixture.Database, TestCollectionName, options);

        // Act.
        var results = sut.UpsertAsync(
            [
                CreateTestHotel("UpsertMany-1", 1),
                CreateTestHotel("UpsertMany-2", 2),
                CreateTestHotel("UpsertMany-3", 3),
            ]);

        // Assert.
        Assert.NotNull(results);
        var resultsList = await results;

        Assert.Equal(3, resultsList.Count);
        Assert.Contains("UpsertMany-1", resultsList);
        Assert.Contains("UpsertMany-2", resultsList);
        Assert.Contains("UpsertMany-3", resultsList);

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
        var options = new RedisJsonVectorStoreRecordCollectionOptions<RedisHotel>
        {
            PrefixCollectionNameToKeyNames = true,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.VectorStoreRecordDefinition : null
        };
        var sut = new RedisJsonVectorStoreRecordCollection<string, RedisHotel>(fixture.Database, TestCollectionName, options);

        // Act.
        var getResult = await sut.GetAsync("BaseSet-1", new GetRecordOptions { IncludeVectors = includeVectors });

        // Assert.
        Assert.Equal("BaseSet-1", getResult?.HotelId);
        Assert.Equal("My Hotel 1", getResult?.HotelName);
        Assert.Equal(1, getResult?.HotelCode);
        Assert.Equal(new[] { "pool", "air conditioning", "concierge" }, getResult?.Tags);
        Assert.Equal(new[] { "pool", "air conditioning", "concierge" }, getResult?.FTSTags);
        Assert.True(getResult?.ParkingIncluded);
        Assert.Equal(new DateTimeOffset(1970, 1, 18, 0, 0, 0, TimeSpan.Zero), getResult?.LastRenovationDate);
        Assert.Equal(3.6, getResult?.Rating);
        Assert.Equal("Seattle", getResult?.Address.City);
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
        var options = new RedisJsonVectorStoreRecordCollectionOptions<RedisHotel> { PrefixCollectionNameToKeyNames = true };
        var sut = new RedisJsonVectorStoreRecordCollection<string, RedisHotel>(fixture.Database, TestCollectionName, options);

        // Act
        // Also include one non-existing key to test that the operation does not fail for these and returns only the found ones.
        var hotels = sut.GetAsync(["BaseSet-1", "BaseSet-5", "BaseSet-2"], new GetRecordOptions { IncludeVectors = true });

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

    [Fact(Skip = SkipReason)]
    public async Task ItFailsToGetDocumentsWithInvalidSchemaAsync()
    {
        // Arrange.
        var options = new RedisJsonVectorStoreRecordCollectionOptions<RedisHotel> { PrefixCollectionNameToKeyNames = true };
        var sut = new RedisJsonVectorStoreRecordCollection<string, RedisHotel>(fixture.Database, TestCollectionName, options);

        // Act & Assert.
        await Assert.ThrowsAsync<VectorStoreRecordMappingException>(async () => await sut.GetAsync("BaseSet-4-Invalid", new GetRecordOptions { IncludeVectors = true }));
    }

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanRemoveDocumentFromVectorStoreAsync(bool useRecordDefinition)
    {
        // Arrange.
        var options = new RedisJsonVectorStoreRecordCollectionOptions<RedisHotel>
        {
            PrefixCollectionNameToKeyNames = true,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.VectorStoreRecordDefinition : null
        };
        var sut = new RedisJsonVectorStoreRecordCollection<string, RedisHotel>(fixture.Database, TestCollectionName, options);
        var address = new RedisHotelAddress { City = "Seattle", Country = "USA" };
        var record = new RedisHotel
        {
            HotelId = "Remove-1",
            HotelName = "Remove Test Hotel",
            HotelCode = 20,
            Description = "This is a great hotel.",
            DescriptionEmbedding = new[] { 30f, 31f, 32f, 33f }
        };

        await sut.UpsertAsync(record);

        // Act.
        await sut.DeleteAsync("Remove-1");
        // Also delete a non-existing key to test that the operation does not fail for these.
        await sut.DeleteAsync("Remove-2");

        // Assert.
        Assert.Null(await sut.GetAsync("Remove-1"));
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanRemoveManyDocumentsFromVectorStoreAsync()
    {
        // Arrange
        var options = new RedisJsonVectorStoreRecordCollectionOptions<RedisHotel> { PrefixCollectionNameToKeyNames = true };
        var sut = new RedisJsonVectorStoreRecordCollection<string, RedisHotel>(fixture.Database, TestCollectionName, options);
        await sut.UpsertAsync(CreateTestHotel("RemoveMany-1", 1));
        await sut.UpsertAsync(CreateTestHotel("RemoveMany-2", 2));
        await sut.UpsertAsync(CreateTestHotel("RemoveMany-3", 3));

        // Act
        // Also include a non-existing key to test that the operation does not fail for these.
        await sut.DeleteAsync(["RemoveMany-1", "RemoveMany-2", "RemoveMany-3", "RemoveMany-4"]);

        // Assert
        Assert.Null(await sut.GetAsync("RemoveMany-1", new GetRecordOptions { IncludeVectors = true }));
        Assert.Null(await sut.GetAsync("RemoveMany-2", new GetRecordOptions { IncludeVectors = true }));
        Assert.Null(await sut.GetAsync("RemoveMany-3", new GetRecordOptions { IncludeVectors = true }));
    }

    [Theory(Skip = SkipReason)]
    [InlineData("equality")]
    [InlineData("tagContains")]
    public async Task ItCanSearchWithFloat32VectorAndFilterAsync(string filterType)
    {
        // Arrange
        var options = new RedisJsonVectorStoreRecordCollectionOptions<RedisHotel> { PrefixCollectionNameToKeyNames = true };
        var sut = new RedisJsonVectorStoreRecordCollection<string, RedisHotel>(fixture.Database, TestCollectionName, options);
        var vector = new ReadOnlyMemory<float>(new[] { 30f, 31f, 32f, 33f });
        var filter = filterType == "equality" ? new VectorSearchFilter().EqualTo("HotelCode", 1) : new VectorSearchFilter().AnyTagEqualTo("Tags", "pool");

        // Act
        var searchResults = await sut.VectorizedSearchAsync(
            vector,
            top: 3,
            new() { IncludeVectors = true, OldFilter = filter }).ToListAsync();

        // Assert
        Assert.Single(searchResults);
        Assert.Equal(1, searchResults.First().Score);
        var searchResult = searchResults.First().Record;
        Assert.Equal("My Hotel 1", searchResults.First().Record.HotelName);
        Assert.Equal("BaseSet-1", searchResult?.HotelId);
        Assert.Equal("My Hotel 1", searchResult?.HotelName);
        Assert.Equal(1, searchResult?.HotelCode);
        Assert.Equal(new[] { "pool", "air conditioning", "concierge" }, searchResult?.Tags);
        Assert.Equal(new[] { "pool", "air conditioning", "concierge" }, searchResult?.FTSTags);
        Assert.True(searchResult?.ParkingIncluded);
        Assert.Equal(new DateTimeOffset(1970, 1, 18, 0, 0, 0, TimeSpan.Zero), searchResult?.LastRenovationDate);
        Assert.Equal(3.6, searchResult?.Rating);
        Assert.Equal("Seattle", searchResult?.Address.City);
        Assert.Equal("This is a great hotel.", searchResult?.Description);
        Assert.Equal(new[] { 30f, 31f, 32f, 33f }, searchResult?.DescriptionEmbedding?.ToArray());
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanSearchWithFloat32VectorAndTopSkipAsync()
    {
        // Arrange
        var options = new RedisJsonVectorStoreRecordCollectionOptions<RedisBasicFloat32Hotel> { PrefixCollectionNameToKeyNames = true };
        var sut = new RedisJsonVectorStoreRecordCollection<string, RedisBasicFloat32Hotel>(fixture.Database, TestCollectionName + "TopSkip", options);
        await sut.CreateCollectionIfNotExistsAsync();
        await sut.UpsertAsync(new RedisBasicFloat32Hotel { HotelId = "TopSkip_1", HotelName = "1", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<float>([1.0f, 1.0f, 1.0f, 1.0f]) });
        await sut.UpsertAsync(new RedisBasicFloat32Hotel { HotelId = "TopSkip_2", HotelName = "2", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<float>([1.0f, 1.0f, 1.0f, 2.0f]) });
        await sut.UpsertAsync(new RedisBasicFloat32Hotel { HotelId = "TopSkip_3", HotelName = "3", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<float>([1.0f, 1.0f, 1.0f, 3.0f]) });
        await sut.UpsertAsync(new RedisBasicFloat32Hotel { HotelId = "TopSkip_4", HotelName = "4", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<float>([1.0f, 1.0f, 1.0f, 4.0f]) });
        await sut.UpsertAsync(new RedisBasicFloat32Hotel { HotelId = "TopSkip_5", HotelName = "5", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<float>([1.0f, 1.0f, 1.0f, 5.0f]) });
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
        Assert.True(searchResults.Select(x => x.Record.HotelId).SequenceEqual(["TopSkip_3", "TopSkip_4", "TopSkip_5"]));
    }

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanSearchWithFloat64VectorAsync(bool includeVectors)
    {
        // Arrange
        var options = new RedisJsonVectorStoreRecordCollectionOptions<RedisBasicFloat64Hotel> { PrefixCollectionNameToKeyNames = true };
        var sut = new RedisJsonVectorStoreRecordCollection<string, RedisBasicFloat64Hotel>(fixture.Database, TestCollectionName + "Float64", options);
        await sut.CreateCollectionIfNotExistsAsync();
        await sut.UpsertAsync(new RedisBasicFloat64Hotel { HotelId = "Float64_1", HotelName = "1", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<double>([1.0d, 1.1d, 1.2d, 1.3d]) });
        await sut.UpsertAsync(new RedisBasicFloat64Hotel { HotelId = "Float64_2", HotelName = "2", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<double>([2.0d, 2.1d, 2.2d, 2.3d]) });
        await sut.UpsertAsync(new RedisBasicFloat64Hotel { HotelId = "Float64_3", HotelName = "3", Description = "Nice hotel", DescriptionEmbedding = new ReadOnlyMemory<double>([3.0d, 3.1d, 3.2d, 3.3d]) });

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
        Assert.Equal("Float64_2", searchResult?.HotelId);
        Assert.Equal("2", searchResult?.HotelName);
        Assert.Equal("Nice hotel", searchResult?.Description);
        if (includeVectors)
        {
            Assert.Equal<double[]>([2.0d, 2.1d, 2.2d, 2.3d], searchResult?.DescriptionEmbedding?.ToArray());
        }
    }

    [Fact(Skip = SkipReason)]
    public async Task ItReturnsNullWhenGettingNonExistentRecordAsync()
    {
        // Arrange
        var options = new RedisJsonVectorStoreRecordCollectionOptions<RedisHotel> { PrefixCollectionNameToKeyNames = true };
        var sut = new RedisJsonVectorStoreRecordCollection<string, RedisHotel>(fixture.Database, TestCollectionName, options);

        // Act & Assert
        Assert.Null(await sut.GetAsync("BaseSet-5", new GetRecordOptions { IncludeVectors = true }));
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanUpsertAndRetrieveUsingTheDynamicMapperAsync()
    {
        // Arrange
        var options = new RedisJsonVectorStoreRecordCollectionOptions<Dictionary<string, object?>>
        {
            PrefixCollectionNameToKeyNames = true,
            VectorStoreRecordDefinition = fixture.VectorStoreRecordDefinition
        };
        var sut = new RedisJsonVectorStoreRecordCollection<object, Dictionary<string, object?>>(fixture.Database, TestCollectionName, options);

        // Act
        var baseSetGetResult = await sut.GetAsync("BaseSet-1", new GetRecordOptions { IncludeVectors = true });
        var upsertResult = await sut.UpsertAsync(new Dictionary<string, object?>
        {
            ["HotelId"] = "DynamicMapper-1",

            ["HotelName"] = "Dynamic Mapper Hotel",
            ["HotelCode"] = 1,
            ["Tags"] = new[] { "dynamic 1", "dynamic 2" },
            ["FTSTags"] = new[] { "dynamic 1", "dynamic 2" },
            ["ParkingIncluded"] = true,
            ["LastRenovationDate"] = new DateTimeOffset(1970, 1, 18, 0, 0, 0, TimeSpan.Zero),
            ["Rating"] = 3.6,
            ["Address"] = new RedisHotelAddress { City = "Seattle", Country = "USA" },
            ["Description"] = "This is a dynamic mapper hotel",

            ["DescriptionEmbedding"] = new ReadOnlyMemory<float>(new[] { 30f, 31f, 32f, 33f })
        });
        var localGetResult = await sut.GetAsync("DynamicMapper-1", new GetRecordOptions { IncludeVectors = true });

        // Assert
        Assert.NotNull(baseSetGetResult);
        Assert.Equal("BaseSet-1", baseSetGetResult["HotelId"]);
        Assert.Equal("My Hotel 1", baseSetGetResult["HotelName"]);
        Assert.Equal(1, baseSetGetResult["HotelCode"]);
        Assert.Equal(new[] { "pool", "air conditioning", "concierge" }, baseSetGetResult["Tags"]);
        Assert.Equal(new[] { "pool", "air conditioning", "concierge" }, baseSetGetResult["FTSTags"]);
        Assert.True((bool)baseSetGetResult["ParkingIncluded"]!);
        Assert.Equal(new DateTimeOffset(1970, 1, 18, 0, 0, 0, TimeSpan.Zero), baseSetGetResult["LastRenovationDate"]);
        Assert.Equal(3.6, baseSetGetResult["Rating"]);
        Assert.Equal("Seattle", ((RedisHotelAddress)baseSetGetResult["Address"]!).City);
        Assert.Equal("This is a great hotel.", baseSetGetResult["Description"]);
        Assert.Equal(new[] { 30f, 31f, 32f, 33f }, ((ReadOnlyMemory<float>)baseSetGetResult["DescriptionEmbedding"]!).ToArray());

        Assert.Equal("DynamicMapper-1", upsertResult);

        Assert.NotNull(localGetResult);
        Assert.Equal("DynamicMapper-1", localGetResult["HotelId"]);
        Assert.Equal("Dynamic Mapper Hotel", localGetResult["HotelName"]);
        Assert.Equal(1, localGetResult["HotelCode"]);
        Assert.Equal(new[] { "dynamic 1", "dynamic 2" }, localGetResult["Tags"]);
        Assert.Equal(new[] { "dynamic 1", "dynamic 2" }, localGetResult["FTSTags"]);
        Assert.True((bool)localGetResult["ParkingIncluded"]!);
        Assert.Equal(new DateTimeOffset(1970, 1, 18, 0, 0, 0, TimeSpan.Zero), localGetResult["LastRenovationDate"]);
        Assert.Equal(3.6d, localGetResult["Rating"]);
        Assert.Equal("Seattle", ((RedisHotelAddress)localGetResult["Address"]!).City);
        Assert.Equal("This is a dynamic mapper hotel", localGetResult["Description"]);
        Assert.Equal(new[] { 30f, 31f, 32f, 33f }, ((ReadOnlyMemory<float>)localGetResult["DescriptionEmbedding"]!).ToArray());
    }

    private static RedisHotel CreateTestHotel(string hotelId, int hotelCode)
    {
        var address = new RedisHotelAddress { City = "Seattle", Country = "USA" };
        var record = new RedisHotel
        {
            HotelId = hotelId,
            HotelName = $"My Hotel {hotelCode}",
            HotelCode = hotelCode,
            Tags = ["air conditioning", "concierge"],
            FTSTags = ["air conditioning", "concierge"],
            ParkingIncluded = true,
            LastRenovationDate = new DateTimeOffset(1970, 1, 18, 0, 0, 0, TimeSpan.Zero),
            Rating = 3.6,
            Address = address,
            Description = "This is a great hotel.",
            DescriptionEmbedding = new[] { 30f, 31f, 32f, 33f }
        };
        return record;
    }
}
