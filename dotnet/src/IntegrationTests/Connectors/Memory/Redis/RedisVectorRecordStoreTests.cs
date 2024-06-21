// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Redis;
using Microsoft.SemanticKernel.Memory;
using Xunit;
using Xunit.Abstractions;
using static SemanticKernel.IntegrationTests.Connectors.Memory.Redis.RedisVectorStoreFixture;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Redis;

/// <summary>
/// Contains tests for the <see cref="RedisVectorRecordStore{TRecord}"/> class.
/// </summary>
/// <param name="output">Used for logging.</param>
/// <param name="fixture">Redis setup and teardown.</param>
[Collection("RedisVectorStoreCollection")]
public sealed class RedisVectorRecordStoreTests(ITestOutputHelper output, RedisVectorStoreFixture fixture)
{
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanUpsertDocumentToVectorStoreAsync(bool useRecordDefinition)
    {
        // Arrange.
        var options = new RedisVectorRecordStoreOptions<Hotel>
        {
            DefaultCollectionName = "hotels",
            PrefixCollectionNameToKeyNames = true,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.VectorStoreRecordDefinition : null
        };
        var sut = new RedisVectorRecordStore<Hotel>(fixture.Database, options);
        Hotel record = CreateTestHotel("Upsert-1", 1);

        // Act.
        var upsertResult = await sut.UpsertAsync(record);

        // Assert.
        var getResult = await sut.GetAsync("Upsert-1", new GetRecordOptions { IncludeVectors = true });
        Assert.Equal("Upsert-1", upsertResult);
        Assert.Equal(record.HotelId, getResult?.HotelId);
        Assert.Equal(record.HotelName, getResult?.HotelName);
        Assert.Equal(record.HotelCode, getResult?.HotelCode);
        Assert.Equal(record.Tags, getResult?.Tags);
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

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanUpsertManyDocumentsToVectorStoreAsync(bool useRecordDefinition)
    {
        // Arrange.
        var options = new RedisVectorRecordStoreOptions<Hotel>
        {
            DefaultCollectionName = "hotels",
            PrefixCollectionNameToKeyNames = true,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.VectorStoreRecordDefinition : null
        };
        var sut = new RedisVectorRecordStore<Hotel>(fixture.Database, options);

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

    [Theory]
    [InlineData(true, true)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(false, false)]
    public async Task ItCanGetDocumentFromVectorStoreAsync(bool includeVectors, bool useRecordDefinition)
    {
        // Arrange.
        var options = new RedisVectorRecordStoreOptions<Hotel>
        {
            DefaultCollectionName = "hotels",
            PrefixCollectionNameToKeyNames = true,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.VectorStoreRecordDefinition : null
        };
        var sut = new RedisVectorRecordStore<Hotel>(fixture.Database, options);

        // Act.
        var getResult = await sut.GetAsync("BaseSet-1", new GetRecordOptions { IncludeVectors = includeVectors });

        // Assert.
        Assert.Equal("BaseSet-1", getResult?.HotelId);
        Assert.Equal("My Hotel 1", getResult?.HotelName);
        Assert.Equal(1, getResult?.HotelCode);
        Assert.Equal(new[] { "pool", "air conditioning", "concierge" }, getResult?.Tags);
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

    [Fact]
    public async Task ItCanGetManyDocumentsFromVectorStoreAsync()
    {
        // Arrange
        var options = new RedisVectorRecordStoreOptions<Hotel> { DefaultCollectionName = "hotels", PrefixCollectionNameToKeyNames = true };
        var sut = new RedisVectorRecordStore<Hotel>(fixture.Database, options);

        // Act
        var hotels = sut.GetBatchAsync(["BaseSet-1", "BaseSet-2"], new GetRecordOptions { IncludeVectors = true });

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

    [Fact]
    public async Task ItFailsToGetDocumentsWithInvalidSchemaAsync()
    {
        // Arrange.
        var options = new RedisVectorRecordStoreOptions<Hotel> { DefaultCollectionName = "hotels", PrefixCollectionNameToKeyNames = true };
        var sut = new RedisVectorRecordStore<Hotel>(fixture.Database, options);

        // Act & Assert.
        await Assert.ThrowsAsync<VectorStoreRecordMappingException>(async () => await sut.GetAsync("BaseSet-4-Invalid", new GetRecordOptions { IncludeVectors = true }));
    }

    [Fact]
    public async Task ItThrowsForPartialGetBatchResultAsync()
    {
        // Arrange.
        var options = new RedisVectorRecordStoreOptions<Hotel> { DefaultCollectionName = "hotels", PrefixCollectionNameToKeyNames = true };
        var sut = new RedisVectorRecordStore<Hotel>(fixture.Database, options);

        // Act & Assert.
        await Assert.ThrowsAsync<VectorStoreOperationException>(async () => await sut.GetBatchAsync(["BaseSet-1", "nonexistent", "BaseSet-2"], new GetRecordOptions { IncludeVectors = true }).ToListAsync());
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanRemoveDocumentFromVectorStoreAsync(bool useRecordDefinition)
    {
        // Arrange.
        var options = new RedisVectorRecordStoreOptions<Hotel>
        {
            DefaultCollectionName = "hotels",
            PrefixCollectionNameToKeyNames = true,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.VectorStoreRecordDefinition : null
        };
        var sut = new RedisVectorRecordStore<Hotel>(fixture.Database, options);
        var address = new HotelAddress { City = "Seattle", Country = "USA" };
        var record = new Hotel
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
        await Assert.ThrowsAsync<VectorStoreOperationException>(async () => await sut.GetAsync("Remove-1"));
    }

    [Fact]
    public async Task ItCanRemoveManyDocumentsFromVectorStoreAsync()
    {
        // Arrange
        var options = new RedisVectorRecordStoreOptions<Hotel> { DefaultCollectionName = "hotels", PrefixCollectionNameToKeyNames = true };
        var sut = new RedisVectorRecordStore<Hotel>(fixture.Database, options);
        await sut.UpsertAsync(CreateTestHotel("RemoveMany-1", 1));
        await sut.UpsertAsync(CreateTestHotel("RemoveMany-2", 2));
        await sut.UpsertAsync(CreateTestHotel("RemoveMany-3", 3));

        // Act
        // Also include a non-existing key to test that the operation does not fail for these.
        await sut.DeleteBatchAsync(["RemoveMany-1", "RemoveMany-2", "RemoveMany-3", "RemoveMany-4"]);

        // Assert
        await Assert.ThrowsAsync<VectorStoreOperationException>(async () => await sut.GetAsync("RemoveMany-1", new GetRecordOptions { IncludeVectors = true }));
        await Assert.ThrowsAsync<VectorStoreOperationException>(async () => await sut.GetAsync("RemoveMany-2", new GetRecordOptions { IncludeVectors = true }));
        await Assert.ThrowsAsync<VectorStoreOperationException>(async () => await sut.GetAsync("RemoveMany-3", new GetRecordOptions { IncludeVectors = true }));
    }

    [Fact]
    public async Task ItThrowsMappingExceptionForFailedMapperAsync()
    {
        // Arrange
        var options = new RedisVectorRecordStoreOptions<Hotel>
        {
            DefaultCollectionName = "hotels",
            PrefixCollectionNameToKeyNames = true,
            MapperType = RedisRecordMapperType.JsonNodeCustomMapper,
            JsonNodeCustomMapper = new FailingMapper()
        };
        var sut = new RedisVectorRecordStore<Hotel>(fixture.Database, options);

        // Act & Assert
        await Assert.ThrowsAsync<VectorStoreRecordMappingException>(async () => await sut.GetAsync("BaseSet-1", new GetRecordOptions { IncludeVectors = true }));
    }

    private static Hotel CreateTestHotel(string hotelId, int hotelCode)
    {
        var address = new HotelAddress { City = "Seattle", Country = "USA" };
        var record = new Hotel
        {
            HotelId = hotelId,
            HotelName = $"My Hotel {hotelCode}",
            HotelCode = 1,
            Tags = ["pool", "air conditioning", "concierge"],
            ParkingIncluded = true,
            LastRenovationDate = new DateTimeOffset(1970, 1, 18, 0, 0, 0, TimeSpan.Zero),
            Rating = 3.6,
            Address = address,
            Description = "This is a great hotel.",
            DescriptionEmbedding = new[] { 30f, 31f, 32f, 33f }
        };
        return record;
    }

    private sealed class FailingMapper : IVectorStoreRecordMapper<Hotel, (string Key, JsonNode Node)>
    {
        public (string Key, JsonNode Node) MapFromDataToStorageModel(Hotel dataModel)
        {
            throw new NotImplementedException();
        }

        public Hotel MapFromStorageToDataModel((string Key, JsonNode Node) storageModel, GetRecordOptions? options = null)
        {
            throw new NotImplementedException();
        }
    }
}
