// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Microsoft.SemanticKernel.Data;
using Qdrant.Client.Grpc;
using Xunit;
using Xunit.Abstractions;
using static SemanticKernel.IntegrationTests.Connectors.Memory.Qdrant.QdrantVectorStoreFixture;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Qdrant;

/// <summary>
/// Contains tests for the <see cref="QdrantVectorStoreRecordCollection{TRecord}"/> class.
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
        var sut = new QdrantVectorStoreRecordCollection<HotelInfo>(fixture.QdrantClient, collectionName);

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
    public async Task ItCanCreateACollectionUpsertAndGetAsync(bool hasNamedVectors, bool useRecordDefinition)
    {
        // Arrange
        var collectionNamePostfix1 = useRecordDefinition ? "WithDefinition" : "WithType";
        var collectionNamePostfix2 = hasNamedVectors ? "HasNamedVectors" : "SingleUnnamedVector";
        var testCollectionName = $"createtest{collectionNamePostfix1}{collectionNamePostfix2}";

        var options = new QdrantVectorStoreRecordCollectionOptions<HotelInfo>
        {
            HasNamedVectors = hasNamedVectors,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.HotelVectorStoreRecordDefinition : null
        };
        var sut = new QdrantVectorStoreRecordCollection<HotelInfo>(fixture.QdrantClient, testCollectionName, options);

        var record = this.CreateTestHotel(30);

        // Act
        await sut.CreateCollectionAsync();
        var upsertResult = await sut.UpsertAsync(record);
        var getResult = await sut.GetAsync(30, new GetRecordOptions { IncludeVectors = true });

        // Assert
        var collectionExistResult = await sut.CollectionExistsAsync();
        Assert.True(collectionExistResult);
        await sut.DeleteCollectionAsync();

        Assert.Equal(30ul, upsertResult);
        Assert.Equal(record.HotelId, getResult?.HotelId);
        Assert.Equal(record.HotelName, getResult?.HotelName);
        Assert.Equal(record.HotelCode, getResult?.HotelCode);
        Assert.Equal(record.HotelRating, getResult?.HotelRating);
        Assert.Equal(record.ParkingIncluded, getResult?.ParkingIncluded);
        Assert.Equal(record.Tags.ToArray(), getResult?.Tags.ToArray());
        Assert.Equal(record.Description, getResult?.Description);

        // Output
        output.WriteLine(collectionExistResult.ToString());
        output.WriteLine(upsertResult.ToString(CultureInfo.InvariantCulture));
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

        var sut = new QdrantVectorStoreRecordCollection<HotelInfo>(fixture.QdrantClient, tempCollectionName);

        // Act
        await sut.DeleteCollectionAsync();

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
        var options = new QdrantVectorStoreRecordCollectionOptions<HotelInfo>
        {
            HasNamedVectors = hasNamedVectors,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.HotelVectorStoreRecordDefinition : null
        };
        var sut = new QdrantVectorStoreRecordCollection<HotelInfo>(fixture.QdrantClient, collectionName, options);

        var record = this.CreateTestHotel(20);

        // Act.
        var upsertResult = await sut.UpsertAsync(record);

        // Assert.
        var getResult = await sut.GetAsync(20, new GetRecordOptions { IncludeVectors = true });
        Assert.Equal(20ul, upsertResult);
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
        output.WriteLine(upsertResult.ToString(CultureInfo.InvariantCulture));
        output.WriteLine(getResult?.ToString());
    }

    [Fact]
    public async Task ItCanUpsertAndRemoveDocumentWithGuidIdToVectorStoreAsync()
    {
        // Arrange.
        var options = new QdrantVectorStoreRecordCollectionOptions<HotelInfoWithGuidId> { HasNamedVectors = false };
        IVectorStoreRecordCollection<Guid, HotelInfoWithGuidId> sut = new QdrantVectorStoreRecordCollection<HotelInfoWithGuidId>(fixture.QdrantClient, "singleVectorGuidIdHotels", options);

        var record = new HotelInfoWithGuidId
        {
            HotelId = Guid.Parse("55555555-5555-5555-5555-555555555555"),
            HotelName = "My Hotel 5",
            Description = "This is a great hotel.",
            DescriptionEmbedding = new[] { 30f, 31f, 32f, 33f },
        };

        // Act.
        var upsertResult = await sut.UpsertAsync(record);

        // Assert.
        var getResult = await sut.GetAsync(Guid.Parse("55555555-5555-5555-5555-555555555555"), new GetRecordOptions { IncludeVectors = true });
        Assert.Equal(Guid.Parse("55555555-5555-5555-5555-555555555555"), upsertResult);
        Assert.Equal(record.HotelId, getResult?.HotelId);
        Assert.Equal(record.HotelName, getResult?.HotelName);
        Assert.Equal(record.Description, getResult?.Description);

        // Act.
        await sut.DeleteAsync(Guid.Parse("55555555-5555-5555-5555-555555555555"));

        // Assert.
        Assert.Null(await sut.GetAsync(Guid.Parse("55555555-5555-5555-5555-555555555555")));

        // Output.
        output.WriteLine(upsertResult.ToString("D"));
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
        var options = new QdrantVectorStoreRecordCollectionOptions<HotelInfo>
        {
            HasNamedVectors = hasNamedVectors,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.HotelVectorStoreRecordDefinition : null
        };
        var sut = new QdrantVectorStoreRecordCollection<HotelInfo>(fixture.QdrantClient, collectionName, options);

        // Act.
        var getResult = await sut.GetAsync(11, new GetRecordOptions { IncludeVectors = withEmbeddings });

        // Assert.
        Assert.Equal(11ul, getResult?.HotelId);
        Assert.Equal("My Hotel 11", getResult?.HotelName);
        Assert.Equal(11, getResult?.HotelCode);
        Assert.True(getResult?.ParkingIncluded);
        Assert.Equal(4.5f, getResult?.HotelRating);
        Assert.Equal(2, getResult?.Tags.Count);
        Assert.Equal("t1", getResult?.Tags[0]);
        Assert.Equal("t2", getResult?.Tags[1]);
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
        var options = new QdrantVectorStoreRecordCollectionOptions<HotelInfoWithGuidId>
        {
            HasNamedVectors = false,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.HotelWithGuidIdVectorStoreRecordDefinition : null
        };
        var sut = new QdrantVectorStoreRecordCollection<HotelInfoWithGuidId>(fixture.QdrantClient, "singleVectorGuidIdHotels", options);

        // Act.
        var getResult = await sut.GetAsync(Guid.Parse("11111111-1111-1111-1111-111111111111"), new GetRecordOptions { IncludeVectors = withEmbeddings });

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
        var options = new QdrantVectorStoreRecordCollectionOptions<HotelInfo> { HasNamedVectors = true };
        var sut = new QdrantVectorStoreRecordCollection<HotelInfo>(fixture.QdrantClient, "namedVectorsHotels", options);

        // Act
        // Also include one non-existing key to test that the operation does not fail for these and returns only the found ones.
        var hotels = sut.GetBatchAsync([11, 15, 12], new GetRecordOptions { IncludeVectors = true });

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
        var options = new QdrantVectorStoreRecordCollectionOptions<HotelInfo>
        {
            HasNamedVectors = hasNamedVectors,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.HotelVectorStoreRecordDefinition : null
        };
        var sut = new QdrantVectorStoreRecordCollection<HotelInfo>(fixture.QdrantClient, collectionName, options);

        await sut.UpsertAsync(this.CreateTestHotel(20));

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
        var options = new QdrantVectorStoreRecordCollectionOptions<HotelInfo>
        {
            HasNamedVectors = hasNamedVectors,
            VectorStoreRecordDefinition = useRecordDefinition ? fixture.HotelVectorStoreRecordDefinition : null
        };
        var sut = new QdrantVectorStoreRecordCollection<HotelInfo>(fixture.QdrantClient, collectionName, options);

        await sut.UpsertAsync(this.CreateTestHotel(20));

        // Act.
        // Also delete a non-existing key to test that the operation does not fail for these.
        await sut.DeleteBatchAsync([20, 21]);

        // Assert.
        Assert.Null(await sut.GetAsync(20));
    }

    [Fact]
    public async Task ItReturnsNullWhenGettingNonExistentRecordAsync()
    {
        // Arrange
        var options = new QdrantVectorStoreRecordCollectionOptions<HotelInfo> { HasNamedVectors = false };
        var sut = new QdrantVectorStoreRecordCollection<HotelInfo>(fixture.QdrantClient, "singleVectorHotels", options);

        // Act & Assert
        Assert.Null(await sut.GetAsync(15, new GetRecordOptions { IncludeVectors = true }));
    }

    [Fact]
    public async Task ItThrowsMappingExceptionForFailedMapperAsync()
    {
        // Arrange
        var options = new QdrantVectorStoreRecordCollectionOptions<HotelInfo> { PointStructCustomMapper = new FailingMapper() };
        var sut = new QdrantVectorStoreRecordCollection<HotelInfo>(fixture.QdrantClient, "singleVectorHotels", options);

        // Act & Assert
        await Assert.ThrowsAsync<VectorStoreRecordMappingException>(async () => await sut.GetAsync(11, new GetRecordOptions { IncludeVectors = true }));
    }

    private HotelInfo CreateTestHotel(uint hotelId)
    {
        return new HotelInfo
        {
            HotelId = hotelId,
            HotelName = $"My Hotel {hotelId}",
            HotelCode = (int)hotelId,
            HotelRating = 4.5f,
            ParkingIncluded = true,
            Tags = { "t1", "t2" },
            Description = "This is a great hotel.",
            DescriptionEmbedding = new[] { 30f, 31f, 32f, 33f },
        };
    }

    private sealed class FailingMapper : IVectorStoreRecordMapper<HotelInfo, PointStruct>
    {
        public PointStruct MapFromDataToStorageModel(HotelInfo dataModel)
        {
            throw new NotImplementedException();
        }

        public HotelInfo MapFromStorageToDataModel(PointStruct storageModel, StorageToDataModelMapperOptions options)
        {
            throw new NotImplementedException();
        }
    }
}
