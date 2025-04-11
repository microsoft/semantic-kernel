// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Weaviate;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.Weaviate.UnitTests;

/// <summary>
/// Unit tests for <see cref="WeaviateVectorStore"/> class.
/// </summary>
public sealed class WeaviateVectorStoreTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub = new();
    private readonly HttpClient _mockHttpClient;

    public WeaviateVectorStoreTests()
    {
        this._mockHttpClient = new(this._messageHandlerStub, false) { BaseAddress = new Uri("http://test") };
    }

    [Fact]
    public void GetCollectionWithNotSupportedKeyThrowsException()
    {
        // Arrange
        var sut = new WeaviateVectorStore(this._mockHttpClient);

        // Act & Assert
        Assert.Throws<NotSupportedException>(() => sut.GetCollection<string, WeaviateHotel>("Collection"));
    }

    [Fact]
    public void GetCollectionWithSupportedKeyReturnsCollection()
    {
        // Arrange
        var sut = new WeaviateVectorStore(this._mockHttpClient);

        // Act
        var collection = sut.GetCollection<Guid, WeaviateHotel>("Collection1");

        // Assert
        Assert.NotNull(collection);
    }

#pragma warning disable CS0618 // IWeaviateVectorStoreRecordCollectionFactory is obsolete
    [Fact]
    public void GetCollectionWithFactoryReturnsCustomCollection()
    {
        // Arrange
        var mockFactory = new Mock<IWeaviateVectorStoreRecordCollectionFactory>();
        var mockRecordCollection = new Mock<IVectorStoreRecordCollection<Guid, WeaviateHotel>>();

        mockFactory
            .Setup(l => l.CreateVectorStoreRecordCollection<Guid, WeaviateHotel>(
                this._mockHttpClient,
                "collection",
                It.IsAny<VectorStoreRecordDefinition>()))
            .Returns(mockRecordCollection.Object);

        var sut = new WeaviateVectorStore(
            this._mockHttpClient,
            new WeaviateVectorStoreOptions { VectorStoreCollectionFactory = mockFactory.Object });

        // Act
        var collection = sut.GetCollection<Guid, WeaviateHotel>("collection");

        // Assert
        Assert.Same(mockRecordCollection.Object, collection);
        mockFactory.Verify(l => l.CreateVectorStoreRecordCollection<Guid, WeaviateHotel>(
            this._mockHttpClient,
            "collection",
            It.IsAny<VectorStoreRecordDefinition>()), Times.Once());
    }
#pragma warning restore CS0618

    [Fact]
    public async Task ListCollectionNamesReturnsCollectionNamesAsync()
    {
        // Arrange
        var expectedCollectionNames = new List<string> { "Collection1", "Collection2", "Collection3" };
        var response = new WeaviateGetCollectionsResponse
        {
            Collections = expectedCollectionNames.Select(name => new WeaviateCollectionSchema(name)).ToList()
        };

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(JsonSerializer.Serialize(response))
        };

        var sut = new WeaviateVectorStore(this._mockHttpClient);

        // Act
        var actualCollectionNames = await sut.ListCollectionNamesAsync().ToListAsync();

        // Assert
        Assert.Equal(expectedCollectionNames, actualCollectionNames);
    }

    public void Dispose()
    {
        this._mockHttpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
