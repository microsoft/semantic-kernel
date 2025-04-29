// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Microsoft.SemanticKernel.Memory;
using Moq;
using Moq.Protected;
using Xunit;

namespace SemanticKernel.Connectors.Qdrant.UnitTests;

/// <summary>
/// Tests for <see cref="QdrantMemoryStore"/> Search operations.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted")]
public class QdrantMemoryStoreTests3
{
    private readonly string _id = "Id";
    private readonly string _text = "text";
    private readonly string _description = "description";
    private readonly ReadOnlyMemory<float> _embedding = new float[] { 1, 1, 1 };
    private readonly Mock<ILoggerFactory> _mockLoggerFactory = new();

    [Fact]
    public async Task GetNearestMatchesAsyncCallsDoNotReturnVectorsUnlessSpecifiedAsync()
    {
        // Arrange
        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        mockQdrantClient
            .Setup<IAsyncEnumerable<(QdrantVectorRecord, double)>>(x => x.FindNearestInCollectionAsync(
                It.IsAny<string>(),
                It.IsAny<ReadOnlyMemory<float>>(),
                It.IsAny<double>(),
                It.IsAny<int>(),
                It.IsAny<bool>(),
                null,
                It.IsAny<CancellationToken>()))
            .Returns(AsyncEnumerable.Empty<(QdrantVectorRecord, double)>());

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object, this._mockLoggerFactory.Object);

        // Act
        _ = await vectorStore.GetNearestMatchAsync(
            collectionName: "test_collection",
            embedding: this._embedding,
            minRelevanceScore: 0.0);
        _ = await vectorStore.GetNearestMatchAsync(
            collectionName: "test_collection",
            embedding: this._embedding,
            withEmbedding: true,
            minRelevanceScore: 0.0);
        _ = await vectorStore.GetNearestMatchesAsync(
            collectionName: "test_collection",
            embedding: this._embedding,
            limit: 3,
            minRelevanceScore: 0.0).ToListAsync();
        _ = await vectorStore.GetNearestMatchesAsync(
            collectionName: "test_collection",
            embedding: this._embedding,
            limit: 3,
            withEmbeddings: true,
            minRelevanceScore: 0.0).ToListAsync();

        // Assert
        mockQdrantClient.Verify<IAsyncEnumerable<(QdrantVectorRecord, double)>>(x => x.FindNearestInCollectionAsync(
                It.IsAny<string>(),
                It.IsAny<ReadOnlyMemory<float>>(),
                It.IsAny<double>(),
                1,
                false,
                null,
                It.IsAny<CancellationToken>()),
            Times.Once());
        mockQdrantClient.Verify<IAsyncEnumerable<(QdrantVectorRecord, double)>>(x => x.FindNearestInCollectionAsync(
                It.IsAny<string>(),
                It.IsAny<ReadOnlyMemory<float>>(),
                It.IsAny<double>(),
                1,
                true,
                null,
                It.IsAny<CancellationToken>()),
            Times.Once());
        mockQdrantClient.Verify<IAsyncEnumerable<(QdrantVectorRecord, double)>>(x => x.FindNearestInCollectionAsync(
                It.IsAny<string>(),
                It.IsAny<ReadOnlyMemory<float>>(),
                It.IsAny<double>(),
                3,
                false,
                null,
                It.IsAny<CancellationToken>()),
            Times.Once());
        mockQdrantClient.Verify<IAsyncEnumerable<(QdrantVectorRecord, double)>>(x => x.FindNearestInCollectionAsync(
                It.IsAny<string>(),
                It.IsAny<ReadOnlyMemory<float>>(),
                It.IsAny<double>(),
                3,
                true,
                null,
                It.IsAny<CancellationToken>()),
            Times.Once());
    }

    [Fact]
    public async Task ItReturnsEmptyTupleIfNearestMatchNotFoundAsync()
    {
        // Arrange
        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        mockQdrantClient
            .Setup<IAsyncEnumerable<(QdrantVectorRecord, double)>>(x => x.FindNearestInCollectionAsync(
                It.IsAny<string>(),
                It.IsAny<ReadOnlyMemory<float>>(),
                It.IsAny<double>(),
                It.IsAny<int>(),
                It.IsAny<bool>(),
                null,
                It.IsAny<CancellationToken>()))
            .Returns(AsyncEnumerable.Empty<(QdrantVectorRecord, double)>());

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object, this._mockLoggerFactory.Object);

        // Act
        var similarityResult = await vectorStore.GetNearestMatchAsync(
            collectionName: "test_collection",
            embedding: this._embedding,
            minRelevanceScore: 0.0);

        // Assert
        mockQdrantClient.Verify<IAsyncEnumerable<(QdrantVectorRecord, double)>>(x => x.FindNearestInCollectionAsync(
                It.IsAny<string>(),
                It.IsAny<ReadOnlyMemory<float>>(),
                It.IsAny<double>(),
                It.IsAny<int>(),
                It.IsAny<bool>(),
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

        var qdrantVectorRecord = QdrantVectorRecord.FromJsonMetadata(
            memoryRecord.Key,
            memoryRecord.Embedding,
            memoryRecord.GetSerializedMetadata());

        var mockQdrantClient = new Mock<IQdrantVectorDbClient>();
        mockQdrantClient
            .Setup<IAsyncEnumerable<(QdrantVectorRecord, double)>>(x => x.FindNearestInCollectionAsync(
                It.IsAny<string>(),
                It.IsAny<ReadOnlyMemory<float>>(),
                It.IsAny<double>(),
                It.IsAny<int>(),
                It.IsAny<bool>(),
                null,
                It.IsAny<CancellationToken>()))
            .Returns(new[] { (qdrantVectorRecord, 0.5) }.ToAsyncEnumerable());

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object, this._mockLoggerFactory.Object);

        // Act
        var similarityResult = await vectorStore.GetNearestMatchAsync(
            collectionName: "test_collection",
            embedding: this._embedding,
            minRelevanceScore: 0.0);

        // Assert
        mockQdrantClient.Verify<IAsyncEnumerable<(QdrantVectorRecord, double)>>(x => x.FindNearestInCollectionAsync(
                It.IsAny<string>(),
                It.IsAny<ReadOnlyMemory<float>>(),
                It.IsAny<double>(),
                It.IsAny<int>(),
                It.IsAny<bool>(),
                null,
                It.IsAny<CancellationToken>()),
            Times.Once());
        Assert.NotNull(similarityResult);
        Assert.Equal(this._id, similarityResult.Value.Item1.Metadata.Id);
        Assert.Equal(this._text, similarityResult.Value.Item1.Metadata.Text);
        Assert.Equal(this._description, similarityResult.Value.Item1.Metadata.Description);
        Assert.True(this._embedding.Span.SequenceEqual(similarityResult.Value.Item1.Embedding.Span));
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
                It.IsAny<ReadOnlyMemory<float>>(),
                It.IsAny<double>(),
                It.IsAny<int>(),
                It.IsAny<bool>(),
                null,
                It.IsAny<CancellationToken>()))
            .Returns(AsyncEnumerable.Empty<(QdrantVectorRecord, double)>());

        var vectorStore = new QdrantMemoryStore(mockQdrantClient.Object, this._mockLoggerFactory.Object);

        // Act
        var similarityResults = await vectorStore.GetNearestMatchesAsync(
            collectionName: "test_collection",
            embedding: this._embedding,
            limit: 3,
            minRelevanceScore: 0.0).ToListAsync();

        // Assert
        Assert.Empty(similarityResults);
    }

    [Fact]
    public async Task ScoredVectorSupportsIntegerIdsAsync()
    {
        // Arrange
        var payloadId = "payloadId";
        var metadataId = "metadataId";
        var expectedId = 100;

        var scoredPointJsonWithIntegerId =
            "{" +
                "\"result\": " +
                "   [{" +
                        "\"id\": " + expectedId + "," +
                        "\"version\": 0," +
                        "\"score\": null," +
                        "\"payload\": {}," +
                        "\"vector\": null " +
                    "}]" +
            "}";

        using var httpResponseMessage = new HttpResponseMessage { StatusCode = HttpStatusCode.OK, Content = new StringContent(scoredPointJsonWithIntegerId) };

        var mockHttpMessageHandler = new Mock<HttpMessageHandler>();
        mockHttpMessageHandler.Protected()
            .Setup<Task<HttpResponseMessage>>("SendAsync", ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>())
            .ReturnsAsync(httpResponseMessage);

        //Act
        using var httpClient = new HttpClient(mockHttpMessageHandler.Object);
        {
            var client = new QdrantVectorDbClient(httpClient, 1536, "https://fake-random-test-host");
            var result = await client.GetVectorByPayloadIdAsync(payloadId, metadataId);

            //Assert
            Assert.Equal(result!.PointId, expectedId.ToString(CultureInfo.InvariantCulture));
        }
    }
}
