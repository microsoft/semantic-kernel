// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Qdrant;

[Collection("QdrantVectorStoreCollection")]
public class QdrantVectorStoreTests(QdrantVectorStoreFixture fixture)
#pragma warning disable CA2000 // Dispose objects before losing scope
    : BaseVectorStoreTests<ulong, QdrantVectorStoreFixture.HotelInfo>(new QdrantVectorStore(fixture.QdrantClient, OwnsClient))
#pragma warning restore CA2000 // Dispose objects before losing scope
{
    // The client is shared with base class tests.
    private const bool OwnsClient = false;

    [Fact]
    public async Task ItPassesSettingsFromVectorStoreToCollectionAsync()
    {
        // Arrange
        using QdrantVectorStore sut = new(fixture.QdrantClient, OwnsClient, new() { HasNamedVectors = true });

        // Act
        var collectionFromVS = sut.GetCollection<ulong, QdrantVectorStoreFixture.HotelInfo>("SettingsPassedCollection");
        await collectionFromVS.EnsureCollectionExistsAsync();

        using QdrantCollection<ulong, QdrantVectorStoreFixture.HotelInfo> directCollection = new(
            fixture.QdrantClient, "SettingsPassedCollection", OwnsClient, new() { HasNamedVectors = true });
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
}
