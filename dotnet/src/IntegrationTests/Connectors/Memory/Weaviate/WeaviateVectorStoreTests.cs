// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Weaviate;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Weaviate;

[Collection("WeaviateVectorStoreCollection")]
public sealed class WeaviateVectorStoreTests(WeaviateVectorStoreFixture fixture)
{
    [Fact]
    public async Task ItCanGetAListOfExistingCollectionNamesAsync()
    {
        // Arrange
        var collection1 = new WeaviateVectorStoreRecordCollection<WeaviateHotel>(fixture.HttpClient!, "Collection1");
        var collection2 = new WeaviateVectorStoreRecordCollection<WeaviateHotel>(fixture.HttpClient!, "Collection2");
        var collection3 = new WeaviateVectorStoreRecordCollection<WeaviateHotel>(fixture.HttpClient!, "Collection3");

        await collection1.CreateCollectionAsync();
        await collection2.CreateCollectionAsync();
        await collection3.CreateCollectionAsync();

        var sut = new WeaviateVectorStore(fixture.HttpClient!);

        // Act
        var collectionNames = await sut.ListCollectionNamesAsync().ToListAsync();

        // Assert
        Assert.Contains("Collection1", collectionNames);
        Assert.Contains("Collection2", collectionNames);
        Assert.Contains("Collection3", collectionNames);
    }
}
