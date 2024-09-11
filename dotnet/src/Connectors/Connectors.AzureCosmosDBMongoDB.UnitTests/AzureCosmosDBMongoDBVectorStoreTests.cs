﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;
using Microsoft.SemanticKernel.Data;
using MongoDB.Driver;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.AzureCosmosDBMongoDB.UnitTests;

/// <summary>
/// Unit tests for <see cref="AzureCosmosDBMongoDBVectorStore"/> class.
/// </summary>
public sealed class AzureCosmosDBMongoDBVectorStoreTests
{
    private readonly Mock<IMongoDatabase> _mockMongoDatabase = new();

    [Fact]
    public void GetCollectionWithNotSupportedKeyThrowsException()
    {
        // Arrange
        var sut = new AzureCosmosDBMongoDBVectorStore(this._mockMongoDatabase.Object);

        // Act & Assert
        Assert.Throws<NotSupportedException>(() => sut.GetCollection<Guid, AzureCosmosDBMongoDBHotelModel>("collection"));
    }

    [Fact]
    public void GetCollectionWithFactoryReturnsCustomCollection()
    {
        // Arrange
        var mockFactory = new Mock<IAzureCosmosDBMongoDBVectorStoreRecordCollectionFactory>();
        var mockRecordCollection = new Mock<IVectorStoreRecordCollection<string, AzureCosmosDBMongoDBHotelModel>>();

        mockFactory
            .Setup(l => l.CreateVectorStoreRecordCollection<string, AzureCosmosDBMongoDBHotelModel>(
                this._mockMongoDatabase.Object,
                "collection",
                It.IsAny<VectorStoreRecordDefinition>()))
            .Returns(mockRecordCollection.Object);

        var sut = new AzureCosmosDBMongoDBVectorStore(
            this._mockMongoDatabase.Object,
            new AzureCosmosDBMongoDBVectorStoreOptions { VectorStoreCollectionFactory = mockFactory.Object });

        // Act
        var collection = sut.GetCollection<string, AzureCosmosDBMongoDBHotelModel>("collection");

        // Assert
        Assert.Same(mockRecordCollection.Object, collection);
        mockFactory.Verify(l => l.CreateVectorStoreRecordCollection<string, AzureCosmosDBMongoDBHotelModel>(
            this._mockMongoDatabase.Object,
            "collection",
            It.IsAny<VectorStoreRecordDefinition>()), Times.Once());
    }

    [Fact]
    public void GetCollectionWithoutFactoryReturnsDefaultCollection()
    {
        // Arrange
        var sut = new AzureCosmosDBMongoDBVectorStore(this._mockMongoDatabase.Object);

        // Act
        var collection = sut.GetCollection<string, AzureCosmosDBMongoDBHotelModel>("collection");

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

        var sut = new AzureCosmosDBMongoDBVectorStore(this._mockMongoDatabase.Object);

        // Act
        var actualCollectionNames = await sut.ListCollectionNamesAsync().ToListAsync();

        // Assert
        Assert.Equal(expectedCollectionNames, actualCollectionNames);
    }
}
