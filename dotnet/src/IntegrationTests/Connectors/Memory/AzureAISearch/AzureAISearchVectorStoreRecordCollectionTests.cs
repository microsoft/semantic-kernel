// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Azure;
using Azure.Search.Documents.Indexes;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Microsoft.SemanticKernel.Embeddings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.AzureAISearch;

#pragma warning disable CS0618 // VectorSearchFilter is obsolete

/// <summary>
/// Integration tests for <see cref="AzureAISearchVectorStoreRecordCollection{TRecord}"/> class.
/// Tests work with an Azure AI Search Instance.
/// </summary>
[Collection("AzureAISearchVectorStoreCollection")]
public sealed class AzureAISearchVectorStoreRecordCollectionTests(ITestOutputHelper output, AzureAISearchVectorStoreFixture fixture)
{
    // If null, all tests will be enabled
    private const string SkipReason = "Requires Azure AI Search Service instance up and running";

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CollectionExistsReturnsCollectionStateAsync(bool expectedExists)
    {
        // Arrange.
        var collectionName = expectedExists ? fixture.TestIndexName : "nonexistentcollection";
        var sut = new AzureAISearchVectorStoreRecordCollection<AzureAISearchHotel>(fixture.SearchIndexClient, collectionName);

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
        var hotel = await this.CreateTestHotelAsync("Upsert-1");
        var testCollectionName = $"{fixture.TestIndexName}-createtest";
        var options = new AzureAISearchVectorStoreRecordCollectionOptions<AzureAISearchHotel>
        {
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.VectorStoreRecordDefinition : null
        };
        var sut = new AzureAISearchVectorStoreRecordCollection<AzureAISearchHotel>(fixture.SearchIndexClient, testCollectionName, options);

        await sut.DeleteCollectionAsync();

        // Act
        await sut.CreateCollectionAsync();
        var upsertResult = await sut.UpsertAsync(hotel);
        var getResult = await sut.GetAsync("Upsert-1");
        var embedding = await fixture.EmbeddingGenerator.GenerateEmbeddingAsync("A great hotel");
        var actual = await sut.VectorizedSearchAsync(
            embedding,
            new()
            {
                IncludeVectors = true,
                OldFilter = new VectorSearchFilter().EqualTo("HotelName", "MyHotel Upsert-1")
            });

        // Assert
        var collectionExistResult = await sut.CollectionExistsAsync();
        Assert.True(collectionExistResult);
        await sut.DeleteCollectionAsync();

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

        var searchResults = await actual.Results.ToListAsync();
        Assert.Single(searchResults);
        var searchResultRecord = searchResults.First().Record;
        Assert.Equal(hotel.HotelName, searchResultRecord.HotelName);
        Assert.Equal(hotel.Description, searchResultRecord.Description);
        Assert.NotNull(searchResultRecord.DescriptionEmbedding);
        Assert.Equal(hotel.DescriptionEmbedding?.ToArray(), searchResultRecord.DescriptionEmbedding?.ToArray());
        Assert.Equal(hotel.Tags, searchResultRecord.Tags);
        Assert.Equal(hotel.ParkingIncluded, searchResultRecord.ParkingIncluded);
        Assert.Equal(hotel.LastRenovationDate, searchResultRecord.LastRenovationDate);
        Assert.Equal(hotel.Rating, searchResultRecord.Rating);

        // Output
        output.WriteLine(collectionExistResult.ToString());
        output.WriteLine(upsertResult);
        output.WriteLine(getResult.ToString());
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanDeleteCollectionAsync()
    {
        // Arrange
        var tempCollectionName = fixture.TestIndexName + "-delete";
        await AzureAISearchVectorStoreFixture.CreateIndexAsync(tempCollectionName, fixture.SearchIndexClient);
        var sut = new AzureAISearchVectorStoreRecordCollection<AzureAISearchHotel>(fixture.SearchIndexClient, tempCollectionName);

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
        // Arrange
        var options = new AzureAISearchVectorStoreRecordCollectionOptions<AzureAISearchHotel>
        {
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.VectorStoreRecordDefinition : null
        };
        var sut = new AzureAISearchVectorStoreRecordCollection<AzureAISearchHotel>(fixture.SearchIndexClient, fixture.TestIndexName, options);

        // Act
        var hotel = await this.CreateTestHotelAsync("Upsert-1");
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

        // Output
        output.WriteLine(upsertResult);
        output.WriteLine(getResult.ToString());
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanUpsertManyDocumentsToVectorStoreAsync()
    {
        // Arrange
        var sut = new AzureAISearchVectorStoreRecordCollection<AzureAISearchHotel>(fixture.SearchIndexClient, fixture.TestIndexName);

        // Act
        var results = sut.UpsertBatchAsync(
            [
                await this.CreateTestHotelAsync("UpsertMany-1"),
                await this.CreateTestHotelAsync("UpsertMany-2"),
                await this.CreateTestHotelAsync("UpsertMany-3"),
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
        var options = new AzureAISearchVectorStoreRecordCollectionOptions<AzureAISearchHotel>
        {
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.VectorStoreRecordDefinition : null
        };
        var sut = new AzureAISearchVectorStoreRecordCollection<AzureAISearchHotel>(fixture.SearchIndexClient, fixture.TestIndexName, options);

        // Act
        var getResult = await sut.GetAsync("BaseSet-1", new GetRecordOptions { IncludeVectors = includeVectors });

        // Assert
        Assert.NotNull(getResult);

        Assert.Equal("Hotel 1", getResult.HotelName);
        Assert.Equal("This is a great hotel", getResult.Description);
        Assert.Equal(includeVectors, getResult.DescriptionEmbedding != null);
        if (includeVectors)
        {
            var embedding = await fixture.EmbeddingGenerator.GenerateEmbeddingAsync("This is a great hotel");
            Assert.Equal(embedding, getResult.DescriptionEmbedding!.Value.ToArray());
        }
        else
        {
            Assert.Null(getResult.DescriptionEmbedding);
        }
        Assert.Equal(new[] { "pool", "air conditioning", "concierge" }, getResult.Tags);
        Assert.False(getResult.ParkingIncluded);
        Assert.Equal(new DateTimeOffset(1970, 1, 18, 0, 0, 0, TimeSpan.Zero), getResult.LastRenovationDate);
        Assert.Equal(3.6, getResult.Rating);

        // Output
        output.WriteLine(getResult.ToString());
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanGetManyDocumentsFromVectorStoreAsync()
    {
        // Arrange
        var sut = new AzureAISearchVectorStoreRecordCollection<AzureAISearchHotel>(fixture.SearchIndexClient, fixture.TestIndexName);

        // Act
        // Also include one non-existing key to test that the operation does not fail for these and returns only the found ones.
        var hotels = sut.GetBatchAsync(["BaseSet-1", "BaseSet-2", "BaseSet-3", "BaseSet-5", "BaseSet-4"], new GetRecordOptions { IncludeVectors = true });

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

    [Theory(Skip = SkipReason)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanRemoveDocumentFromVectorStoreAsync(bool useRecordDefinition)
    {
        // Arrange
        var options = new AzureAISearchVectorStoreRecordCollectionOptions<AzureAISearchHotel>
        {
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.VectorStoreRecordDefinition : null
        };
        var sut = new AzureAISearchVectorStoreRecordCollection<AzureAISearchHotel>(fixture.SearchIndexClient, fixture.TestIndexName);
        await sut.UpsertAsync(await this.CreateTestHotelAsync("Remove-1"));

        // Act
        await sut.DeleteAsync("Remove-1");
        // Also delete a non-existing key to test that the operation does not fail for these.
        await sut.DeleteAsync("Remove-2");

        // Assert
        Assert.Null(await sut.GetAsync("Remove-1", new GetRecordOptions { IncludeVectors = true }));
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanRemoveManyDocumentsFromVectorStoreAsync()
    {
        // Arrange
        var sut = new AzureAISearchVectorStoreRecordCollection<AzureAISearchHotel>(fixture.SearchIndexClient, fixture.TestIndexName);
        await sut.UpsertAsync(await this.CreateTestHotelAsync("RemoveMany-1"));
        await sut.UpsertAsync(await this.CreateTestHotelAsync("RemoveMany-2"));
        await sut.UpsertAsync(await this.CreateTestHotelAsync("RemoveMany-3"));

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
        var sut = new AzureAISearchVectorStoreRecordCollection<AzureAISearchHotel>(fixture.SearchIndexClient, fixture.TestIndexName);

        // Act & Assert
        Assert.Null(await sut.GetAsync("BaseSet-5", new GetRecordOptions { IncludeVectors = true }));
    }

    [Fact(Skip = SkipReason)]
    public async Task ItThrowsOperationExceptionForFailedConnectionAsync()
    {
        // Arrange
        var searchIndexClient = new SearchIndexClient(new Uri("https://localhost:12345"), new AzureKeyCredential("12345"));
        var sut = new AzureAISearchVectorStoreRecordCollection<AzureAISearchHotel>(searchIndexClient, fixture.TestIndexName);

        // Act & Assert
        await Assert.ThrowsAsync<VectorStoreOperationException>(async () => await sut.GetAsync("BaseSet-1", new GetRecordOptions { IncludeVectors = true }));
    }

    [Fact(Skip = SkipReason)]
    public async Task ItThrowsOperationExceptionForFailedAuthenticationAsync()
    {
        // Arrange
        var searchIndexClient = new SearchIndexClient(new Uri(fixture.Config.ServiceUrl), new AzureKeyCredential("12345"));
        var sut = new AzureAISearchVectorStoreRecordCollection<AzureAISearchHotel>(searchIndexClient, fixture.TestIndexName);

        // Act & Assert
        await Assert.ThrowsAsync<VectorStoreOperationException>(async () => await sut.GetAsync("BaseSet-1", new GetRecordOptions { IncludeVectors = true }));
    }

    [Fact(Skip = SkipReason)]
    public async Task ItThrowsMappingExceptionForFailedMapperAsync()
    {
        // Arrange
        var options = new AzureAISearchVectorStoreRecordCollectionOptions<AzureAISearchHotel> { JsonObjectCustomMapper = new FailingMapper() };
        var sut = new AzureAISearchVectorStoreRecordCollection<AzureAISearchHotel>(fixture.SearchIndexClient, fixture.TestIndexName, options);

        // Act & Assert
        await Assert.ThrowsAsync<VectorStoreRecordMappingException>(async () => await sut.GetAsync("BaseSet-1", new GetRecordOptions { IncludeVectors = true }));
    }

    [Theory(Skip = SkipReason)]
    [InlineData("equality", true)]
    [InlineData("tagContains", false)]
    public async Task ItCanSearchWithVectorAndFiltersAsync(string option, bool includeVectors)
    {
        // Arrange.
        var sut = new AzureAISearchVectorStoreRecordCollection<AzureAISearchHotel>(fixture.SearchIndexClient, fixture.TestIndexName);

        // Act.
        var filter = option == "equality" ? new VectorSearchFilter().EqualTo("HotelName", "Hotel 3") : new VectorSearchFilter().AnyTagEqualTo("Tags", "bar");
        var actual = await sut.VectorizedSearchAsync(
            await fixture.EmbeddingGenerator.GenerateEmbeddingAsync("A great hotel"),
            new()
            {
                IncludeVectors = includeVectors,
                VectorProperty = r => r.DescriptionEmbedding,
                OldFilter = filter,
            });

        // Assert.
        var searchResults = await actual.Results.ToListAsync();
        Assert.Single(searchResults);
        var searchResult = searchResults.First();
        Assert.Equal("BaseSet-3", searchResult.Record.HotelId);
        Assert.Equal("Hotel 3", searchResult.Record.HotelName);
        Assert.Equal("This is a great hotel", searchResult.Record.Description);
        Assert.Equal(new[] { "air conditioning", "bar", "continental breakfast" }, searchResult.Record.Tags);
        Assert.True(searchResult.Record.ParkingIncluded);
        Assert.Equal(new DateTimeOffset(2015, 9, 20, 0, 0, 0, TimeSpan.Zero), searchResult.Record.LastRenovationDate);
        Assert.Equal(4.8, searchResult.Record.Rating);
        if (includeVectors)
        {
            Assert.NotNull(searchResult.Record.DescriptionEmbedding);
            var embedding = await fixture.EmbeddingGenerator.GenerateEmbeddingAsync("This is a great hotel");
            Assert.Equal(embedding, searchResult.Record.DescriptionEmbedding!.Value.ToArray());
        }
        else
        {
            Assert.Null(searchResult.Record.DescriptionEmbedding);
        }
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanSearchWithVectorizableTextAndFiltersAsync()
    {
        // Arrange.
        var sut = new AzureAISearchVectorStoreRecordCollection<AzureAISearchHotel>(fixture.SearchIndexClient, fixture.TestIndexName);

        // Act.
        var filter = new VectorSearchFilter().EqualTo("HotelName", "Hotel 3");
        var actual = await sut.VectorizableTextSearchAsync(
            "A hotel with great views.",
            new()
            {
                VectorProperty = r => r.DescriptionEmbedding,
                OldFilter = filter,
            });

        // Assert.
        var searchResults = await actual.Results.ToListAsync();
        Assert.Single(searchResults);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanUpsertAndRetrieveUsingTheGenericMapperAsync()
    {
        // Arrange
        var options = new AzureAISearchVectorStoreRecordCollectionOptions<VectorStoreGenericDataModel<string>>
        {
            VectorStoreRecordDefinition = fixture.VectorStoreRecordDefinition
        };
        var sut = new AzureAISearchVectorStoreRecordCollection<VectorStoreGenericDataModel<string>>(fixture.SearchIndexClient, fixture.TestIndexName, options);

        // Act
        var baseSetGetResult = await sut.GetAsync("BaseSet-1", new GetRecordOptions { IncludeVectors = true });
        var baseSetEmbedding = await fixture.EmbeddingGenerator.GenerateEmbeddingAsync("This is a great hotel");
        var genericMapperEmbedding = await fixture.EmbeddingGenerator.GenerateEmbeddingAsync("This is a generic mapper hotel");
        var upsertResult = await sut.UpsertAsync(new VectorStoreGenericDataModel<string>("GenericMapper-1")
        {
            Data =
            {
                { "HotelName", "Generic Mapper Hotel" },
                { "Description", "This is a generic mapper hotel" },
                { "Tags", new string[] { "generic" } },
                { "ParkingIncluded", false },
                { "LastRenovationDate", new DateTimeOffset(1970, 1, 18, 0, 0, 0, TimeSpan.Zero) },
                { "Rating", 3.6d }
            },
            Vectors =
            {
                { "DescriptionEmbedding", genericMapperEmbedding }
            }
        });
        var localGetResult = await sut.GetAsync("GenericMapper-1", new GetRecordOptions { IncludeVectors = true });

        // Assert
        Assert.NotNull(baseSetGetResult);
        Assert.Equal("Hotel 1", baseSetGetResult.Data["HotelName"]);
        Assert.Equal("This is a great hotel", baseSetGetResult.Data["Description"]);
        Assert.Equal(new[] { "pool", "air conditioning", "concierge" }, baseSetGetResult.Data["Tags"]);
        Assert.False((bool?)baseSetGetResult.Data["ParkingIncluded"]);
        Assert.Equal(new DateTimeOffset(1970, 1, 18, 0, 0, 0, TimeSpan.Zero), baseSetGetResult.Data["LastRenovationDate"]);
        Assert.Equal(3.6d, baseSetGetResult.Data["Rating"]);
        Assert.Equal(baseSetEmbedding, (ReadOnlyMemory<float>)baseSetGetResult.Vectors["DescriptionEmbedding"]!);

        Assert.NotNull(upsertResult);
        Assert.Equal("GenericMapper-1", upsertResult);

        Assert.NotNull(localGetResult);
        Assert.Equal("Generic Mapper Hotel", localGetResult.Data["HotelName"]);
        Assert.Equal("This is a generic mapper hotel", localGetResult.Data["Description"]);
        Assert.Equal(new[] { "generic" }, localGetResult.Data["Tags"]);
        Assert.False((bool?)localGetResult.Data["ParkingIncluded"]);
        Assert.Equal(new DateTimeOffset(1970, 1, 18, 0, 0, 0, TimeSpan.Zero), localGetResult.Data["LastRenovationDate"]);
        Assert.Equal(3.6d, localGetResult.Data["Rating"]);
        Assert.Equal(genericMapperEmbedding, (ReadOnlyMemory<float>)localGetResult.Vectors["DescriptionEmbedding"]!);
    }

    private async Task<AzureAISearchHotel> CreateTestHotelAsync(string hotelId) => new()
    {
        HotelId = hotelId,
        HotelName = $"MyHotel {hotelId}",
        Description = "My Hotel is great.",
        DescriptionEmbedding = await fixture.EmbeddingGenerator.GenerateEmbeddingAsync("My hotel is great"),
        Tags = ["pool", "air conditioning", "concierge"],
        ParkingIncluded = true,
        LastRenovationDate = new DateTimeOffset(1970, 1, 18, 0, 0, 0, TimeSpan.Zero),
        Rating = 3.6
    };

    private sealed class FailingMapper : IVectorStoreRecordMapper<AzureAISearchHotel, JsonObject>
    {
        public JsonObject MapFromDataToStorageModel(AzureAISearchHotel dataModel)
        {
            throw new NotImplementedException();
        }

        public AzureAISearchHotel MapFromStorageToDataModel(JsonObject storageModel, StorageToDataModelMapperOptions options)
        {
            throw new NotImplementedException();
        }
    }
}
