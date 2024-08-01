// Copyright (c) Microsoft. All rights reserved.

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

namespace SemanticKernel.Connectors.AzureAISearch.UnitTests;

public sealed class AzureCosmosDBMongoDBVectorStoreTests
{
    private readonly Mock<IMongoDatabase> _mockMongoDatabase = new();

    [Fact]
    public void GetCollectionWithNotSupportedKeyThrowsException()
    {
        // Arrange
        var sut = new AzureCosmosDBMongoDBVectorStore(this._mockMongoDatabase.Object);

        // Act & Assert
        Assert.Throws<NotSupportedException>(() => sut.GetCollection<Guid, Hotel>("collection"));
    }

    [Fact]
    public void GetCollectionWithFactoryReturnsCustomCollection()
    {
        // Arrange
        var mockFactory = new Mock<IAzureCosmosDBMongoDBVectorStoreRecordCollectionFactory>();
        var mockRecordCollection = new Mock<IVectorStoreRecordCollection<string, Hotel>>();

        mockFactory
            .Setup(l => l.CreateVectorStoreRecordCollection<string, Hotel>(
                this._mockMongoDatabase.Object,
                "collection",
                It.IsAny<VectorStoreRecordDefinition>()))
            .Returns(mockRecordCollection.Object);

        var sut = new AzureCosmosDBMongoDBVectorStore(
            this._mockMongoDatabase.Object,
            new AzureCosmosDBMongoDBVectorStoreOptions { VectorStoreCollectionFactory = mockFactory.Object });

        // Act
        var collection = sut.GetCollection<string, Hotel>("collection");

        // Assert
        Assert.Same(mockRecordCollection.Object, collection);
        mockFactory.Verify(l => l.CreateVectorStoreRecordCollection<string, Hotel>(
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
        var collection = sut.GetCollection<string, Hotel>("collection");

        // Assert
        Assert.NotNull(collection);
    }

    [Fact]
    public async Task ListCollectionNamesReturnsCollectionNamesAsync()
    {
        // Arrange
        var cursorResponses = new Queue<bool>([true, false]);
        var expectedCollectionNames = new List<string> { "collection-1", "collection-2", "collection-3" };

        var mockCursor = new Mock<IAsyncCursor<string>>();
        mockCursor
            .Setup(l => l.MoveNextAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(() => cursorResponses.Dequeue());

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

    #region private

    public class Hotel(string hotelId)
    {
        /// <summary>The key of the record.</summary>
        [VectorStoreRecordKey]
        public string HotelId { get; init; } = hotelId;

        /// <summary>A string metadata field.</summary>
        [VectorStoreRecordData]
        public string? HotelName { get; set; }

        /// <summary>An int metadata field.</summary>
        [VectorStoreRecordData]
        public int HotelCode { get; set; }

        /// <summary>A float metadata field.</summary>
        [VectorStoreRecordData]
        public float? HotelRating { get; set; }

        /// <summary>A bool metadata field.</summary>
        [VectorStoreRecordData(StoragePropertyName = "parking_is_included")]
        public bool ParkingIncluded { get; set; }

        /// <summary>An array metadata field.</summary>
        [VectorStoreRecordData]
        public List<string> Tags { get; set; } = [];

        /// <summary>A data field.</summary>
        [VectorStoreRecordData]
        public string? Description { get; set; }

        /// <summary>A vector field.</summary>
        [VectorStoreRecordVector(Dimensions: 4, IndexKind: "vector-ivf", DistanceFunction: "COS")]
        public ReadOnlyMemory<float>? DescriptionEmbedding { get; set; }
    }

    #endregion
}
