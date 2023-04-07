// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Connectors.Memory.Qdrant;
using Microsoft.SemanticKernel.Memory;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.Memory.Qdrant;

/// <summary>
/// Tests for <see cref="QdrantMemoryStore"/> Search operations.
/// </summary>
public class QdrantMemoryStoreTests3
{
    private readonly string _id = "Id";
    private readonly string _text = "text";
    private readonly string _description = "description";
    private readonly Embedding<float> _embedding = new Embedding<float>(new float[] { 1, 1, 1 });

    [Fact]
    public async Task ItReturnsEmptyTupleIfNearestMatchNotFoundAsync()
    {
        // Arrange
        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        mockQdrantClient
            .Setup<IAsyncEnumerable<(QdrantVectorRecord, double)>>(x => x.FindNearestInCollectionAsync(
                It.IsAny<string>(),
                It.IsAny<IEnumerable<float>>(),
                It.IsAny<double>(),
                It.IsAny<int>(),
                null,
                It.IsAny<CancellationToken>()))
            .Returns(AsyncEnumerable.Empty<(QdrantVectorRecord, double)>());

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object);

        // Act
        var similarityResult = await vectorStore.GetNearestMatchAsync(
            collectionName: "test_collection",
            embedding: this._embedding,
            minRelevanceScore: 0.0);

        // Assert
        mockQdrantClient.Verify<IAsyncEnumerable<(QdrantVectorRecord, double)>>(x => x.FindNearestInCollectionAsync(
                It.IsAny<string>(),
                It.IsAny<IEnumerable<float>>(),
                It.IsAny<double>(),
                It.IsAny<int>(),
                null,
                It.IsAny<CancellationToken>()),
            Times.Once());
        Assert.NotNull(similarityResult);
        Assert.Null(similarityResult.Value.Item1);
        Assert.Equal(0.0, similarityResult.Value.Item2);
    }

    [Fact]
    public async Task ItWillReturnTheNearestMatchAsATupleAsync()
    {
        // Arrange
        var memoryRecord = MemoryRecord.LocalRecord(
            id: this._id,
            text: this._text,
            description: this._description,
            embedding: this._embedding);

        memoryRecord.Key = Guid.NewGuid().ToString();

        var qdrantVectorRecord = QdrantVectorRecord.FromJson(
            memoryRecord.Key,
            memoryRecord.Embedding.Vector,
            memoryRecord.GetSerializedMetadata());

        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        mockQdrantClient
            .Setup<IAsyncEnumerable<(QdrantVectorRecord, double)>>(x => x.FindNearestInCollectionAsync(
                It.IsAny<string>(),
                It.IsAny<IEnumerable<float>>(),
                It.IsAny<double>(),
                It.IsAny<int>(),
                null,
                It.IsAny<CancellationToken>()))
            .Returns(new[] { (qdrantVectorRecord, 0.5) }.ToAsyncEnumerable());

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object);

        // Act
        var similarityResult = await vectorStore.GetNearestMatchAsync(
            collectionName: "test_collection",
            embedding: this._embedding,
            minRelevanceScore: 0.0);

        // Assert
        mockQdrantClient.Verify<IAsyncEnumerable<(QdrantVectorRecord, double)>>(x => x.FindNearestInCollectionAsync(
                It.IsAny<string>(),
                It.IsAny<IEnumerable<float>>(),
                It.IsAny<double>(),
                It.IsAny<int>(),
                null,
                It.IsAny<CancellationToken>()),
            Times.Once());
        Assert.NotNull(similarityResult);
        Assert.Equal(this._id, similarityResult.Value.Item1.Metadata.Id);
        Assert.Equal(this._text, similarityResult.Value.Item1.Metadata.Text);
        Assert.Equal(this._description, similarityResult.Value.Item1.Metadata.Description);
        Assert.Equal(this._embedding.Vector, similarityResult.Value.Item1.Embedding.Vector);
        Assert.Equal(0.5, similarityResult.Value.Item2);
    }

    [Fact]
    public async Task ItReturnsEmptyListIfNearestMatchesNotFoundAsync()
    {
        // Arrange
        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        mockQdrantClient
            .Setup<IAsyncEnumerable<(QdrantVectorRecord, double)>>(x => x.FindNearestInCollectionAsync(
                It.IsAny<string>(),
                It.IsAny<IEnumerable<float>>(),
                It.IsAny<double>(),
                It.IsAny<int>(),
                null,
                It.IsAny<CancellationToken>()))
            .Returns(AsyncEnumerable.Empty<(QdrantVectorRecord, double)>());

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object);

        // Act
        var similarityResults = await vectorStore.GetNearestMatchesAsync(
            collectionName: "test_collection",
            embedding: this._embedding,
            limit: 3,
            minRelevanceScore: 0.0).ToListAsync();

        // Assert
        Assert.Empty(similarityResults);
    }
}
