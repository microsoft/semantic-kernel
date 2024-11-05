// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Qdrant;

[Collection("QdrantVectorStoreCollection")]
public class QdrantVectorStoreTests(ITestOutputHelper output, QdrantVectorStoreFixture fixture)
{
    [Fact]
    public async Task ItPassesSettingsFromVectorStoreToCollectionAsync()
    {
        // Arrange
        var sut = new QdrantVectorStore(fixture.QdrantClient, new() { HasNamedVectors = true });

        // Act
        var collectionFromVS = sut.GetCollection<ulong, QdrantVectorStoreFixture.HotelInfo>("SettingsPassedCollection");
        await collectionFromVS.CreateCollectionIfNotExistsAsync();

        var directCollection = new QdrantVectorStoreRecordCollection<QdrantVectorStoreFixture.HotelInfo>(fixture.QdrantClient, "SettingsPassedCollection", new() { HasNamedVectors = true });
        await directCollection.UpsertAsync(new QdrantVectorStoreFixture.HotelInfo
        {
            HotelId = 1ul,
            HotelName = "My Hotel 1",
            HotelCode = 1,
            HotelRating = 4.5f,
            ParkingIncluded = true,
            Tags = { "t1", "t2" },
            Description = "This is a great hotel.",
            DescriptionEmbedding = new float[1536],
        });
    }

    [Fact]
    public async Task ItCanGetAListOfExistingCollectionNamesAsync()
    {
        // Arrange
        var sut = new QdrantVectorStore(fixture.QdrantClient);

        // Act
        var collectionNames = await sut.ListCollectionNamesAsync().ToListAsync();

        // Assert
        Assert.Equal(3, collectionNames.Count);
        Assert.Contains("namedVectorsHotels", collectionNames);
        Assert.Contains("singleVectorHotels", collectionNames);
        Assert.Contains("singleVectorGuidIdHotels", collectionNames);

        // Output
        output.WriteLine(string.Join(",", collectionNames));
    }
}
