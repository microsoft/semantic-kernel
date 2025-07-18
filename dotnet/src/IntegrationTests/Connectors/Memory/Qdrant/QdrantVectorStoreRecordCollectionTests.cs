// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Qdrant.Client.Grpc;
using Xunit;
using Xunit.Abstractions;
using static SemanticKernel.IntegrationTests.Connectors.Memory.Qdrant.QdrantVectorStoreFixture;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Qdrant;

#pragma warning disable CA1859 // Use concrete types when possible for improved performance
#pragma warning disable CS0618 // VectorSearchFilter is obsolete

/// <summary>
/// Contains tests for the <see cref="QdrantCollection{TKey, TRecord}"/> class.
/// </summary>
/// <param name="output">Used for logging.</param>
/// <param name="fixture">Qdrant setup and teardown.</param>
[Collection("QdrantVectorStoreCollection")]
public sealed class QdrantVectorStoreRecordCollectionTests(ITestOutputHelper output, QdrantVectorStoreFixture fixture)
{
    [Theory]
    [InlineData("singleVectorHotels", true)]
    [InlineData("nonexistentcollection", false)]
    public async Task CollectionExistsReturnsCollectionStateAsync(string collectionName, bool expectedExists)
    {
        // Arrange.
        using var sut = new QdrantCollection<ulong, HotelInfo>(fixture.QdrantClient, collectionName, ownsClient: false);

        // Act.
        var actual = await sut.CollectionExistsAsync();

        // Assert.
        Assert.Equal(expectedExists, actual);
    }

    [Theory]
    [InlineData(true, true)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(false, false)]
    public async Task ItCanCreateACollectionUpsertGetAndSearchAsync(bool hasNamedVectors, bool useRecordDefinition)
    {
        // Arrange
        var collectionNamePostfix1 = useRecordDefinition ? "WithDefinition" : "WithType";
        var collectionNamePostfix2 = hasNamedVectors ? "HasNamedVectors" : "SingleUnnamedVector";
        var testCollectionName = $"createtest{collectionNamePostfix1}{collectionNamePostfix2}";

        var options = new QdrantCollectionOptions
        {
            HasNamedVectors = hasNamedVectors,
            Definition = useRecordDefinition ? fixture.HotelVectorStoreRecordDefinition : null
        };
        using var sut = new QdrantCollection<ulong, HotelInfo>(fixture.QdrantClient, testCollectionName, ownsClient: false, options);

        var record = await this.CreateTestHotelAsync(30, fixture.EmbeddingGenerator);

        // Act
        await sut.EnsureCollectionExistsAsync();
        await sut.UpsertAsync(record);
        var getResult = await sut.GetAsync(30, new() { IncludeVectors = true });
        var vector = (await fixture.EmbeddingGenerator.GenerateAsync("A great hotel")).Vector;
        var searchResults = await sut.SearchAsync(
            vector,
            top: 3,
            new() { OldFilter = new VectorSearchFilter().EqualTo("HotelCode", 30).AnyTagEqualTo("Tags", "t2") }).ToListAsync();

        // Assert
        var collectionExistResult = await sut.CollectionExistsAsync();
        Assert.True(collectionExistResult);
        await sut.EnsureCollectionDeletedAsync();

        Assert.Equal(record.HotelId, getResult?.HotelId);
        Assert.Equal(record.HotelName, getResult?.HotelName);
        Assert.Equal(record.HotelCode, getResult?.HotelCode);
        Assert.Equal(record.HotelRating, getResult?.HotelRating);
        Assert.Equal(record.ParkingIncluded, getResult?.ParkingIncluded);
        Assert.Equal(record.LastRenovationDate, getResult?.LastRenovationDate);
        Assert.Equal(record.Tags.ToArray(), getResult?.Tags.ToArray());
        Assert.Equal(record.Description, getResult?.Description);

        Assert.Single(searchResults);
        var searchResultRecord = searchResults.First().Record;
        Assert.Equal(record.HotelId, searchResultRecord?.HotelId);
        Assert.Equal(record.HotelName, searchResultRecord?.HotelName);
        Assert.Equal(record.HotelCode, searchResultRecord?.HotelCode);
        Assert.Equal(record.HotelRating, searchResultRecord?.HotelRating);
        Assert.Equal(record.ParkingIncluded, searchResultRecord?.ParkingIncluded);
        Assert.Equal(record.LastRenovationDate, searchResultRecord?.LastRenovationDate);
        Assert.Equal(record.Tags.ToArray(), searchResultRecord?.Tags.ToArray());
        Assert.Equal(record.Description, searchResultRecord?.Description);

        // Output
        output.WriteLine(collectionExistResult.ToString());
        output.WriteLine(getResult?.ToString());
    }

    [Fact]
    public async Task ItCanDeleteCollectionAsync()
    {
        // Arrange
        var tempCollectionName = "temp-test";
        await fixture.QdrantClient.CreateCollectionAsync(
            tempCollectionName,
            new VectorParams { Size = 4, Distance = Distance.Cosine });

        using var sut = new QdrantCollection<ulong, HotelInfo>(fixture.QdrantClient, tempCollectionName, ownsClient: false);

        // Act
        await sut.EnsureCollectionDeletedAsync();

        // Assert
        Assert.False(await sut.CollectionExistsAsync());
    }

    [Theory]
    [InlineData(true, "singleVectorHotels", false)]
    [InlineData(false, "singleVectorHotels", false)]
    [InlineData(true, "namedVectorsHotels", true)]
    [InlineData(false, "namedVectorsHotels", true)]
    public async Task ItCanUpsertDocumentToVectorStoreAsync(bool useRecordDefinition, string collectionName, bool hasNamedVectors)
    {
        // Arrange.
        var options = new QdrantCollectionOptions
        {
            HasNamedVectors = hasNamedVectors,
            Definition = useRecordDefinition ? fixture.HotelVectorStoreRecordDefinition : null
        };
        using var sut = new QdrantCollection<ulong, HotelInfo>(fixture.QdrantClient, collectionName, ownsClient: false, options);

        var record = await this.CreateTestHotelAsync(20, fixture.EmbeddingGenerator);

        // Act.
        await sut.UpsertAsync(record);

        // Assert.
        var getResult = await sut.GetAsync(20, new RecordRetrievalOptions { IncludeVectors = true });
        Assert.Equal(record.HotelId, getResult?.HotelId);
        Assert.Equal(record.HotelName, getResult?.HotelName);
        Assert.Equal(record.HotelCode, getResult?.HotelCode);
        Assert.Equal(record.HotelRating, getResult?.HotelRating);
        Assert.Equal(record.ParkingIncluded, getResult?.ParkingIncluded);
        Assert.Equal(record.Tags.ToArray(), getResult?.Tags.ToArray());
        Assert.Equal(record.Description, getResult?.Description);

        // TODO: figure out why original array is different from the one we get back.
        //Assert.Equal(record.DescriptionEmbedding?.ToArray(), getResult?.DescriptionEmbedding?.ToArray());

        // Output.
        output.WriteLine(getResult?.ToString());
    }

    [Fact]
    public async Task ItCanUpsertAndRemoveDocumentWithGuidIdToVectorStoreAsync()
    {
        // Arrange.
        var options = new QdrantCollectionOptions { HasNamedVectors = false };
        using VectorStoreCollection<Guid, HotelInfoWithGuidId> sut = new QdrantCollection<Guid, HotelInfoWithGuidId>(fixture.QdrantClient, "singleVectorGuidIdHotels", ownsClient: false, options);

        var record = new HotelInfoWithGuidId
        {
            HotelId = Guid.Parse("55555555-5555-5555-5555-555555555555"),
            HotelName = "My Hotel 5",
            Description = "This is a great hotel.",
            DescriptionEmbedding = (await fixture.EmbeddingGenerator.GenerateAsync("This is a great hotel.")).Vector,
        };

        // Act.
        await sut.UpsertAsync(record);

        // Assert.
        var getResult = await sut.GetAsync(Guid.Parse("55555555-5555-5555-5555-555555555555"), new RecordRetrievalOptions { IncludeVectors = true });
        Assert.Equal(record.HotelId, getResult?.HotelId);
        Assert.Equal(record.HotelName, getResult?.HotelName);
        Assert.Equal(record.Description, getResult?.Description);

        // Act.
        await sut.DeleteAsync(Guid.Parse("55555555-5555-5555-5555-555555555555"));

        // Assert.
        Assert.Null(await sut.GetAsync(Guid.Parse("55555555-5555-5555-5555-555555555555")));

        // Output.
        output.WriteLine(getResult?.ToString());
    }

    [Theory]
    [InlineData(true, true, "singleVectorHotels", false)]
    [InlineData(true, false, "singleVectorHotels", false)]
    [InlineData(false, true, "singleVectorHotels", false)]
    [InlineData(false, false, "singleVectorHotels", false)]
    [InlineData(true, true, "namedVectorsHotels", true)]
    [InlineData(true, false, "namedVectorsHotels", true)]
    [InlineData(false, true, "namedVectorsHotels", true)]
    [InlineData(false, false, "namedVectorsHotels", true)]
    public async Task ItCanGetDocumentFromVectorStoreAsync(bool useRecordDefinition, bool withEmbeddings, string collectionName, bool hasNamedVectors)
    {
        // Arrange.
        var options = new QdrantCollectionOptions
        {
            HasNamedVectors = hasNamedVectors,
            Definition = useRecordDefinition ? fixture.HotelVectorStoreRecordDefinition : null
        };
        using var sut = new QdrantCollection<ulong, HotelInfo>(fixture.QdrantClient, collectionName, ownsClient: false, options);

        // Act.
        var getResult = await sut.GetAsync(11, new RecordRetrievalOptions { IncludeVectors = withEmbeddings });

        // Assert.
        Assert.Equal(11ul, getResult?.HotelId);
        Assert.Equal("My Hotel 11", getResult?.HotelName);
        Assert.Equal(11, getResult?.HotelCode);
        Assert.True(getResult?.ParkingIncluded);
        Assert.Equal(4.5f, getResult?.HotelRating);
        Assert.Equal(new DateTimeOffset(2025, 2, 10, 5, 10, 15, TimeSpan.Zero), getResult?.LastRenovationDate);
        Assert.Equal(2, getResult?.Tags.Count);
        Assert.Equal("t11.1", getResult?.Tags[0]);
        Assert.Equal("t11.2", getResult?.Tags[1]);
        Assert.Equal("This is a great hotel.", getResult?.Description);
        if (withEmbeddings)
        {
            Assert.NotNull(getResult?.DescriptionEmbedding);
        }
        else
        {
            Assert.Null(getResult?.DescriptionEmbedding);
        }

        // Output.
        output.WriteLine(getResult?.ToString());
    }

    [Theory]
    [InlineData(true, true)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(false, false)]
    public async Task ItCanGetDocumentWithGuidIdFromVectorStoreAsync(bool useRecordDefinition, bool withEmbeddings)
    {
        // Arrange.
        var options = new QdrantCollectionOptions
        {
            HasNamedVectors = false,
            Definition = useRecordDefinition ? fixture.HotelWithGuidIdVectorStoreRecordDefinition : null
        };
        using var sut = new QdrantCollection<Guid, HotelInfoWithGuidId>(fixture.QdrantClient, "singleVectorGuidIdHotels", ownsClient: false, options);

        // Act.
        var getResult = await sut.GetAsync(Guid.Parse("11111111-1111-1111-1111-111111111111"), new RecordRetrievalOptions { IncludeVectors = withEmbeddings });

        // Assert.
        Assert.Equal(Guid.Parse("11111111-1111-1111-1111-111111111111"), getResult?.HotelId);
        Assert.Equal("My Hotel 11", getResult?.HotelName);
        Assert.Equal("This is a great hotel.", getResult?.Description);
        if (withEmbeddings)
        {
            Assert.NotNull(getResult?.DescriptionEmbedding);
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
        var options = new QdrantCollectionOptions { HasNamedVectors = true };
        using var sut = new QdrantCollection<ulong, HotelInfo>(fixture.QdrantClient, "namedVectorsHotels", ownsClient: false, options);

        // Act
        // Also include one non-existing key to test that the operation does not fail for these and returns only the found ones.
        var hotels = sut.GetAsync([11, 15, 12], new RecordRetrievalOptions { IncludeVectors = true });

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

    [Theory]
    [InlineData(true, "singleVectorHotels", false)]
    [InlineData(false, "singleVectorHotels", false)]
    [InlineData(true, "namedVectorsHotels", true)]
    [InlineData(false, "namedVectorsHotels", true)]
    public async Task ItCanRemoveDocumentFromVectorStoreAsync(bool useRecordDefinition, string collectionName, bool hasNamedVectors)
    {
        // Arrange.
        var options = new QdrantCollectionOptions
        {
            HasNamedVectors = hasNamedVectors,
            Definition = useRecordDefinition ? fixture.HotelVectorStoreRecordDefinition : null
        };
        using var sut = new QdrantCollection<ulong, HotelInfo>(fixture.QdrantClient, collectionName, ownsClient: false, options);

        await sut.UpsertAsync(await this.CreateTestHotelAsync(20, fixture.EmbeddingGenerator));

        // Act.
        await sut.DeleteAsync(20);
        // Also delete a non-existing key to test that the operation does not fail for these.
        await sut.DeleteAsync(21);

        // Assert.
        Assert.Null(await sut.GetAsync(20));
    }

    [Theory]
    [InlineData(true, "singleVectorHotels", false)]
    [InlineData(false, "singleVectorHotels", false)]
    [InlineData(true, "namedVectorsHotels", true)]
    [InlineData(false, "namedVectorsHotels", true)]
    public async Task ItCanRemoveManyDocumentsFromVectorStoreAsync(bool useRecordDefinition, string collectionName, bool hasNamedVectors)
    {
        // Arrange.
        var options = new QdrantCollectionOptions
        {
            HasNamedVectors = hasNamedVectors,
            Definition = useRecordDefinition ? fixture.HotelVectorStoreRecordDefinition : null
        };
        using var sut = new QdrantCollection<ulong, HotelInfo>(fixture.QdrantClient, collectionName, ownsClient: false, options);

        await sut.UpsertAsync(await this.CreateTestHotelAsync(20, fixture.EmbeddingGenerator));

        // Act.
        // Also delete a non-existing key to test that the operation does not fail for these.
        await sut.DeleteAsync([20, 21]);

        // Assert.
        Assert.Null(await sut.GetAsync(20));
    }

    [Fact]
    public async Task ItReturnsNullWhenGettingNonExistentRecordAsync()
    {
        // Arrange
        var options = new QdrantCollectionOptions { HasNamedVectors = false };
        using var sut = new QdrantCollection<ulong, HotelInfo>(fixture.QdrantClient, "singleVectorHotels", ownsClient: false, options);

        // Act & Assert
        Assert.Null(await sut.GetAsync(15, new RecordRetrievalOptions { IncludeVectors = true }));
    }

    [Theory]
    [InlineData(true, "singleVectorHotels", false, "equality")]
    [InlineData(false, "singleVectorHotels", false, "equality")]
    [InlineData(true, "namedVectorsHotels", true, "equality")]
    [InlineData(false, "namedVectorsHotels", true, "equality")]
    [InlineData(true, "singleVectorHotels", false, "tagContains")]
    [InlineData(false, "singleVectorHotels", false, "tagContains")]
    [InlineData(true, "namedVectorsHotels", true, "tagContains")]
    [InlineData(false, "namedVectorsHotels", true, "tagContains")]
    public async Task ItCanSearchWithFilterAsync(bool useRecordDefinition, string collectionName, bool hasNamedVectors, string filterType)
    {
        // Arrange.
        var options = new QdrantCollectionOptions
        {
            HasNamedVectors = hasNamedVectors,
            Definition = useRecordDefinition ? fixture.HotelVectorStoreRecordDefinition : null
        };
        using var sut = new QdrantCollection<ulong, HotelInfo>(fixture.QdrantClient, collectionName, ownsClient: false, options);

        // Act.
        var vector = (await fixture.EmbeddingGenerator.GenerateAsync("A great hotel")).Vector;
        var filter = filterType == "equality" ? new VectorSearchFilter().EqualTo("HotelName", "My Hotel 13").EqualTo("LastRenovationDate", new DateTimeOffset(2020, 02, 01, 0, 0, 0, TimeSpan.Zero)) : new VectorSearchFilter().AnyTagEqualTo("Tags", "t13.2");
        var searchResults = await sut.SearchAsync(
            vector,
            top: 3,
            new()
            {
                OldFilter = filter
            }).ToListAsync();

        // Assert.
        Assert.Single(searchResults);

        var searchResultRecord = searchResults.First().Record;
        Assert.Equal(13ul, searchResultRecord?.HotelId);
        Assert.Equal("My Hotel 13", searchResultRecord?.HotelName);
        Assert.Equal(13, searchResultRecord?.HotelCode);
        Assert.Equal(false, searchResultRecord?.ParkingIncluded);
        Assert.Equal(new string[] { "t13.1", "t13.2" }, searchResultRecord?.Tags.ToArray());
        Assert.Equal("This is a great hotel.", searchResultRecord?.Description);
    }

    [Fact]
    public async Task ItCanUpsertAndRetrieveUsingTheDynamicMapperAsync()
    {
        // Arrange
        var options = new QdrantCollectionOptions
        {
            Definition = fixture.HotelVectorStoreRecordDefinition
        };
        using var sut = new QdrantDynamicCollection(fixture.QdrantClient, "singleVectorHotels", ownsClient: false, options);

        // Act
        var baseSetGetResult = await sut.GetAsync(11ul, new RecordRetrievalOptions { IncludeVectors = true });
        await sut.UpsertAsync(new Dictionary<string, object?>
        {
            ["HotelId"] = 40ul,

            ["HotelName"] = "Dynamic Mapper Hotel",
            ["HotelCode"] = 40,
            ["ParkingIncluded"] = false,
            ["HotelRating"] = 3.6f,
            ["Tags"] = new List<string> { "dynamic" },
            ["Description"] = "This is a dynamic mapper hotel",

            ["DescriptionEmbedding"] = (await fixture.EmbeddingGenerator.GenerateAsync("This is a dynamic mapper hotel")).Vector
        });
        var localGetResult = await sut.GetAsync(40ul, new RecordRetrievalOptions { IncludeVectors = true });

        // Assert
        Assert.NotNull(baseSetGetResult);
        Assert.Equal(11ul, baseSetGetResult["HotelId"]);
        Assert.Equal("My Hotel 11", baseSetGetResult["HotelName"]);
        Assert.Equal(11, baseSetGetResult["HotelCode"]);
        Assert.True((bool)baseSetGetResult["ParkingIncluded"]!);
        Assert.Equal(4.5f, baseSetGetResult["HotelRating"]);
        Assert.Equal(new[] { "t11.1", "t11.2" }, ((List<string>)baseSetGetResult["Tags"]!).ToArray());
        Assert.Equal("This is a great hotel.", baseSetGetResult["Description"]);
        Assert.NotNull(baseSetGetResult["DescriptionEmbedding"]);
        Assert.IsType<ReadOnlyMemory<float>>(baseSetGetResult["DescriptionEmbedding"]);

        Assert.NotNull(localGetResult);
        Assert.Equal(40ul, localGetResult["HotelId"]);
        Assert.Equal("Dynamic Mapper Hotel", localGetResult["HotelName"]);
        Assert.Equal(40, localGetResult["HotelCode"]);
        Assert.False((bool)localGetResult["ParkingIncluded"]!);
        Assert.Equal(3.6f, localGetResult["HotelRating"]);
        Assert.Equal(new[] { "dynamic" }, ((List<string>)localGetResult["Tags"]!).ToArray());
        Assert.Equal("This is a dynamic mapper hotel", localGetResult["Description"]);
        Assert.NotNull(localGetResult["DescriptionEmbedding"]);
        Assert.IsType<ReadOnlyMemory<float>>(localGetResult["DescriptionEmbedding"]);
    }

    private async Task<HotelInfo> CreateTestHotelAsync(uint hotelId, IEmbeddingGenerator<string, Embedding<float>> embeddingGenerator)
    {
        return new HotelInfo
        {
            HotelId = hotelId,
            HotelName = $"My Hotel {hotelId}",
            HotelCode = (int)hotelId,
            HotelRating = 4.5f,
            ParkingIncluded = true,
            LastRenovationDate = new DateTimeOffset(2025, 2, 10, 5, 10, 15, TimeSpan.Zero),
            Tags = { "t1", "t2" },
            Description = "This is a great hotel.",
            DescriptionEmbedding = (await embeddingGenerator.GenerateAsync("This is a great hotel.")).Vector,
        };
    }
}
