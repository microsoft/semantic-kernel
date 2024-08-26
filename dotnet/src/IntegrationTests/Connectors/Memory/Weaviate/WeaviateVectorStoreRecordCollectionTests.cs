// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Weaviate;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Weaviate;

[Collection("WeaviateVectorStoreCollection")]
public sealed class WeaviateVectorStoreRecordCollectionTests(WeaviateVectorStoreFixture fixture)
{
    [Fact]
    public async Task ItCanCreateCollectionAsync()
    {
        // Arrange
        var sut = new WeaviateVectorStoreRecordCollection<WeaviateHotel>(fixture.HttpClient!, "TestCreateCollection");

        // Act
        await sut.CreateCollectionAsync();

        // Assert
        Assert.True(await sut.CollectionExistsAsync());
    }
}
