// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Connectors.Memory.Pinecone;
using Microsoft.SemanticKernel.Connectors.Memory.Qdrant;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Memory;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.Memory.Qdrant;

/// <summary>
/// Tests for <see cref="QdrantMemoryStore"/> collection and upsert operations.
/// </summary>
public class QdrantMemoryStoreTests
{
    private readonly string _id = "Id";
    private readonly string _id2 = "Id2";
    private readonly string _id3 = "Id3";
    private readonly string _text = "text";
    private readonly string _text2 = "text2";
    private readonly string _text3 = "text3";
    private readonly string _description = "description";
    private readonly string _description2 = "description2";
    private readonly string _description3 = "description3";
    private readonly Embedding<float> _embedding = new(new float[] { 1, 1, 1 });
    private readonly Embedding<float> _embedding2 = new(new float[] { 2, 2, 2 });
    private readonly Embedding<float> _embedding3 = new(new float[] { 3, 3, 3 });
    private readonly Mock<ILogger<PineconeMemoryStore>> _mockLogger = new();

    [Fact]
    public async Task ItCreatesNewCollectionAsync()
    {
        // Arrange
        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        mockQdrantClient
            .Setup<Task<bool>>(x => x.DoesCollectionExistAsync(It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(false);
        mockQdrantClient
            .Setup<Task>(x => x.CreateCollectionAsync(It.IsAny<string>(), It.IsAny<CancellationToken>()));

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object, this._mockLogger.Object);

        // Act
        await vectorStore.CreateCollectionAsync("test");

        // Assert
        mockQdrantClient
            .Verify<Task<bool>>(x => x.DoesCollectionExistAsync("test", It.IsAny<CancellationToken>()), Times.Once());
        mockQdrantClient
            .Verify<Task>(x => x.CreateCollectionAsync("test", It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task ItWillNotOverwriteExistingCollectionAsync()
    {
        // Arrange
        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        mockQdrantClient
            .Setup<Task<bool>>(x => x.DoesCollectionExistAsync(It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);
        mockQdrantClient
            .Setup<Task>(x => x.CreateCollectionAsync(It.IsAny<string>(), It.IsAny<CancellationToken>()));

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object, this._mockLogger.Object);

        // Act
        await vectorStore.CreateCollectionAsync("test");

        // Assert
        mockQdrantClient
            .Verify<Task<bool>>(x => x.DoesCollectionExistAsync("test", It.IsAny<CancellationToken>()), Times.Once());
        mockQdrantClient
            .Verify<Task>(x => x.CreateCollectionAsync("test", It.IsAny<CancellationToken>()), Times.Never());
    }

    [Fact]
    public async Task ItListsCollectionsAsync()
    {
        // Arrange
        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        mockQdrantClient
            .Setup<IAsyncEnumerable<string>>(x => x.ListCollectionsAsync(It.IsAny<CancellationToken>()))
            .Returns((new string[] { "test1", "test2" }).ToAsyncEnumerable());

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object, this._mockLogger.Object);

        // Act
        var collections = await vectorStore.GetCollectionsAsync().ToListAsync();

        // Assert
        mockQdrantClient.Verify<IAsyncEnumerable<string>>(x => x.ListCollectionsAsync(It.IsAny<CancellationToken>()), Times.Once());
        Assert.Equal(2, collections.Count);
        Assert.Equal("test1", collections[0]);
        Assert.Equal("test2", collections[1]);
    }

    [Fact]
    public async Task ItDeletesCollectionAsync()
    {
        // Arrange
        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        mockQdrantClient
            .Setup<Task>(x => x.DeleteCollectionAsync(It.IsAny<string>(), It.IsAny<CancellationToken>()));
        mockQdrantClient
            .Setup<Task>(x => x.DoesCollectionExistAsync(It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .Returns(Task.FromResult(true));

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object, this._mockLogger.Object);

        // Act
        await vectorStore.DeleteCollectionAsync("test");

        // Assert
        mockQdrantClient.Verify<Task>(x => x.DeleteCollectionAsync("test", It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task ItThrowsIfUpsertRequestFailsAsync()
    {
        // Arrange
        var memoryRecord = MemoryRecord.LocalRecord(
            id: this._id,
            text: this._text,
            description: this._description,
            embedding: this._embedding);

        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        mockQdrantClient
            .Setup<Task<bool>>(x => x.DoesCollectionExistAsync(It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(false);
        mockQdrantClient
            .Setup<Task<QdrantVectorRecord?>>(x => x.GetVectorByPayloadIdAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync((QdrantVectorRecord?)null);
        mockQdrantClient
            .Setup<IAsyncEnumerable<QdrantVectorRecord>>(x =>
                x.GetVectorsByIdAsync(It.IsAny<string>(), It.IsAny<IEnumerable<string>>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .Returns(AsyncEnumerable.Empty<QdrantVectorRecord>());
        mockQdrantClient
            .Setup<Task>(x => x.UpsertVectorsAsync(It.IsAny<string>(), It.IsAny<IEnumerable<QdrantVectorRecord>>(), It.IsAny<CancellationToken>()))
            .Throws<HttpRequestException>();

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object, this._mockLogger.Object);

        // Assert
        await Assert.ThrowsAsync<SKException>(() => vectorStore.UpsertAsync("test_collection", memoryRecord));
    }

    [Fact]
    public async Task InsertIntoNonExistentCollectionDoesNotCallCreateCollectionAsync()
    {
        // Arrange
        var memoryRecord = MemoryRecord.LocalRecord(
            id: this._id,
            text: this._text,
            description: this._description,
            embedding: this._embedding);

        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        mockQdrantClient
            .Setup<Task<bool>>(x => x.DoesCollectionExistAsync(It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(false);
        mockQdrantClient
            .Setup<Task<QdrantVectorRecord?>>(x => x.GetVectorByPayloadIdAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync((QdrantVectorRecord?)null);
        mockQdrantClient
            .Setup<IAsyncEnumerable<QdrantVectorRecord>>(x =>
                x.GetVectorsByIdAsync(It.IsAny<string>(), It.IsAny<IEnumerable<string>>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .Returns(AsyncEnumerable.Empty<QdrantVectorRecord>());
        mockQdrantClient
            .Setup<Task>(x => x.UpsertVectorsAsync(It.IsAny<string>(), It.IsAny<IEnumerable<QdrantVectorRecord>>(), It.IsAny<CancellationToken>()));

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object, this._mockLogger.Object);

        // Act
        string guidString = await vectorStore.UpsertAsync("test_collection", memoryRecord);

        // Assert
        mockQdrantClient
            .Verify<Task<bool>>(x => x.DoesCollectionExistAsync("test_collection", It.IsAny<CancellationToken>()), Times.Never());
        mockQdrantClient.Verify<Task>(x => x.CreateCollectionAsync("test_collection", It.IsAny<CancellationToken>()), Times.Never());
    }

    [Fact]
    public async Task ItUpdatesExistingDataEntryBasedOnMetadataIdAsync()
    {
        // Arrange
        var memoryRecord = MemoryRecord.LocalRecord(
            id: this._id,
            text: this._text,
            description: this._description,
            embedding: this._embedding);

        var key = Guid.NewGuid().ToString();

        var qdrantVectorRecord = QdrantVectorRecord.FromJsonMetadata(
            key,
            memoryRecord.Embedding.Vector,
            memoryRecord.GetSerializedMetadata());

        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        mockQdrantClient
            .Setup<Task<bool>>(x => x.DoesCollectionExistAsync(It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);
        mockQdrantClient
            .Setup<Task<QdrantVectorRecord?>>(x => x.GetVectorByPayloadIdAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(qdrantVectorRecord);
        mockQdrantClient
            .Setup<IAsyncEnumerable<QdrantVectorRecord>>(x =>
                x.GetVectorsByIdAsync(It.IsAny<string>(), It.IsAny<IEnumerable<string>>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .Returns(AsyncEnumerable.Empty<QdrantVectorRecord>());
        mockQdrantClient
            .Setup<Task>(x => x.UpsertVectorsAsync(It.IsAny<string>(), It.IsAny<IEnumerable<QdrantVectorRecord>>(), It.IsAny<CancellationToken>()));

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object, this._mockLogger.Object);

        // Act
        string guidString = await vectorStore.UpsertAsync("test_collection", memoryRecord);

        // Assert
        mockQdrantClient
            .Verify<Task<bool>>(x => x.DoesCollectionExistAsync("test_collection", It.IsAny<CancellationToken>()), Times.Never());
        mockQdrantClient.Verify<Task>(x => x.CreateCollectionAsync("test_collection", It.IsAny<CancellationToken>()), Times.Never());
        mockQdrantClient.Verify<Task<QdrantVectorRecord?>>(
            x => x.GetVectorByPayloadIdAsync("test_collection", memoryRecord.Metadata.Id, false, It.IsAny<CancellationToken>()), Times.Once());
        mockQdrantClient.Verify<IAsyncEnumerable<QdrantVectorRecord>>(
            x => x.GetVectorsByIdAsync("test_collection", new[] { guidString }, false, It.IsAny<CancellationToken>()), Times.Never());
        mockQdrantClient.Verify<Task>(x => x.UpsertVectorsAsync("test_collection", It.IsAny<IEnumerable<QdrantVectorRecord>>(), It.IsAny<CancellationToken>()),
            Times.Once());
        Assert.True(Guid.TryParse(guidString, out _));
        Assert.Equal(key, guidString);
    }

    [Fact]
    public async Task ItGeneratesIdsForQdrantUntilUniqueIdIsFoundAsync()
    {
        // Arrange
        var memoryRecord = MemoryRecord.LocalRecord(
            id: this._id,
            text: this._text,
            description: this._description,
            embedding: this._embedding);

        var qdrantVectorRecord = QdrantVectorRecord.FromJsonMetadata(
            Guid.NewGuid().ToString(),
            Array.Empty<float>(),
            memoryRecord.GetSerializedMetadata());

        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        mockQdrantClient
            .Setup<Task<bool>>(x => x.DoesCollectionExistAsync(It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);
        mockQdrantClient
            .Setup<Task<QdrantVectorRecord?>>(x => x.GetVectorByPayloadIdAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync((QdrantVectorRecord?)null);
        mockQdrantClient
            .Setup<IAsyncEnumerable<QdrantVectorRecord>>(x =>
                x.GetVectorsByIdAsync(It.IsAny<string>(), It.IsAny<IEnumerable<string>>(), false, It.IsAny<CancellationToken>()))
            .Returns(new[] { qdrantVectorRecord }.ToAsyncEnumerable());
        mockQdrantClient
            .Setup<IAsyncEnumerable<QdrantVectorRecord>>(x =>
                x.GetVectorsByIdAsync(It.IsAny<string>(), It.IsAny<IEnumerable<string>>(), false, It.IsAny<CancellationToken>()))
            .Returns(AsyncEnumerable.Empty<QdrantVectorRecord>());
        mockQdrantClient
            .Setup<Task>(x => x.UpsertVectorsAsync(It.IsAny<string>(), It.IsAny<IEnumerable<QdrantVectorRecord>>(), It.IsAny<CancellationToken>()));

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object, this._mockLogger.Object);

        // Act
        string guidString = await vectorStore.UpsertAsync("test_collection", memoryRecord);

        // Assert
        mockQdrantClient
            .Verify<Task<bool>>(x => x.DoesCollectionExistAsync("test_collection", It.IsAny<CancellationToken>()), Times.Never());
        mockQdrantClient.Verify<Task>(x => x.CreateCollectionAsync("test_collection", It.IsAny<CancellationToken>()), Times.Never());
        mockQdrantClient.Verify<Task<QdrantVectorRecord?>>(
            x => x.GetVectorByPayloadIdAsync("test_collection", memoryRecord.Metadata.Id, false, It.IsAny<CancellationToken>()), Times.Once());
        mockQdrantClient.Verify<IAsyncEnumerable<QdrantVectorRecord>>(
            x => x.GetVectorsByIdAsync("test_collection", It.IsAny<IEnumerable<string>>(), false, It.IsAny<CancellationToken>()), Times.Once());
        mockQdrantClient.Verify<IAsyncEnumerable<QdrantVectorRecord>>(
            x => x.GetVectorsByIdAsync("test_collection", new[] { guidString }, It.IsAny<bool>(), It.IsAny<CancellationToken>()), Times.Once());
        mockQdrantClient.Verify<Task>(x => x.UpsertVectorsAsync("test_collection", It.IsAny<IEnumerable<QdrantVectorRecord>>(), It.IsAny<CancellationToken>()),
            Times.Once());
        Assert.True(Guid.TryParse(guidString, out _));
    }

    [Fact]
    public async Task ItUpdatesExistingDataEntryBasedOnKnownDatabaseKeyAsync()
    {
        // Arrange
        var memoryRecord = MemoryRecord.LocalRecord(
            id: this._id,
            text: this._text,
            description: this._description,
            embedding: this._embedding);

        memoryRecord.Key = Guid.NewGuid().ToString();

        var qdrantVectorRecord = QdrantVectorRecord.FromJsonMetadata(
            memoryRecord.Key,
            Array.Empty<float>(),
            memoryRecord.GetSerializedMetadata());

        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        mockQdrantClient
            .Setup<Task<bool>>(x => x.DoesCollectionExistAsync(It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);
        mockQdrantClient
            .Setup<Task<QdrantVectorRecord?>>(x => x.GetVectorByPayloadIdAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(qdrantVectorRecord);
        mockQdrantClient
            .Setup<IAsyncEnumerable<QdrantVectorRecord>>(x =>
                x.GetVectorsByIdAsync(It.IsAny<string>(), It.IsAny<IEnumerable<string>>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .Returns(AsyncEnumerable.Empty<QdrantVectorRecord>());
        mockQdrantClient
            .Setup<Task>(x => x.UpsertVectorsAsync(It.IsAny<string>(), It.IsAny<IEnumerable<QdrantVectorRecord>>(), It.IsAny<CancellationToken>()));

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object, this._mockLogger.Object);

        // Act
        string guidString = await vectorStore.UpsertAsync("test_collection", memoryRecord);

        // Assert
        mockQdrantClient
            .Verify<Task<bool>>(x => x.DoesCollectionExistAsync("test_collection", It.IsAny<CancellationToken>()), Times.Never());
        mockQdrantClient.Verify<Task>(x => x.CreateCollectionAsync("test_collection", It.IsAny<CancellationToken>()), Times.Never());
        mockQdrantClient.Verify<Task<QdrantVectorRecord?>>(
            x => x.GetVectorByPayloadIdAsync("test_collection", memoryRecord.Metadata.Id, false, It.IsAny<CancellationToken>()), Times.Never());
        mockQdrantClient.Verify<IAsyncEnumerable<QdrantVectorRecord>>(
            x => x.GetVectorsByIdAsync("test_collection", new[] { guidString }, false, It.IsAny<CancellationToken>()), Times.Never());
        mockQdrantClient.Verify<Task>(x => x.UpsertVectorsAsync("test_collection", It.IsAny<IEnumerable<QdrantVectorRecord>>(), It.IsAny<CancellationToken>()),
            Times.Once());
        Assert.True(Guid.TryParse(guidString, out _));
        Assert.Equal(memoryRecord.Key, guidString);
    }

    [Fact]
    public async Task ItCanBatchUpsertAsync()
    {
        // Arrange
        var memoryRecord = MemoryRecord.LocalRecord(
            id: this._id,
            text: this._text,
            description: this._description,
            embedding: this._embedding);
        var memoryRecord2 = MemoryRecord.LocalRecord(
            id: this._id2,
            text: this._text2,
            description: this._description2,
            embedding: this._embedding2);
        var memoryRecord3 = MemoryRecord.LocalRecord(
            id: this._id3,
            text: this._text3,
            description: this._description3,
            embedding: this._embedding3);

        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        mockQdrantClient
            .Setup<Task>(x => x.CreateCollectionAsync(It.IsAny<string>(), It.IsAny<CancellationToken>()));
        mockQdrantClient
            .Setup<Task<QdrantVectorRecord?>>(x => x.GetVectorByPayloadIdAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync((QdrantVectorRecord?)null);
        mockQdrantClient
            .Setup<IAsyncEnumerable<QdrantVectorRecord>>(x =>
                x.GetVectorsByIdAsync(It.IsAny<string>(), It.IsAny<IEnumerable<string>>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .Returns(AsyncEnumerable.Empty<QdrantVectorRecord>());
        mockQdrantClient
            .Setup<Task>(x => x.UpsertVectorsAsync(It.IsAny<string>(), It.IsAny<IEnumerable<QdrantVectorRecord>>(), It.IsAny<CancellationToken>()));

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object, this._mockLogger.Object);

        // Act
        var keys = await vectorStore.UpsertBatchAsync("test_collection", new[] { memoryRecord, memoryRecord2, memoryRecord3 }).ToListAsync();

        // Assert
        mockQdrantClient
            .Verify<Task<bool>>(x => x.DoesCollectionExistAsync("test_collection", It.IsAny<CancellationToken>()), Times.Never());
        mockQdrantClient.Verify<Task>(x => x.CreateCollectionAsync("test_collection", It.IsAny<CancellationToken>()), Times.Never());
        mockQdrantClient.Verify<Task<QdrantVectorRecord?>>(
            x => x.GetVectorByPayloadIdAsync("test_collection", memoryRecord.Metadata.Id, false, It.IsAny<CancellationToken>()), Times.Once());
        mockQdrantClient.Verify<Task<QdrantVectorRecord?>>(
            x => x.GetVectorByPayloadIdAsync("test_collection", memoryRecord2.Metadata.Id, false, It.IsAny<CancellationToken>()), Times.Once());
        mockQdrantClient.Verify<Task<QdrantVectorRecord?>>(
            x => x.GetVectorByPayloadIdAsync("test_collection", memoryRecord3.Metadata.Id, false, It.IsAny<CancellationToken>()), Times.Once());
        mockQdrantClient.Verify<Task>(x => x.UpsertVectorsAsync("test_collection", It.IsAny<IEnumerable<QdrantVectorRecord>>(), It.IsAny<CancellationToken>()),
            Times.Once());

        foreach (var guidString in keys)
        {
            mockQdrantClient.Verify<IAsyncEnumerable<QdrantVectorRecord>>(
                x => x.GetVectorsByIdAsync("test_collection", new[] { guidString }, It.IsAny<bool>(), It.IsAny<CancellationToken>()), Times.Once());
            Assert.True(Guid.TryParse(guidString, out _));
        }
    }
}
