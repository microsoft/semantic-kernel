// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.CosmosMongoDB;
using MongoDB.Driver;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.CosmosMongoDB.UnitTests;

/// <summary>
/// Unit tests for <see cref="CosmosMongoVectorStore"/> class.
/// </summary>
public sealed class CosmosMongoVectorStoreTests
{
    private readonly Mock<IMongoDatabase> _mockMongoDatabase = new();

    [Fact]
    public void GetCollectionWithNotSupportedKeyThrowsException()
    {
        // Arrange
        using var sut = new CosmosMongoVectorStore(this._mockMongoDatabase.Object);

        // Act & Assert
        Assert.Throws<NotSupportedException>(() => sut.GetCollection<Guid, CosmosMongoHotelModel>("collection"));
    }

    [Fact]
    public void GetCollectionWithoutFactoryReturnsDefaultCollection()
    {
        // Arrange
        using var sut = new CosmosMongoVectorStore(this._mockMongoDatabase.Object);

        // Act
        var collection = sut.GetCollection<string, CosmosMongoHotelModel>("collection");

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

        using var sut = new CosmosMongoVectorStore(this._mockMongoDatabase.Object);

        // Act
        var actualCollectionNames = await sut.ListCollectionNamesAsync().ToListAsync();

        // Assert
        Assert.Equal(expectedCollectionNames, actualCollectionNames);
    }
}
