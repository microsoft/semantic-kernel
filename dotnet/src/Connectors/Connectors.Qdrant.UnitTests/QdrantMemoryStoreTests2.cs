// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Microsoft.SemanticKernel.Memory;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.Qdrant.UnitTests;

/// <summary>
/// Tests for <see cref="QdrantMemoryStore"/> Get and Remove operations.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted")]
public class QdrantMemoryStoreTests2
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
    private readonly ReadOnlyMemory<float> _embedding = new float[] { 1, 1, 1 };
    private readonly ReadOnlyMemory<float> _embedding2 = new float[] { 2, 2, 2 };
    private readonly ReadOnlyMemory<float> _embedding3 = new float[] { 3, 3, 3 };
    private readonly Mock<ILoggerFactory> _mockLogger = new();

    [Fact]
    public async Task GetAsyncCallsDoNotRequestVectorsUnlessSpecifiedAsync()
    {
        // Arrange
        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object, this._mockLogger.Object);

        var guidString = Guid.NewGuid().ToString();
        var guidString2 = Guid.NewGuid().ToString();

        var memoryRecord = MemoryRecord.LocalRecord(
            id: this._id,
            text: this._text,
            description: this._description,
            embedding: this._embedding);

        // this information will not be verified
        var qdrantVectorRecord = QdrantVectorRecord.FromJsonMetadata(
            guidString,
            memoryRecord.Embedding,
            memoryRecord.GetSerializedMetadata());

        mockQdrantClient
            .Setup<IAsyncEnumerable<QdrantVectorRecord>>(x =>
                x.GetVectorsByIdAsync(It.IsAny<string>(), It.IsAny<IEnumerable<string>>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .Returns(new[] { qdrantVectorRecord }.ToAsyncEnumerable());

        // Act
        _ = await vectorStore.GetAsync("test_collection", this._id);
        _ = await vectorStore.GetAsync("test_collection", this._id, true);
        _ = await vectorStore.GetBatchAsync("test_collection", [this._id2]).ToListAsync();
        _ = await vectorStore.GetBatchAsync("test_collection", [this._id2], true).ToListAsync();
        _ = await vectorStore.GetWithPointIdAsync("test_collection", guidString);
        _ = await vectorStore.GetWithPointIdAsync("test_collection", guidString, true);
        _ = await vectorStore.GetWithPointIdBatchAsync("test_collection", [guidString2]).ToListAsync();
        _ = await vectorStore.GetWithPointIdBatchAsync("test_collection", [guidString2], true).ToListAsync();

        // Assert
        mockQdrantClient.Verify<Task<QdrantVectorRecord?>>(
            x => x.GetVectorByPayloadIdAsync("test_collection", this._id, false, It.IsAny<CancellationToken>()),
            Times.Once());
        mockQdrantClient.Verify<Task<QdrantVectorRecord?>>(
            x => x.GetVectorByPayloadIdAsync("test_collection", this._id, true, It.IsAny<CancellationToken>()),
            Times.Once());
        mockQdrantClient.Verify<Task<QdrantVectorRecord?>>(
            x => x.GetVectorByPayloadIdAsync("test_collection", this._id2, false, It.IsAny<CancellationToken>()),
            Times.Once());
        mockQdrantClient.Verify<Task<QdrantVectorRecord?>>(
            x => x.GetVectorByPayloadIdAsync("test_collection", this._id2, true, It.IsAny<CancellationToken>()),
            Times.Once());
        mockQdrantClient.Verify<IAsyncEnumerable<QdrantVectorRecord>>(
            x => x.GetVectorsByIdAsync("test_collection", new[] { guidString }, false, It.IsAny<CancellationToken>()),
            Times.Once());
        mockQdrantClient.Verify<IAsyncEnumerable<QdrantVectorRecord>>(
            x => x.GetVectorsByIdAsync("test_collection", new[] { guidString }, true, It.IsAny<CancellationToken>()),
            Times.Once());
        mockQdrantClient.Verify<IAsyncEnumerable<QdrantVectorRecord>>(
            x => x.GetVectorsByIdAsync("test_collection", new[] { guidString2 }, false, It.IsAny<CancellationToken>()),
            Times.Once());
        mockQdrantClient.Verify<IAsyncEnumerable<QdrantVectorRecord>>(
            x => x.GetVectorsByIdAsync("test_collection", new[] { guidString2 }, true, It.IsAny<CancellationToken>()),
            Times.Once());
    }

    [Fact]
    public async Task GetAsyncSearchesByMetadataIdReturnsNullIfNotFoundAsync()
    {
        // Arrange
        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        mockQdrantClient
            .Setup<Task<QdrantVectorRecord?>>(x => x.GetVectorByPayloadIdAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync((QdrantVectorRecord?)null);

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object, this._mockLogger.Object);

        // Act
        var getResult = await vectorStore.GetAsync("test_collection", this._id, false);

        // Assert
        mockQdrantClient.Verify<Task<QdrantVectorRecord?>>(x => x.GetVectorByPayloadIdAsync("test_collection", this._id, It.IsAny<bool>(), It.IsAny<CancellationToken>()),
            Times.Once());
        Assert.Null(getResult);
    }

    [Fact]
    public async Task GetAsyncSearchesByMetadataIdReturnsMemoryRecordIfFoundAsync()
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
            memoryRecord.Embedding,
            memoryRecord.GetSerializedMetadata());

        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        mockQdrantClient
            .Setup<Task<QdrantVectorRecord?>>(x => x.GetVectorByPayloadIdAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(qdrantVectorRecord);

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object, this._mockLogger.Object);

        // Act
        var getResult = await vectorStore.GetAsync("test_collection", this._id, true);

        // Assert
        mockQdrantClient.Verify<Task<QdrantVectorRecord?>>(x => x.GetVectorByPayloadIdAsync("test_collection", this._id, It.IsAny<bool>(), It.IsAny<CancellationToken>()),
            Times.Once());
        Assert.NotNull(getResult);
        Assert.Equal(memoryRecord.Metadata.Id, getResult.Metadata.Id);
        Assert.Equal(memoryRecord.Metadata.Text, getResult.Metadata.Text);
        Assert.Equal(memoryRecord.Metadata.Description, getResult.Metadata.Description);
        Assert.Equal(memoryRecord.Metadata.ExternalSourceName, getResult.Metadata.ExternalSourceName);
        Assert.Equal(memoryRecord.Metadata.IsReference, getResult.Metadata.IsReference);
        Assert.True(memoryRecord.Embedding.Span.SequenceEqual(getResult.Embedding.Span));
    }

    [Fact]
    public async Task GetBatchAsyncSearchesByMetadataIdReturnsAllResultsIfAllFoundAsync()
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

        var key = Guid.NewGuid().ToString();
        var key2 = Guid.NewGuid().ToString();
        var key3 = Guid.NewGuid().ToString();

        var qdrantVectorRecord = QdrantVectorRecord.FromJsonMetadata(
            key,
            memoryRecord.Embedding,
            memoryRecord.GetSerializedMetadata());
        var qdrantVectorRecord2 = QdrantVectorRecord.FromJsonMetadata(
            key2,
            memoryRecord2.Embedding,
            memoryRecord2.GetSerializedMetadata());
        var qdrantVectorRecord3 = QdrantVectorRecord.FromJsonMetadata(
            key3,
            memoryRecord3.Embedding,
            memoryRecord3.GetSerializedMetadata());

        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        mockQdrantClient
            .Setup<Task<QdrantVectorRecord?>>(x => x.GetVectorByPayloadIdAsync(It.IsAny<string>(), this._id, It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(qdrantVectorRecord);
        mockQdrantClient
            .Setup<Task<QdrantVectorRecord?>>(x => x.GetVectorByPayloadIdAsync(It.IsAny<string>(), this._id2, It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(qdrantVectorRecord2);
        mockQdrantClient
            .Setup<Task<QdrantVectorRecord?>>(x => x.GetVectorByPayloadIdAsync(It.IsAny<string>(), this._id3, It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(qdrantVectorRecord3);

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object, this._mockLogger.Object);

        // Act
        var getBatchResult = await vectorStore.GetBatchAsync("test_collection", [this._id, this._id2, this._id3], false).ToListAsync();

        // Assert
        mockQdrantClient.Verify<Task<QdrantVectorRecord?>>(
            x => x.GetVectorByPayloadIdAsync("test_collection", It.IsAny<string>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()),
            Times.Exactly(3));
        mockQdrantClient.Verify<Task<QdrantVectorRecord?>>(x => x.GetVectorByPayloadIdAsync("test_collection", this._id, It.IsAny<bool>(), It.IsAny<CancellationToken>()),
            Times.Once());
        mockQdrantClient.Verify<Task<QdrantVectorRecord?>>(x => x.GetVectorByPayloadIdAsync("test_collection", this._id2, It.IsAny<bool>(), It.IsAny<CancellationToken>()),
            Times.Once());
        mockQdrantClient.Verify<Task<QdrantVectorRecord?>>(x => x.GetVectorByPayloadIdAsync("test_collection", this._id3, It.IsAny<bool>(), It.IsAny<CancellationToken>()),
            Times.Once());

        Assert.NotNull(getBatchResult);
        Assert.NotEmpty(getBatchResult);
        Assert.Equal(3, getBatchResult.Count);
        Assert.Equal(memoryRecord.Metadata.Id, getBatchResult[0].Metadata.Id);
        Assert.Equal(memoryRecord2.Metadata.Id, getBatchResult[1].Metadata.Id);
        Assert.Equal(memoryRecord3.Metadata.Id, getBatchResult[2].Metadata.Id);
        Assert.Equal(key, getBatchResult[0].Key);
        Assert.Equal(key2, getBatchResult[1].Key);
        Assert.Equal(key3, getBatchResult[2].Key);
    }

    [Fact]
    public async Task GetBatchAsyncSearchesByMetadataIdReturnsOnlyNonNullResultsAsync()
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

        var key = Guid.NewGuid().ToString();
        var key2 = Guid.NewGuid().ToString();

        var qdrantVectorRecord = QdrantVectorRecord.FromJsonMetadata(
            key,
            memoryRecord.Embedding,
            memoryRecord.GetSerializedMetadata());
        var qdrantVectorRecord2 = QdrantVectorRecord.FromJsonMetadata(
            key2,
            memoryRecord2.Embedding,
            memoryRecord2.GetSerializedMetadata());

        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        mockQdrantClient
            .Setup<Task<QdrantVectorRecord?>>(x => x.GetVectorByPayloadIdAsync(It.IsAny<string>(), this._id, It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(qdrantVectorRecord);
        mockQdrantClient
            .Setup<Task<QdrantVectorRecord?>>(x => x.GetVectorByPayloadIdAsync(It.IsAny<string>(), this._id2, It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(qdrantVectorRecord2);
        mockQdrantClient
            .Setup<Task<QdrantVectorRecord?>>(x => x.GetVectorByPayloadIdAsync(It.IsAny<string>(), this._id3, It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync((QdrantVectorRecord?)null);

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object, this._mockLogger.Object);

        // Act
        var getBatchResult = await vectorStore.GetBatchAsync("test_collection", [this._id, this._id2, this._id3], false).ToListAsync();

        // Assert
        mockQdrantClient.Verify<Task<QdrantVectorRecord?>>(
            x => x.GetVectorByPayloadIdAsync("test_collection", It.IsAny<string>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()),
            Times.Exactly(3));
        mockQdrantClient.Verify<Task<QdrantVectorRecord?>>(x => x.GetVectorByPayloadIdAsync("test_collection", this._id, It.IsAny<bool>(), It.IsAny<CancellationToken>()),
            Times.Once());
        mockQdrantClient.Verify<Task<QdrantVectorRecord?>>(x => x.GetVectorByPayloadIdAsync("test_collection", this._id2, It.IsAny<bool>(), It.IsAny<CancellationToken>()),
            Times.Once());
        mockQdrantClient.Verify<Task<QdrantVectorRecord?>>(x => x.GetVectorByPayloadIdAsync("test_collection", this._id3, It.IsAny<bool>(), It.IsAny<CancellationToken>()),
            Times.Once());
        Assert.NotNull(getBatchResult);
        Assert.NotEmpty(getBatchResult);
        Assert.Equal(2, getBatchResult.Count);
        Assert.Equal(memoryRecord.Metadata.Id, getBatchResult[0].Metadata.Id);
        Assert.Equal(memoryRecord2.Metadata.Id, getBatchResult[1].Metadata.Id);
        Assert.Equal(key, getBatchResult[0].Key);
        Assert.Equal(key2, getBatchResult[1].Key);
    }

    [Fact]
    public async Task GetBatchAsyncSearchesByMetadataIdReturnsEmptyListIfNoneFoundAsync()
    {
        // Arrange
        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        mockQdrantClient
            .Setup<Task<QdrantVectorRecord?>>(x => x.GetVectorByPayloadIdAsync(It.IsAny<string>(), this._id, It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync((QdrantVectorRecord?)null);
        mockQdrantClient
            .Setup<Task<QdrantVectorRecord?>>(x => x.GetVectorByPayloadIdAsync(It.IsAny<string>(), this._id2, It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync((QdrantVectorRecord?)null);
        mockQdrantClient
            .Setup<Task<QdrantVectorRecord?>>(x => x.GetVectorByPayloadIdAsync(It.IsAny<string>(), this._id3, It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync((QdrantVectorRecord?)null);

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object, this._mockLogger.Object);

        // Act
        var getBatchResult = await vectorStore.GetBatchAsync("test_collection", [this._id, this._id2, this._id3], false).ToListAsync();

        // Assert
        mockQdrantClient.Verify<Task<QdrantVectorRecord?>>(
            x => x.GetVectorByPayloadIdAsync("test_collection", It.IsAny<string>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()),
            Times.Exactly(3));
        mockQdrantClient.Verify<Task<QdrantVectorRecord?>>(x => x.GetVectorByPayloadIdAsync("test_collection", this._id, It.IsAny<bool>(), It.IsAny<CancellationToken>()),
            Times.Once());
        mockQdrantClient.Verify<Task<QdrantVectorRecord?>>(x => x.GetVectorByPayloadIdAsync("test_collection", this._id2, It.IsAny<bool>(), It.IsAny<CancellationToken>()),
            Times.Once());
        mockQdrantClient.Verify<Task<QdrantVectorRecord?>>(x => x.GetVectorByPayloadIdAsync("test_collection", this._id3, It.IsAny<bool>(), It.IsAny<CancellationToken>()),
            Times.Once());
        Assert.NotNull(getBatchResult);
        Assert.Empty(getBatchResult);
    }

    [Fact]
    public async Task GetByQdrantPointIdReturnsNullIfNotFoundAsync()
    {
        // Arrange
        var key = Guid.NewGuid().ToString();

        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        mockQdrantClient
            .Setup<IAsyncEnumerable<QdrantVectorRecord>>(x =>
                x.GetVectorsByIdAsync(It.IsAny<string>(), It.IsAny<IEnumerable<string>>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .Returns(AsyncEnumerable.Empty<QdrantVectorRecord>());

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object, this._mockLogger.Object);

        // Act
        var getResult = await vectorStore.GetWithPointIdAsync("test_collection", key, false);

        // Assert
        mockQdrantClient.Verify<IAsyncEnumerable<QdrantVectorRecord>>(
            x => x.GetVectorsByIdAsync("test_collection", new[] { key }, It.IsAny<bool>(), It.IsAny<CancellationToken>()),
            Times.Once());
        Assert.Null(getResult);
    }

    [Fact]
    public async Task GetByQdrantPointIdReturnsMemoryRecordIfFoundAsync()
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
            memoryRecord.Embedding,
            memoryRecord.GetSerializedMetadata());

        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        mockQdrantClient
            .Setup<IAsyncEnumerable<QdrantVectorRecord>>(x =>
                x.GetVectorsByIdAsync(It.IsAny<string>(), It.IsAny<IEnumerable<string>>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .Returns(new[] { qdrantVectorRecord }.ToAsyncEnumerable());

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object, this._mockLogger.Object);

        // Act
        var getResult = await vectorStore.GetWithPointIdAsync("test_collection", memoryRecord.Key, true);

        // Assert
        mockQdrantClient.Verify<IAsyncEnumerable<QdrantVectorRecord>>(
            x => x.GetVectorsByIdAsync("test_collection", new[] { memoryRecord.Key }, It.IsAny<bool>(), It.IsAny<CancellationToken>()),
            Times.Once());

        Assert.NotNull(getResult);
        Assert.Equal(memoryRecord.Metadata.Id, getResult.Metadata.Id);
        Assert.Equal(memoryRecord.Metadata.Text, getResult.Metadata.Text);
        Assert.Equal(memoryRecord.Metadata.Description, getResult.Metadata.Description);
        Assert.Equal(memoryRecord.Metadata.ExternalSourceName, getResult.Metadata.ExternalSourceName);
        Assert.Equal(memoryRecord.Metadata.IsReference, getResult.Metadata.IsReference);
        Assert.True(memoryRecord.Embedding.Span.SequenceEqual(getResult.Embedding.Span));
    }

    [Fact]
    public async Task GetBatchByQdrantPointIdsReturnsAllResultsIfFoundAsync()
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

        var key = Guid.NewGuid().ToString();
        var key2 = Guid.NewGuid().ToString();
        var key3 = Guid.NewGuid().ToString();

        var qdrantVectorRecord = QdrantVectorRecord.FromJsonMetadata(
            key,
            memoryRecord.Embedding,
            memoryRecord.GetSerializedMetadata());
        var qdrantVectorRecord2 = QdrantVectorRecord.FromJsonMetadata(
            key2,
            memoryRecord2.Embedding,
            memoryRecord2.GetSerializedMetadata());
        var qdrantVectorRecord3 = QdrantVectorRecord.FromJsonMetadata(
            key3,
            memoryRecord3.Embedding,
            memoryRecord3.GetSerializedMetadata());

        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        mockQdrantClient
            .Setup<IAsyncEnumerable<QdrantVectorRecord>>(x =>
                x.GetVectorsByIdAsync(It.IsAny<string>(), It.IsAny<IEnumerable<string>>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .Returns(new[] { qdrantVectorRecord, qdrantVectorRecord2, qdrantVectorRecord3 }.ToAsyncEnumerable());

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object, this._mockLogger.Object);

        // Act
        var getBatchResult = await vectorStore.GetWithPointIdBatchAsync("test_collection", [key, key2, key3], false).ToListAsync();

        // Assert
        mockQdrantClient.Verify<IAsyncEnumerable<QdrantVectorRecord>>(x =>
            x.GetVectorsByIdAsync(It.IsAny<string>(), It.IsAny<IEnumerable<string>>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()), Times.Once());

        Assert.NotNull(getBatchResult);
        Assert.NotEmpty(getBatchResult);
        Assert.Equal(3, getBatchResult.Count);
        Assert.Equal(memoryRecord.Metadata.Id, getBatchResult[0].Metadata.Id);
        Assert.Equal(memoryRecord2.Metadata.Id, getBatchResult[1].Metadata.Id);
        Assert.Equal(memoryRecord3.Metadata.Id, getBatchResult[2].Metadata.Id);
        Assert.Equal(key, getBatchResult[0].Key);
        Assert.Equal(key2, getBatchResult[1].Key);
        Assert.Equal(key3, getBatchResult[2].Key);
    }

    [Fact]
    public async Task GetBatchByQdrantPointIdsReturnsEmptyEnumerableIfNonFoundAsync()
    {
        // Arrange
        var key = Guid.NewGuid().ToString();
        var key2 = Guid.NewGuid().ToString();
        var key3 = Guid.NewGuid().ToString();

        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        mockQdrantClient
            .Setup<IAsyncEnumerable<QdrantVectorRecord>>(x =>
                x.GetVectorsByIdAsync(It.IsAny<string>(), It.IsAny<IEnumerable<string>>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()))
            .Returns(AsyncEnumerable.Empty<QdrantVectorRecord>());

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object, this._mockLogger.Object);

        // Act
        var getBatchResult = await vectorStore.GetWithPointIdBatchAsync("test_collection", [key, key2, key3], false).ToListAsync();

        // Assert
        mockQdrantClient.Verify<IAsyncEnumerable<QdrantVectorRecord>>(x =>
            x.GetVectorsByIdAsync(It.IsAny<string>(), It.IsAny<IEnumerable<string>>(), It.IsAny<bool>(), It.IsAny<CancellationToken>()), Times.Once());

        Assert.Empty(getBatchResult);
    }

    [Fact]
    public async Task ItCanRemoveAVectorUsingMetadataIdAsync()
    {
        // Arrange
        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        mockQdrantClient
            .Setup<Task>(x =>
                x.DeleteVectorByPayloadIdAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object, this._mockLogger.Object);

        // Act
        await vectorStore.RemoveAsync("test_collection", this._id);

        // Assert
        mockQdrantClient.Verify<Task>(x =>
            x.DeleteVectorByPayloadIdAsync(It.IsAny<string>(), this._id, It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task ItCanRemoveBatchVectorsUsingMetadataIdAsync()
    {
        // Arrange
        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        mockQdrantClient
            .Setup<Task>(x =>
                x.DeleteVectorByPayloadIdAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object, this._mockLogger.Object);

        // Act
        await vectorStore.RemoveBatchAsync("test_collection", [this._id, this._id2, this._id3]);

        // Assert
        mockQdrantClient.Verify<Task>(x =>
            x.DeleteVectorByPayloadIdAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<CancellationToken>()), Times.Exactly(3));
        mockQdrantClient.Verify<Task>(x =>
            x.DeleteVectorByPayloadIdAsync(It.IsAny<string>(), this._id, It.IsAny<CancellationToken>()), Times.Once());
        mockQdrantClient.Verify<Task>(x =>
            x.DeleteVectorByPayloadIdAsync(It.IsAny<string>(), this._id2, It.IsAny<CancellationToken>()), Times.Once());
        mockQdrantClient.Verify<Task>(x =>
            x.DeleteVectorByPayloadIdAsync(It.IsAny<string>(), this._id3, It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task ItCanRemoveAVectorUsingDatabaseKeyAsync()
    {
        // Arrange
        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        mockQdrantClient
            .Setup<Task>(x =>
                x.DeleteVectorsByIdAsync(It.IsAny<string>(), It.IsAny<IEnumerable<string>>(), It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object, this._mockLogger.Object);
        var key = Guid.NewGuid().ToString();

        // Act
        await vectorStore.RemoveWithPointIdAsync("test_collection", key);

        // Assert
        mockQdrantClient.Verify<Task>(x =>
            x.DeleteVectorsByIdAsync(It.IsAny<string>(), new[] { key }, It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task ItCanRemoveBatchVectorsUsingDatabaseKeyAsync()
    {
        // Arrange
        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        mockQdrantClient
            .Setup<Task>(x =>
                x.DeleteVectorsByIdAsync(It.IsAny<string>(), It.IsAny<IEnumerable<string>>(), It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object, this._mockLogger.Object);
        var key = Guid.NewGuid().ToString();
        var key2 = Guid.NewGuid().ToString();
        var key3 = Guid.NewGuid().ToString();

        // Act
        await vectorStore.RemoveWithPointIdBatchAsync("test_collection", [key, key2, key3]);

        // Assert
        mockQdrantClient.Verify<Task>(x =>
            x.DeleteVectorsByIdAsync(It.IsAny<string>(), It.IsAny<IEnumerable<string>>(), It.IsAny<CancellationToken>()), Times.Once());
        mockQdrantClient.Verify<Task>(x =>
            x.DeleteVectorsByIdAsync(It.IsAny<string>(), new[] { key, key2, key3 }, It.IsAny<CancellationToken>()), Times.Once());
    }
}
