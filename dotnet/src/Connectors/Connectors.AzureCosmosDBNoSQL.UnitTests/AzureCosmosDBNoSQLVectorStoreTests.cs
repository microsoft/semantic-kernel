// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.AzureCosmosDBNoSQL.UnitTests;

/// <summary>
/// Unit tests for <see cref="AzureCosmosDBNoSQLVectorStore"/> class.
/// </summary>
public sealed class AzureCosmosDBNoSQLVectorStoreTests
{
    private readonly Mock<Database> _mockDatabase = new();

    public AzureCosmosDBNoSQLVectorStoreTests()
    {
        var mockClient = new Mock<CosmosClient>();

        mockClient.Setup(l => l.ClientOptions).Returns(new CosmosClientOptions() { UseSystemTextJsonSerializerWithOptions = JsonSerializerOptions.Default });

        this._mockDatabase
            .Setup(l => l.Client)
            .Returns(mockClient.Object);
    }

    [Fact]
    public void GetCollectionWithNotSupportedKeyThrowsException()
    {
        // Arrange
        var sut = new AzureCosmosDBNoSQLVectorStore(this._mockDatabase.Object);

        // Act & Assert
        Assert.Throws<NotSupportedException>(() => sut.GetCollection<Guid, AzureCosmosDBNoSQLHotel>("collection"));
    }

    [Fact]
    public void GetCollectionWithSupportedKeyReturnsCollection()
    {
        // Arrange
        var sut = new AzureCosmosDBNoSQLVectorStore(this._mockDatabase.Object);

        // Act
        var collectionWithStringKey = sut.GetCollection<string, AzureCosmosDBNoSQLHotel>("collection1");
        var collectionWithCompositeKey = sut.GetCollection<AzureCosmosDBNoSQLCompositeKey, AzureCosmosDBNoSQLHotel>("collection1");

        // Assert
        Assert.NotNull(collectionWithStringKey);
        Assert.NotNull(collectionWithCompositeKey);
    }

#pragma warning disable CS0618 // IAzureCosmosDBNoSQLVectorStoreRecordCollectionFactory is obsolete
    [Fact]
    public void GetCollectionWithFactoryReturnsCustomCollection()
    {
        // Arrange
        var mockFactory = new Mock<IAzureCosmosDBNoSQLVectorStoreRecordCollectionFactory>();
        var mockRecordCollection = new Mock<IVectorStoreRecordCollection<string, AzureCosmosDBNoSQLHotel>>();

        mockFactory
            .Setup(l => l.CreateVectorStoreRecordCollection<string, AzureCosmosDBNoSQLHotel>(
                this._mockDatabase.Object,
                "collection",
                It.IsAny<VectorStoreRecordDefinition>()))
            .Returns(mockRecordCollection.Object);

        var sut = new AzureCosmosDBNoSQLVectorStore(
            this._mockDatabase.Object,
            new AzureCosmosDBNoSQLVectorStoreOptions { VectorStoreCollectionFactory = mockFactory.Object });

        // Act
        var collection = sut.GetCollection<string, AzureCosmosDBNoSQLHotel>("collection");

        // Assert
        Assert.Same(mockRecordCollection.Object, collection);
        mockFactory.Verify(l => l.CreateVectorStoreRecordCollection<string, AzureCosmosDBNoSQLHotel>(
            this._mockDatabase.Object,
            "collection",
            It.IsAny<VectorStoreRecordDefinition>()), Times.Once());
    }
#pragma warning restore CS0618

    [Fact]
    public void GetCollectionWithoutFactoryReturnsDefaultCollection()
    {
        // Arrange
        var sut = new AzureCosmosDBNoSQLVectorStore(this._mockDatabase.Object);

        // Act
        var collection = sut.GetCollection<string, AzureCosmosDBNoSQLHotel>("collection");

        // Assert
        Assert.NotNull(collection);
    }

    [Fact]
    public async Task ListCollectionNamesReturnsCollectionNamesAsync()
    {
        // Arrange
        var expectedCollectionNames = new List<string> { "collection-1", "collection-2", "collection-3" };

        var mockFeedResponse = new Mock<FeedResponse<string>>();
        mockFeedResponse
            .Setup(l => l.Resource)
            .Returns(expectedCollectionNames);

        var mockFeedIterator = new Mock<FeedIterator<string>>();
        mockFeedIterator
            .SetupSequence(l => l.HasMoreResults)
            .Returns(true)
            .Returns(false);

        mockFeedIterator
            .Setup(l => l.ReadNextAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(mockFeedResponse.Object);

        this._mockDatabase
            .Setup(l => l.GetContainerQueryIterator<string>(
                It.IsAny<string>(),
                It.IsAny<string>(),
                It.IsAny<QueryRequestOptions>()))
            .Returns(mockFeedIterator.Object);

        var sut = new AzureCosmosDBNoSQLVectorStore(this._mockDatabase.Object);

        // Act
        var actualCollectionNames = await sut.ListCollectionNamesAsync().ToListAsync();

        // Assert
        Assert.Equal(expectedCollectionNames, actualCollectionNames);
    }
}
