﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Redis;
using Microsoft.SemanticKernel.Data;
using NRedisStack.RedisStackCommands;
using NRedisStack.Search;
using StackExchange.Redis;
using Xunit;
using Xunit.Abstractions;
using static SemanticKernel.IntegrationTests.Connectors.Memory.Redis.RedisVectorStoreFixture;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Redis;

/// <summary>
/// Contains tests for the <see cref="RedisHashSetVectorStoreRecordCollection{TRecord}"/> class.
/// </summary>
/// <param name="output">Used for logging.</param>
/// <param name="fixture">Redis setup and teardown.</param>
[Collection("RedisVectorStoreCollection")]
public sealed class RedisHashSetVectorStoreRecordCollectionTests(ITestOutputHelper output, RedisVectorStoreFixture fixture)
{
    // If null, all tests will be enabled
    private const string SkipReason = "Requires Redis docker container up and running";

    private const string TestCollectionName = "hashhotels";

    [Theory(Skip = SkipReason)]
    [InlineData(TestCollectionName, true)]
    [InlineData("nonexistentcollection", false)]
    public async Task CollectionExistsReturnsCollectionStateAsync(string collectionName, bool expectedExists)
    {
        // Arrange.
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, collectionName);

        // Act.
        var actual = await sut.CollectionExistsAsync();

        // Assert.
        Assert.Equal(expectedExists, actual);
    }

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanCreateACollectionUpsertAndGetAsync(bool useRecordDefinition)
    {
        // Arrange
        var record = CreateTestHotel("Upsert-1", 1);
        var collectionNamePostfix = useRecordDefinition ? "WithDefinition" : "WithType";
        var testCollectionName = $"hashsetcreatetest{collectionNamePostfix}";

        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel>
        {
            PrefixCollectionNameToKeyNames = true,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.BasicVectorStoreRecordDefinition : null
        };
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, testCollectionName, options);

        // Act
        await sut.CreateCollectionAsync();
        var upsertResult = await sut.UpsertAsync(record);
        var getResult = await sut.GetAsync("Upsert-1", new GetRecordOptions { IncludeVectors = true });

        // Assert
        var collectionExistResult = await sut.CollectionExistsAsync();
        Assert.True(collectionExistResult);
        await sut.DeleteCollectionAsync();

        Assert.Equal("Upsert-1", upsertResult);
        Assert.Equal(record.HotelId, getResult?.HotelId);
        Assert.Equal(record.HotelName, getResult?.HotelName);
        Assert.Equal(record.HotelCode, getResult?.HotelCode);
        Assert.Equal(record.ParkingIncluded, getResult?.ParkingIncluded);
        Assert.Equal(record.Rating, getResult?.Rating);
        Assert.Equal(record.Description, getResult?.Description);
        Assert.Equal(record.DescriptionEmbedding?.ToArray(), getResult?.DescriptionEmbedding?.ToArray());

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

        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, tempCollectionName);

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
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel>
        {
            PrefixCollectionNameToKeyNames = true,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.BasicVectorStoreRecordDefinition : null
        };
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, TestCollectionName, options);
        var record = CreateTestHotel("Upsert-2", 2);

        // Act.
        var upsertResult = await sut.UpsertAsync(record);

        // Assert.
        var getResult = await sut.GetAsync("Upsert-2", new GetRecordOptions { IncludeVectors = true });
        Assert.Equal("Upsert-2", upsertResult);
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
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel>
        {
            PrefixCollectionNameToKeyNames = true,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.BasicVectorStoreRecordDefinition : null
        };
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, TestCollectionName, options);

        // Act.
        var results = sut.UpsertBatchAsync(
            [
                CreateTestHotel("UpsertMany-1", 1),
                CreateTestHotel("UpsertMany-2", 2),
                CreateTestHotel("UpsertMany-3", 3),
            ]);

        // Assert.
        Assert.NotNull(results);
        var resultsList = await results.ToListAsync();

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
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel>
        {
            PrefixCollectionNameToKeyNames = true,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.BasicVectorStoreRecordDefinition : null
        };
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, TestCollectionName, options);

        // Act.
        var getResult = await sut.GetAsync("BaseSet-1", new GetRecordOptions { IncludeVectors = includeVectors });

        // Assert.
        Assert.Equal("BaseSet-1", getResult?.HotelId);
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
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel> { PrefixCollectionNameToKeyNames = true };
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, TestCollectionName, options);

        // Act
        // Also include one non-existing key to test that the operation does not fail for these and returns only the found ones.
        var hotels = sut.GetBatchAsync(["BaseSet-1", "BaseSet-5", "BaseSet-2"], new GetRecordOptions { IncludeVectors = true });

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
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel>
        {
            PrefixCollectionNameToKeyNames = true,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.BasicVectorStoreRecordDefinition : null
        };
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, TestCollectionName, options);
        var record = new BasicHotel
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
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel> { PrefixCollectionNameToKeyNames = true };
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, TestCollectionName, options);
        await sut.UpsertAsync(CreateTestHotel("RemoveMany-1", 1));
        await sut.UpsertAsync(CreateTestHotel("RemoveMany-2", 2));
        await sut.UpsertAsync(CreateTestHotel("RemoveMany-3", 3));

        // Act
        // Also include a non-existing key to test that the operation does not fail for these.
        await sut.DeleteBatchAsync(["RemoveMany-1", "RemoveMany-2", "RemoveMany-3", "RemoveMany-4"]);

        // Assert
        Assert.Null(await sut.GetAsync("RemoveMany-1", new GetRecordOptions { IncludeVectors = true }));
        Assert.Null(await sut.GetAsync("RemoveMany-2", new GetRecordOptions { IncludeVectors = true }));
        Assert.Null(await sut.GetAsync("RemoveMany-3", new GetRecordOptions { IncludeVectors = true }));
    }

    [Fact(Skip = SkipReason)]
    public async Task ItReturnsNullWhenGettingNonExistentRecordAsync()
    {
        // Arrange
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel> { PrefixCollectionNameToKeyNames = true };
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, TestCollectionName, options);

        // Act & Assert
        Assert.Null(await sut.GetAsync("BaseSet-5", new GetRecordOptions { IncludeVectors = true }));
    }

    [Fact(Skip = SkipReason)]
    public async Task ItThrowsMappingExceptionForFailedMapperAsync()
    {
        // Arrange
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<BasicHotel>
        {
            PrefixCollectionNameToKeyNames = true,
            HashEntriesCustomMapper = new FailingMapper()
        };
        var sut = new RedisHashSetVectorStoreRecordCollection<BasicHotel>(fixture.Database, TestCollectionName, options);

        // Act & Assert
        await Assert.ThrowsAsync<VectorStoreRecordMappingException>(async () => await sut.GetAsync("BaseSet-1", new GetRecordOptions { IncludeVectors = true }));
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanUpsertAndRetrieveUsingTheGenericMapperAsync()
    {
        // Arrange
        var options = new RedisHashSetVectorStoreRecordCollectionOptions<VectorStoreGenericDataModel<string>>
        {
            PrefixCollectionNameToKeyNames = true,
            VectorStoreRecordDefinition = fixture.BasicVectorStoreRecordDefinition
        };
        var sut = new RedisHashSetVectorStoreRecordCollection<VectorStoreGenericDataModel<string>>(fixture.Database, TestCollectionName, options);

        // Act
        var baseSetGetResult = await sut.GetAsync("BaseSet-1", new GetRecordOptions { IncludeVectors = true });
        var upsertResult = await sut.UpsertAsync(new VectorStoreGenericDataModel<string>("GenericMapper-1")
        {
            Data =
            {
                { "HotelName", "Generic Mapper Hotel" },
                { "HotelCode", 40 },
                { "ParkingIncluded", true },
                { "Rating", 3.6d },
                { "Description", "This is a generic mapper hotel" },
            },
            Vectors =
            {
                { "DescriptionEmbedding", new ReadOnlyMemory<float>(new[] { 30f, 31f, 32f, 33f }) }
            }
        });
        var localGetResult = await sut.GetAsync("GenericMapper-1", new GetRecordOptions { IncludeVectors = true });

        // Assert
        Assert.NotNull(baseSetGetResult);
        Assert.Equal("BaseSet-1", baseSetGetResult.Key);
        Assert.Equal("My Hotel 1", baseSetGetResult.Data["HotelName"]);
        Assert.Equal(1, baseSetGetResult.Data["HotelCode"]);
        Assert.True((bool)baseSetGetResult.Data["ParkingIncluded"]!);
        Assert.Equal(3.6d, baseSetGetResult.Data["Rating"]);
        Assert.Equal("This is a great hotel.", baseSetGetResult.Data["Description"]);
        Assert.NotNull(baseSetGetResult.Vectors["DescriptionEmbedding"]);
        Assert.Equal(new[] { 30f, 31f, 32f, 33f }, ((ReadOnlyMemory<float>)baseSetGetResult.Vectors["DescriptionEmbedding"]!).ToArray());

        Assert.Equal("GenericMapper-1", upsertResult);

        Assert.NotNull(localGetResult);
        Assert.Equal("GenericMapper-1", localGetResult.Key);
        Assert.Equal("Generic Mapper Hotel", localGetResult.Data["HotelName"]);
        Assert.Equal(40, localGetResult.Data["HotelCode"]);
        Assert.True((bool)localGetResult.Data["ParkingIncluded"]!);
        Assert.Equal(3.6d, localGetResult.Data["Rating"]);
        Assert.Equal("This is a generic mapper hotel", localGetResult.Data["Description"]);
        Assert.Equal(new[] { 30f, 31f, 32f, 33f }, ((ReadOnlyMemory<float>)localGetResult.Vectors["DescriptionEmbedding"]!).ToArray());
    }

    private static BasicHotel CreateTestHotel(string hotelId, int hotelCode)
    {
        var record = new BasicHotel
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

    private sealed class FailingMapper : IVectorStoreRecordMapper<BasicHotel, (string Key, HashEntry[] HashEntries)>
    {
        public (string Key, HashEntry[] HashEntries) MapFromDataToStorageModel(BasicHotel dataModel)
        {
            throw new NotImplementedException();
        }

        public BasicHotel MapFromStorageToDataModel((string Key, HashEntry[] HashEntries) storageModel, StorageToDataModelMapperOptions options)
        {
            throw new NotImplementedException();
        }
    }
}
