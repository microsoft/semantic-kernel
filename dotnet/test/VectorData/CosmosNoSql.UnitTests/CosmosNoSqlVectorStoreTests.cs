// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Azure.Cosmos;
using Microsoft.SemanticKernel.Connectors.CosmosNoSql;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.CosmosNoSql.UnitTests;

/// <summary>
/// Unit tests for <see cref="Microsoft.SemanticKernel.Connectors.CosmosNoSql.CosmosNoSqlVectorStore"/> class.
/// </summary>
public sealed class CosmosNoSqlVectorStoreTests
{
    private readonly Mock<Database> _mockDatabase = new();

    public CosmosNoSqlVectorStoreTests()
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
        using var sut = new Microsoft.SemanticKernel.Connectors.CosmosNoSql.CosmosNoSqlVectorStore(this._mockDatabase.Object);

        // Act & Assert
        Assert.Throws<NotSupportedException>(() => sut.GetCollection<byte[], CosmosNoSqlHotel>("collection"));
    }

    [Fact]
    public void GetCollectionWithSupportedKeyReturnsCollection()
    {
        // Arrange
        using var sut = new Microsoft.SemanticKernel.Connectors.CosmosNoSql.CosmosNoSqlVectorStore(this._mockDatabase.Object);

        // Act
        var collection = sut.GetCollection<CosmosNoSqlKey, CosmosNoSqlHotel>("collection1");

        // Assert
        Assert.NotNull(collection);
    }

    [Fact]
    public void GetCollectionWithoutFactoryReturnsDefaultCollection()
    {
        // Arrange
        using var sut = new Microsoft.SemanticKernel.Connectors.CosmosNoSql.CosmosNoSqlVectorStore(this._mockDatabase.Object);

        // Act
        var collection = sut.GetCollection<CosmosNoSqlKey, CosmosNoSqlHotel>("collection");

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

        using var sut = new Microsoft.SemanticKernel.Connectors.CosmosNoSql.CosmosNoSqlVectorStore(this._mockDatabase.Object);

        // Act
        var actualCollectionNames = await sut.ListCollectionNamesAsync().ToListAsync();

        // Assert
        Assert.Equal(expectedCollectionNames, actualCollectionNames);
    }
}
