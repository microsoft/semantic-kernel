// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.MongoDB;
using MongoDB.Driver;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.MongoDB.UnitTests;

/// <summary>
/// Unit tests for <see cref="MongoDBVectorStore"/> class.
/// </summary>
public sealed class MongoDBVectorStoreTests
{
    private readonly Mock<IMongoDatabase> _mockMongoDatabase = new();

    [Fact]
    public void GetCollectionWithNotSupportedKeyThrowsException()
    {
        // Arrange
        var sut = new MongoDBVectorStore(this._mockMongoDatabase.Object);

        // Act & Assert
        Assert.Throws<NotSupportedException>(() => sut.GetCollection<Guid, MongoDBHotelModel>("collection"));
    }

#pragma warning disable CS0618 // IMongoDBVectorStoreRecordCollectionFactoryß is obsolete
    [Fact]
    public void GetCollectionWithFactoryReturnsCustomCollection()
    {
        // Arrange
        var mockFactory = new Mock<IMongoDBVectorStoreRecordCollectionFactory>();
        var mockRecordCollection = new Mock<IVectorStoreRecordCollection<string, MongoDBHotelModel>>();

        mockFactory
            .Setup(l => l.CreateVectorStoreRecordCollection<string, MongoDBHotelModel>(
                this._mockMongoDatabase.Object,
                "collection",
                It.IsAny<VectorStoreRecordDefinition>()))
            .Returns(mockRecordCollection.Object);

        var sut = new MongoDBVectorStore(
            this._mockMongoDatabase.Object,
            new MongoDBVectorStoreOptions { VectorStoreCollectionFactory = mockFactory.Object });

        // Act
        var collection = sut.GetCollection<string, MongoDBHotelModel>("collection");

        // Assert
        Assert.Same(mockRecordCollection.Object, collection);
        mockFactory.Verify(l => l.CreateVectorStoreRecordCollection<string, MongoDBHotelModel>(
            this._mockMongoDatabase.Object,
            "collection",
            It.IsAny<VectorStoreRecordDefinition>()), Times.Once());
    }
#pragma warning restore CS0618

    [Fact]
    public void GetCollectionWithoutFactoryReturnsDefaultCollection()
    {
        // Arrange
        var sut = new MongoDBVectorStore(this._mockMongoDatabase.Object);

        // Act
        var collection = sut.GetCollection<string, MongoDBHotelModel>("collection");

        // Assert
        Assert.NotNull(collection);
    }

    [Fact]
    public async Task ListCollectionNamesReturnsCollectionNamesAsync()
    {
        // Arrange
        var expectedCollectionNames = new List<string> { "collection-1", "collection-2", "collection-3" };

        var mockCursor = new Mock<IAsyncCursor<string>>();
        mockCursor
            .SetupSequence(l => l.MoveNextAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(true)
            .ReturnsAsync(false);

        mockCursor
            .Setup(l => l.Current)
            .Returns(expectedCollectionNames);

        this._mockMongoDatabase
            .Setup(l => l.ListCollectionNamesAsync(It.IsAny<ListCollectionNamesOptions>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(mockCursor.Object);

        var sut = new MongoDBVectorStore(this._mockMongoDatabase.Object);

        // Act
        var actualCollectionNames = await sut.ListCollectionNamesAsync().ToListAsync();

        // Assert
        Assert.Equal(expectedCollectionNames, actualCollectionNames);
    }
}
