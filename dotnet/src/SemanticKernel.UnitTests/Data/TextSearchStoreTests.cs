// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Embeddings;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Data;

public class TextSearchStoreTests
{
    private readonly Mock<IVectorStore> _vectorStoreMock;
    private readonly Mock<ITextEmbeddingGenerationService> _embeddingServiceMock;
    private readonly Mock<IVectorStoreRecordCollection<string, TextSearchStore<string>.TextRagStorageDocument<string>>> _recordCollectionMock;

    public TextSearchStoreTests()
    {
        this._vectorStoreMock = new Mock<IVectorStore>();
        this._recordCollectionMock = new Mock<IVectorStoreRecordCollection<string, TextSearchStore<string>.TextRagStorageDocument<string>>>();
        this._embeddingServiceMock = new Mock<ITextEmbeddingGenerationService>();

        this._vectorStoreMock
            .Setup(v => v.GetCollection<string, TextSearchStore<string>.TextRagStorageDocument<string>>("testCollection", It.IsAny<VectorStoreRecordDefinition>()))
            .Returns(this._recordCollectionMock.Object);

        this._embeddingServiceMock
            .Setup(e => e.GenerateEmbeddingsAsync(It.IsAny<IList<string>>(), null, It.IsAny<CancellationToken>()))
            .ReturnsAsync(new[] { new ReadOnlyMemory<float>(new float[128]) });
    }

    [Fact]
    public async Task UpsertDocumentsAsyncThrowsWhenDocumentsAreNull()
    {
        // Arrange
        using var store = new TextSearchStore<string>(this._vectorStoreMock.Object, this._embeddingServiceMock.Object, "testCollection", 128);

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentNullException>(() => store.UpsertDocumentsAsync(null!));
    }

    [Theory]
    [InlineData(null)]
    [InlineData(" ")]
    public async Task UpsertDocumentsAsyncThrowsDocumentTextIsNullOrWhiteSpace(string? text)
    {
        // Arrange
        using var store = new TextSearchStore<string>(this._vectorStoreMock.Object, this._embeddingServiceMock.Object, "testCollection", 128);

        var documents = new List<TextSearchDocument>
        {
            new() { Text = text }
        };

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(() => store.UpsertDocumentsAsync(documents));
    }

    [Fact]
    public async Task UpsertDocumentsAsyncCreatesCollectionGeneratesVectorAndUpsertsDocument()
    {
        // Arrange
        this._recordCollectionMock
            .Setup(r => r.UpsertBatchAsync(It.IsAny<IEnumerable<TextSearchStore<string>.TextRagStorageDocument<string>>>(), It.IsAny<CancellationToken>()))
            .Returns(AsyncEnumerable.Empty<string>());

        using var store = new TextSearchStore<string>(this._vectorStoreMock.Object, this._embeddingServiceMock.Object, "testCollection", 128);

        var documents = new List<TextSearchDocument>
        {
            new() { Text = "Sample text", Namespaces = ["ns1"], SourceId = "sid", SourceLink = "sl", SourceName = "sn" }
        };

        // Act
        await store.UpsertDocumentsAsync(documents);

        // Assert
        this._recordCollectionMock.Verify(r => r.CreateCollectionIfNotExistsAsync(It.IsAny<CancellationToken>()), Times.Once);
        this._embeddingServiceMock.Verify(e => e.GenerateEmbeddingsAsync(It.Is<IList<string>>(texts => texts.Count == 1 && texts[0] == "Sample text"), null, It.IsAny<CancellationToken>()), Times.Once);
        this._recordCollectionMock.Verify(r => r.UpsertBatchAsync(
            It.Is<IEnumerable<TextSearchStore<string>.TextRagStorageDocument<string>>>(doc =>
                doc.Count() == 1 &&
                doc.First().Text == "Sample text" &&
                doc.First().Namespaces.Count == 1 &&
                doc.First().Namespaces[0] == "ns1" &&
                doc.First().SourceId == "sid" &&
                doc.First().SourceLink == "sl" &&
                doc.First().SourceName == "sn" &&
                doc.First().TextEmbedding.Length == 128),
            It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task UpsertDocumentsAsyncCreatesCollectionGeneratesVectorAndUpsertsDocumentWithSourceIdAsId()
    {
        // Arrange
        this._recordCollectionMock
            .Setup(r => r.UpsertBatchAsync(It.IsAny<IEnumerable<TextSearchStore<string>.TextRagStorageDocument<string>>>(), It.IsAny<CancellationToken>()))
            .Returns(AsyncEnumerable.Empty<string>());

        using var store = new TextSearchStore<string>(this._vectorStoreMock.Object, this._embeddingServiceMock.Object, "testCollection", 128, new() { UseSourceIdAsPrimaryKey = true });

        var documents = new List<TextSearchDocument>
        {
            new() { Text = "Sample text", Namespaces = ["ns1"], SourceId = "sid", SourceLink = "sl", SourceName = "sn" }
        };

        // Act
        await store.UpsertDocumentsAsync(documents);

        // Assert
        this._recordCollectionMock.Verify(r => r.UpsertBatchAsync(
            It.Is<IEnumerable<TextSearchStore<string>.TextRagStorageDocument<string>>>(doc =>
                doc.Count() == 1 &&
                doc.First().Key == "sid" &&
                doc.First().Text == "Sample text" &&
                doc.First().Namespaces.Count == 1 &&
                doc.First().Namespaces[0] == "ns1" &&
                doc.First().SourceId == "sid" &&
                doc.First().SourceLink == "sl" &&
                doc.First().SourceName == "sn" &&
                doc.First().TextEmbedding.Length == 128),
            It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task UpsertDocumentsAsyncCreatesCollectionGeneratesVectorAndUpsertsDocumentWithoutSourceText()
    {
        // Arrange
        this._recordCollectionMock
            .Setup(r => r.UpsertBatchAsync(It.IsAny<IEnumerable<TextSearchStore<string>.TextRagStorageDocument<string>>>(), It.IsAny<CancellationToken>()))
            .Returns(AsyncEnumerable.Empty<string>());

        using var store = new TextSearchStore<string>(this._vectorStoreMock.Object, this._embeddingServiceMock.Object, "testCollection", 128);

        var documents = new List<TextSearchDocument>
        {
            new() { Text = "Sample text", Namespaces = ["ns1"], SourceId = "sid", SourceLink = "sl", SourceName = "sn" }
        };

        // Act
        await store.UpsertDocumentsAsync(documents, new() { PersistSourceText = false });

        // Assert
        this._recordCollectionMock.Verify(r => r.UpsertBatchAsync(
            It.Is<IEnumerable<TextSearchStore<string>.TextRagStorageDocument<string>>>(doc =>
                doc.Count() == 1 &&
                doc.First().Text == null &&
                doc.First().Namespaces.Count == 1 &&
                doc.First().Namespaces[0] == "ns1" &&
                doc.First().SourceId == "sid" &&
                doc.First().SourceLink == "sl" &&
                doc.First().SourceName == "sn" &&
                doc.First().TextEmbedding.Length == 128),
            It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task SearchAsyncReturnsSearchResults()
    {
        // Arrange
        var mockResults = new List<VectorSearchResult<TextSearchStore<string>.TextRagStorageDocument<string>>>
        {
            new(new TextSearchStore<string>.TextRagStorageDocument<string> { Text = "Sample text" }, 0.9f)
        };

        this._recordCollectionMock
            .Setup(r => r.VectorizedSearchAsync(It.IsAny<ReadOnlyMemory<float>>(), It.IsAny<VectorSearchOptions<TextSearchStore<string>.TextRagStorageDocument<string>>>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new VectorSearchResults<TextSearchStore<string>.TextRagStorageDocument<string>>(mockResults.ToAsyncEnumerable()));

        using var store = new TextSearchStore<string>(this._vectorStoreMock.Object, this._embeddingServiceMock.Object, "testCollection", 128);

        // Act
        var actualResults = await store.SearchAsync("query");

        // Assert
        var actualResultsList = await actualResults.Results.ToListAsync();
        Assert.Single(actualResultsList);
        Assert.Equal("Sample text", actualResultsList[0]);
    }

    [Fact]
    public async Task SearchAsyncWithHydrationCallsCallbackAndReturnsSearchResults()
    {
        // Arrange
        var mockResults = new List<VectorSearchResult<TextSearchStore<string>.TextRagStorageDocument<string>>>
        {
            new(new TextSearchStore<string>.TextRagStorageDocument<string> { SourceId = "sid1", SourceLink = "sl1", Text = "Sample text 1" }, 0.9f),
            new(new TextSearchStore<string>.TextRagStorageDocument<string> { SourceId = "sid2", SourceLink = "sl2" }, 0.9f),
            new(new TextSearchStore<string>.TextRagStorageDocument<string> { SourceId = "sid3", SourceLink = "sl3", Text = "Sample text 3" }, 0.9f),
        };

        this._recordCollectionMock
            .Setup(r => r.VectorizedSearchAsync(It.IsAny<ReadOnlyMemory<float>>(), It.IsAny<VectorSearchOptions<TextSearchStore<string>.TextRagStorageDocument<string>>>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new VectorSearchResults<TextSearchStore<string>.TextRagStorageDocument<string>>(mockResults.ToAsyncEnumerable()));

        using var store = new TextSearchStore<string>(
            this._vectorStoreMock.Object,
            this._embeddingServiceMock.Object,
            "testCollection",
            128,
            new()
            {
                SourceRetrievalCallback = sourceIds =>
                {
                    Assert.Single(sourceIds);
                    Assert.Equal("sid2", sourceIds[0].SourceId);
                    Assert.Equal("sl2", sourceIds[0].SourceLink);

                    return Task.FromResult<IEnumerable<TextSearchStoreSourceRetrievalResponse>>([new TextSearchStoreSourceRetrievalResponse(new TextSearchStoreSourceRetrievalRequest("sid2", "sl2"), "Sample text 2")]);
                }
            });

        // Act
        var actualResults = await store.SearchAsync("query");

        // Assert
        var actualResultsList = await actualResults.Results.ToListAsync();
        Assert.Equal(3, actualResultsList.Count);
        Assert.Equal("Sample text 1", actualResultsList[0]);
        Assert.Equal("Sample text 2", actualResultsList[1]);
        Assert.Equal("Sample text 3", actualResultsList[2]);
    }
}
