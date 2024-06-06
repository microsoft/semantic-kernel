// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Microsoft.SemanticKernel.Memory;
using Xunit;
using Xunit.Abstractions;
using static SemanticKernel.IntegrationTests.Connectors.Memory.AzureAISearch.AzureAISearchMemoryFixture;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.AzureAISearch;

/// <summary>
/// Integration tests for <see cref="AzureAISearchMemoryRecordService{TDataModel}"/> class.
/// Tests work with Azure AI Search Instance.
/// </summary>
[Collection("AzureAISearchMemoryCollection")]
public sealed class AzureAISearchMemoryRecordServiceTests(ITestOutputHelper output, AzureAISearchMemoryFixture fixture) : IClassFixture<AzureAISearchMemoryFixture>
{
    // If null, all tests will be enabled
    private const string SkipReason = null; //"Requires Azure AI Search Service instance up and running";

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanUpsertDocumentToMemoryStoreAsync(bool useRecordDefinition)
    {
        // Arrange
        var options = new AzureAISearchMemoryRecordServiceOptions<Hotel>
        {
            MemoryRecordDefinition = useRecordDefinition ? fixture.MemoryRecordDefinition : null
        };
        var sut = new AzureAISearchMemoryRecordService<Hotel>(fixture.SearchIndexClient, fixture.TestIndexName, options);

        // Act
        var hotel = new Hotel()
        {
            HotelId = "Upsert-1",
            HotelName = "MyHotel1",
            Description = "My Hotel is great.",
            DescriptionEmbedding = new[] { 30f, 31f, 32f, 33f },
            Tags = new[] { "pool", "air conditioning", "concierge" },
            ParkingIncluded = true,
            LastRenovationDate = new DateTimeOffset(1970, 1, 18, 0, 0, 0, TimeSpan.Zero),
            Rating = 3.6,
            Address = new Address()
            {
                City = "New York",
                Country = "USA"
            }
        };
        var upsertResult = await sut.UpsertAsync(hotel);
        var getResult = await sut.GetAsync("Upsert-1");

        // Assert
        Assert.NotNull(upsertResult);
        Assert.Equal("Upsert-1", upsertResult);

        Assert.NotNull(getResult);
        Assert.Equal(hotel.HotelName, getResult.HotelName);
        Assert.Equal(hotel.Description, getResult.Description);
        Assert.NotNull(getResult.DescriptionEmbedding);
        Assert.Equal(hotel.DescriptionEmbedding.Value, getResult.DescriptionEmbedding.Value);
        Assert.Equal(hotel.Tags, getResult.Tags);
        Assert.Equal(hotel.ParkingIncluded, getResult.ParkingIncluded);
        Assert.Equal(hotel.LastRenovationDate, getResult.LastRenovationDate);
        Assert.Equal(hotel.Rating, getResult.Rating);
        Assert.Equal(hotel.Address.City, getResult.Address.City);
        Assert.Equal(hotel.Address.Country, getResult.Address.Country);

        // Output
        output.WriteLine(upsertResult);
        output.WriteLine(getResult.ToString());
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanUpsertManyDocumentsToMemoryStoreAsync()
    {
        // Arrange
        var sut = new AzureAISearchMemoryRecordService<Hotel>(fixture.SearchIndexClient, fixture.TestIndexName);

        // Act
        var results = sut.UpsertBatchAsync(
            [
                CreateTestHotel("UpsertMany-1"),
                CreateTestHotel("UpsertMany-2"),
                CreateTestHotel("UpsertMany-3"),
            ]);

        // Assert
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
    public async Task ItCanGetDocumentFromMemoryStoreAsync(bool includeVectors, bool useRecordDefinition)
    {
        // Arrange
        var options = new AzureAISearchMemoryRecordServiceOptions<Hotel>
        {
            MemoryRecordDefinition = useRecordDefinition ? fixture.MemoryRecordDefinition : null
        };
        var sut = new AzureAISearchMemoryRecordService<Hotel>(fixture.SearchIndexClient, fixture.TestIndexName, options);

        // Act
        var getResult = await sut.GetAsync("BaseSet-1", new GetRecordOptions { IncludeVectors = includeVectors });

        // Assert
        Assert.NotNull(getResult);

        Assert.Equal("Hotel 1", getResult.HotelName);
        Assert.Equal("This is a great hotel", getResult.Description);
        Assert.Equal(includeVectors, getResult.DescriptionEmbedding != null);
        if (includeVectors)
        {
            Assert.Equal(new[] { 30f, 31f, 32f, 33f }, getResult.DescriptionEmbedding!.Value.ToArray());
        }
        Assert.Equal(new[] { "pool", "air conditioning", "concierge" }, getResult.Tags);
        Assert.False(getResult.ParkingIncluded);
        Assert.Equal(new DateTimeOffset(1970, 1, 18, 0, 0, 0, TimeSpan.Zero), getResult.LastRenovationDate);
        Assert.Equal(3.6, getResult.Rating);
        Assert.Equal("New York", getResult.Address.City);
        Assert.Equal("USA", getResult.Address.Country);

        // Output
        output.WriteLine(getResult.ToString());
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanGetManyDocumentsFromMemoryStoreAsync()
    {
        // Arrange
        var sut = new AzureAISearchMemoryRecordService<Hotel>(fixture.SearchIndexClient, fixture.TestIndexName);

        // Act
        var hotels = sut.GetBatchAsync(["BaseSet-1", "BaseSet-2", "BaseSet-3", "BaseSet-4"], new GetRecordOptions { IncludeVectors = true });

        // Assert
        Assert.NotNull(hotels);
        var hotelsList = await hotels.ToListAsync();
        Assert.Equal(4, hotelsList.Count);

        // Output
        foreach (var hotel in hotelsList)
        {
            output.WriteLine(hotel.ToString());
        }
    }

    [Fact]
    public async Task ItThrowsForPartialGetBatchResultAsync()
    {
        // Arrange.
        var sut = new AzureAISearchMemoryRecordService<Hotel>(fixture.SearchIndexClient, fixture.TestIndexName);

        // Act.
        await Assert.ThrowsAsync<MemoryServiceOperationException>(async () => await sut.GetBatchAsync(["BaseSet-1", "BaseSet-5", "BaseSet-2"]).ToListAsync());
    }

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanRemoveDocumentFromMemoryStoreAsync(bool useRecordDefinition)
    {
        // Arrange
        var options = new AzureAISearchMemoryRecordServiceOptions<Hotel>
        {
            MemoryRecordDefinition = useRecordDefinition ? fixture.MemoryRecordDefinition : null
        };
        var sut = new AzureAISearchMemoryRecordService<Hotel>(fixture.SearchIndexClient, fixture.TestIndexName, options);
        await sut.UpsertAsync(CreateTestHotel("Remove-1"));

        // Act
        await sut.DeleteAsync("Remove-1");

        // Assert
        await Assert.ThrowsAsync<MemoryServiceOperationException>(async () => await sut.GetAsync("Remove-1", new GetRecordOptions { IncludeVectors = true }));
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanRemoveManyDocumentsFromMemoryStoreAsync()
    {
        // Arrange
        var sut = new AzureAISearchMemoryRecordService<Hotel>(fixture.SearchIndexClient, fixture.TestIndexName);
        await sut.UpsertAsync(CreateTestHotel("RemoveMany-1"));
        await sut.UpsertAsync(CreateTestHotel("RemoveMany-2"));
        await sut.UpsertAsync(CreateTestHotel("RemoveMany-3"));

        // Act
        await sut.DeleteBatchAsync(["RemoveMany-1", "RemoveMany-2", "RemoveMany-3"]);

        // Assert
        await Assert.ThrowsAsync<MemoryServiceOperationException>(async () => await sut.GetAsync("RemoveMany-1", new GetRecordOptions { IncludeVectors = true }));
        await Assert.ThrowsAsync<MemoryServiceOperationException>(async () => await sut.GetAsync("RemoveMany-2", new GetRecordOptions { IncludeVectors = true }));
        await Assert.ThrowsAsync<MemoryServiceOperationException>(async () => await sut.GetAsync("RemoveMany-3", new GetRecordOptions { IncludeVectors = true }));
    }

    private static Hotel CreateTestHotel(string hotelId) => new()
    {
        HotelId = hotelId,
        HotelName = $"MyHotel {hotelId}",
        Description = "My Hotel is great.",
        DescriptionEmbedding = new[] { 30f, 31f, 32f, 33f },
        Tags = new[] { "pool", "air conditioning", "concierge" },
        ParkingIncluded = true,
        LastRenovationDate = new DateTimeOffset(1970, 1, 18, 0, 0, 0, TimeSpan.Zero),
        Rating = 3.6,
        Address = new Address
        {
            City = "New York",
            Country = "USA"
        }
    };
}
