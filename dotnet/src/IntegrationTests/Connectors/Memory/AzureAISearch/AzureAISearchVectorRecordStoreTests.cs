// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Azure;
using Azure.Search.Documents.Indexes;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Microsoft.SemanticKernel.Memory;
using Xunit;
using Xunit.Abstractions;
using static SemanticKernel.IntegrationTests.Connectors.Memory.AzureAISearch.AzureAISearchVectorStoreFixture;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.AzureAISearch;

/// <summary>
/// Integration tests for <see cref="AzureAISearchVectorRecordStore{TRecord}"/> class.
/// Tests work with Azure AI Search Instance.
/// </summary>
[Collection("AzureAISearchVectorStoreCollection")]
public sealed class AzureAISearchVectorRecordStoreTests(ITestOutputHelper output, AzureAISearchVectorStoreFixture fixture) : IClassFixture<AzureAISearchVectorStoreFixture>
{
    // If null, all tests will be enabled
    private const string SkipReason = null; //"Requires Azure AI Search Service instance up and running";

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanUpsertDocumentToVectorStoreAsync(bool useRecordDefinition)
    {
        // Arrange
        var options = new AzureAISearchVectorRecordStoreOptions<Hotel>
        {
            DefaultCollectionName = fixture.TestIndexName,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.VectorStoreRecordDefinition : null
        };
        var sut = new AzureAISearchVectorRecordStore<Hotel>(fixture.SearchIndexClient, options);

        // Act
        var hotel = CreateTestHotel("Upsert-1");
        var upsertResult = await sut.UpsertAsync(hotel);
        var getResult = await sut.GetAsync("Upsert-1");

        // Assert
        Assert.NotNull(upsertResult);
        Assert.Equal("Upsert-1", upsertResult);

        Assert.NotNull(getResult);
        Assert.Equal(hotel.HotelName, getResult.HotelName);
        Assert.Equal(hotel.Description, getResult.Description);
        Assert.NotNull(getResult.DescriptionEmbedding);
        Assert.Equal(hotel.DescriptionEmbedding?.ToArray(), getResult.DescriptionEmbedding?.ToArray());
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
    public async Task ItCanUpsertManyDocumentsToVectorStoreAsync()
    {
        // Arrange
        var options = new AzureAISearchVectorRecordStoreOptions<Hotel>
        {
            DefaultCollectionName = fixture.TestIndexName
        };
        var sut = new AzureAISearchVectorRecordStore<Hotel>(fixture.SearchIndexClient, options);

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
    public async Task ItCanGetDocumentFromVectorStoreAsync(bool includeVectors, bool useRecordDefinition)
    {
        // Arrange
        var options = new AzureAISearchVectorRecordStoreOptions<Hotel>
        {
            DefaultCollectionName = fixture.TestIndexName,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.VectorStoreRecordDefinition : null
        };
        var sut = new AzureAISearchVectorRecordStore<Hotel>(fixture.SearchIndexClient, options);

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
    public async Task ItCanGetManyDocumentsFromVectorStoreAsync()
    {
        // Arrange
        var options = new AzureAISearchVectorRecordStoreOptions<Hotel>
        {
            DefaultCollectionName = fixture.TestIndexName
        };
        var sut = new AzureAISearchVectorRecordStore<Hotel>(fixture.SearchIndexClient, options);

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
        var options = new AzureAISearchVectorRecordStoreOptions<Hotel>
        {
            DefaultCollectionName = fixture.TestIndexName
        };
        var sut = new AzureAISearchVectorRecordStore<Hotel>(fixture.SearchIndexClient, options);

        // Act.
        await Assert.ThrowsAsync<VectorStoreOperationException>(async () => await sut.GetBatchAsync(["BaseSet-1", "BaseSet-5", "BaseSet-2"]).ToListAsync());
    }

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanRemoveDocumentFromVectorStoreAsync(bool useRecordDefinition)
    {
        // Arrange
        var options = new AzureAISearchVectorRecordStoreOptions<Hotel>
        {
            DefaultCollectionName = fixture.TestIndexName,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.VectorStoreRecordDefinition : null
        };
        var sut = new AzureAISearchVectorRecordStore<Hotel>(fixture.SearchIndexClient, options);
        await sut.UpsertAsync(CreateTestHotel("Remove-1"));

        // Act
        await sut.DeleteAsync("Remove-1");

        // Assert
        await Assert.ThrowsAsync<VectorStoreOperationException>(async () => await sut.GetAsync("Remove-1", new GetRecordOptions { IncludeVectors = true }));
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanRemoveManyDocumentsFromVectorStoreAsync()
    {
        // Arrange
        var options = new AzureAISearchVectorRecordStoreOptions<Hotel>
        {
            DefaultCollectionName = fixture.TestIndexName
        };
        var sut = new AzureAISearchVectorRecordStore<Hotel>(fixture.SearchIndexClient, options);
        await sut.UpsertAsync(CreateTestHotel("RemoveMany-1"));
        await sut.UpsertAsync(CreateTestHotel("RemoveMany-2"));
        await sut.UpsertAsync(CreateTestHotel("RemoveMany-3"));

        // Act
        await sut.DeleteBatchAsync(["RemoveMany-1", "RemoveMany-2", "RemoveMany-3"]);

        // Assert
        await Assert.ThrowsAsync<VectorStoreOperationException>(async () => await sut.GetAsync("RemoveMany-1", new GetRecordOptions { IncludeVectors = true }));
        await Assert.ThrowsAsync<VectorStoreOperationException>(async () => await sut.GetAsync("RemoveMany-2", new GetRecordOptions { IncludeVectors = true }));
        await Assert.ThrowsAsync<VectorStoreOperationException>(async () => await sut.GetAsync("RemoveMany-3", new GetRecordOptions { IncludeVectors = true }));
    }

    [Fact(Skip = SkipReason)]
    public async Task ItThrowsOperationExceptionForFailedConnectionAsync()
    {
        // Arrange
        var options = new AzureAISearchVectorRecordStoreOptions<Hotel> { DefaultCollectionName = fixture.TestIndexName };
        var searchIndexClient = new SearchIndexClient(new Uri("https://localhost:12345"), new AzureKeyCredential("12345"));
        var sut = new AzureAISearchVectorRecordStore<Hotel>(searchIndexClient, options);

        // Act & Assert
        await Assert.ThrowsAsync<VectorStoreOperationException>(async () => await sut.GetAsync("BaseSet-1", new GetRecordOptions { IncludeVectors = true }));
    }

    [Fact(Skip = SkipReason)]
    public async Task ItThrowsOperationExceptionForFailedAuthenticationAsync()
    {
        // Arrange
        var options = new AzureAISearchVectorRecordStoreOptions<Hotel> { DefaultCollectionName = fixture.TestIndexName };
        var searchIndexClient = new SearchIndexClient(new Uri(fixture.Config.ServiceUrl), new AzureKeyCredential("12345"));
        var sut = new AzureAISearchVectorRecordStore<Hotel>(searchIndexClient, options);

        // Act & Assert
        await Assert.ThrowsAsync<VectorStoreOperationException>(async () => await sut.GetAsync("BaseSet-1", new GetRecordOptions { IncludeVectors = true }));
    }

    [Fact(Skip = SkipReason)]
    public async Task ItThrowsMappingExceptionForFailedMapperAsync()
    {
        // Arrange
        var options = new AzureAISearchVectorRecordStoreOptions<Hotel> { DefaultCollectionName = fixture.TestIndexName, MapperType = AzureAISearchRecordMapperType.JsonObjectCustomMapper, JsonObjectCustomMapper = new FailingMapper() };
        var sut = new AzureAISearchVectorRecordStore<Hotel>(fixture.SearchIndexClient, options);

        // Act & Assert
        await Assert.ThrowsAsync<VectorStoreRecordMappingException>(async () => await sut.GetAsync("BaseSet-1", new GetRecordOptions { IncludeVectors = true }));
    }

    private static Hotel CreateTestHotel(string hotelId) => new()
    {
        HotelId = hotelId,
        HotelName = $"MyHotel {hotelId}",
        Description = "My Hotel is great.",
        DescriptionEmbedding = new[] { 30f, 31f, 32f, 33f },
        Tags = ["pool", "air conditioning", "concierge"],
        ParkingIncluded = true,
        LastRenovationDate = new DateTimeOffset(1970, 1, 18, 0, 0, 0, TimeSpan.Zero),
        Rating = 3.6,
        Address = new Address
        {
            City = "New York",
            Country = "USA"
        }
    };

    private sealed class FailingMapper : IVectorStoreRecordMapper<Hotel, JsonObject>
    {
        public JsonObject MapFromDataToStorageModel(Hotel dataModel)
        {
            throw new NotImplementedException();
        }

        public Hotel MapFromStorageToDataModel(JsonObject storageModel, GetRecordOptions? options = null)
        {
            throw new NotImplementedException();
        }
    }
}
