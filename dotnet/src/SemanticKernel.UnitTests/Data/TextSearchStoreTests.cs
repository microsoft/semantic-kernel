// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Data;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Data;

public class TextSearchStoreTests
{
    private readonly Mock<VectorStore> _vectorStoreMock;
    private readonly Mock<VectorStoreCollection<string, TextSearchStore<string>.TextRagStorageDocument<string>>> _recordCollectionMock;
    private readonly Mock<IKeywordHybridSearchable<TextSearchStore<string>.TextRagStorageDocument<string>>> _keywordHybridSearchableMock;

    public TextSearchStoreTests()
    {
        this._vectorStoreMock = new Mock<VectorStore>();
        this._recordCollectionMock = new Mock<VectorStoreCollection<string, TextSearchStore<string>.TextRagStorageDocument<string>>>();
        this._keywordHybridSearchableMock = new Mock<IKeywordHybridSearchable<TextSearchStore<string>.TextRagStorageDocument<string>>>();

        this._vectorStoreMock
            .Setup(v => v.GetCollection<string, TextSearchStore<string>.TextRagStorageDocument<string>>("testCollection", It.IsAny<VectorStoreCollectionDefinition>()))
            .Returns(this._recordCollectionMock.Object);
    }

    [Fact]
    public async Task UpsertDocumentsAsyncThrowsWhenDocumentsAreNull()
    {
        // Arrange
        using var store = new TextSearchStore<string>(this._vectorStoreMock.Object, "testCollection", 128);

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentNullException>(() => store.UpsertDocumentsAsync(null!));
    }

    [Fact]
    public async Task UpsertTextAsyncThrowsWhenDocumentsAreNull()
    {
        // Arrange
        using var store = new TextSearchStore<string>(this._vectorStoreMock.Object, "testCollection", 128);

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentNullException>(() => store.UpsertTextAsync(null!));
    }

    [Theory]
    [InlineData(null)]
    [InlineData(" ")]
    public async Task UpsertDocumentsAsyncThrowsDocumentTextIsNullOrWhiteSpace(string? text)
    {
        // Arrange
        using var store = new TextSearchStore<string>(this._vectorStoreMock.Object, "testCollection", 128);
        this._recordCollectionMock
            .Setup(r => r.UpsertAsync(It.IsAny<IEnumerable<TextSearchStore<string>.TextRagStorageDocument<string>>>(), It.IsAny<CancellationToken>()))
            .Callback(
                (IEnumerable<TextSearchStore<string>.TextRagStorageDocument<string>> documents, CancellationToken token) =>
                {
                    // Enumerate upserted documents to trigger the exception.
                    var a = documents.ToList();
                })
            .Returns(Task.CompletedTask);

        var documents = new List<TextSearchDocument>
        {
            new() { Text = text }
        };

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(() => store.UpsertDocumentsAsync(documents));
    }

    [Theory]
    [InlineData(null)]
    [InlineData(" ")]
    public async Task UpsertTextAsyncThrowsDocumentTextIsNullOrWhiteSpace(string? text)
    {
        // Arrange
        using var store = new TextSearchStore<string>(this._vectorStoreMock.Object, "testCollection", 128);
        this._recordCollectionMock
            .Setup(r => r.UpsertAsync(It.IsAny<IEnumerable<TextSearchStore<string>.TextRagStorageDocument<string>>>(), It.IsAny<CancellationToken>()))
            .Callback(
                (IEnumerable<TextSearchStore<string>.TextRagStorageDocument<string>> documents, CancellationToken token) =>
                {
                    // Enumerate upserted documents to trigger the exception.
                    var a = documents.ToList();
                })
            .Returns(Task.CompletedTask);

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(() => store.UpsertTextAsync([text!]));
    }

    [Fact]
    public async Task UpsertDocumentsAsyncCreatesCollectionUpsertsDocument()
    {
        // Arrange
        this._recordCollectionMock
            .Setup(r => r.UpsertAsync(It.IsAny<IEnumerable<TextSearchStore<string>.TextRagStorageDocument<string>>>(), It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        using var store = new TextSearchStore<string>(this._vectorStoreMock.Object, "testCollection", 128);

        var documents = new List<TextSearchDocument>
        {
            new() { Text = "Sample text", Namespaces = ["ns1"], SourceId = "sid", SourceLink = "sl", SourceName = "sn" }
        };

        // Act
        await store.UpsertDocumentsAsync(documents);

        // Assert
        this._recordCollectionMock.Verify(r => r.EnsureCollectionExistsAsync(It.IsAny<CancellationToken>()), Times.Once);
        this._recordCollectionMock.Verify(r => r.UpsertAsync(
            It.Is<IEnumerable<TextSearchStore<string>.TextRagStorageDocument<string>>>(doc =>
                doc.Count() == 1 &&
                doc.First().Text == "Sample text" &&
                doc.First().Namespaces.Count == 1 &&
                doc.First().Namespaces[0] == "ns1" &&
                doc.First().SourceId == "sid" &&
                doc.First().SourceLink == "sl" &&
                doc.First().SourceName == "sn" &&
                doc.First().TextEmbedding == "Sample text"),
            It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task UpsertDocumentsAsyncCreatesCollectionUpsertsDocumentWithSourceIdAsId()
    {
        // Arrange
        this._recordCollectionMock
            .Setup(r => r.UpsertAsync(It.IsAny<IEnumerable<TextSearchStore<string>.TextRagStorageDocument<string>>>(), It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        using var store = new TextSearchStore<string>(this._vectorStoreMock.Object, "testCollection", 128, new() { UseSourceIdAsPrimaryKey = true });

        var documents = new List<TextSearchDocument>
        {
            new() { Text = "Sample text", Namespaces = ["ns1"], SourceId = "sid", SourceLink = "sl", SourceName = "sn" }
        };

        // Act
        await store.UpsertDocumentsAsync(documents);

        // Assert
        this._recordCollectionMock.Verify(r => r.UpsertAsync(
            It.Is<IEnumerable<TextSearchStore<string>.TextRagStorageDocument<string>>>(doc =>
                doc.Count() == 1 &&
                doc.First().Key == "sid" &&
                doc.First().Text == "Sample text" &&
                doc.First().Namespaces.Count == 1 &&
                doc.First().Namespaces[0] == "ns1" &&
                doc.First().SourceId == "sid" &&
                doc.First().SourceLink == "sl" &&
                doc.First().SourceName == "sn" &&
                doc.First().TextEmbedding == "Sample text"),
            It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task UpsertDocumentsAsyncCreatesCollectionUpsertsDocumentWithoutSourceText()
    {
        // Arrange
        this._recordCollectionMock
            .Setup(r => r.UpsertAsync(It.IsAny<IEnumerable<TextSearchStore<string>.TextRagStorageDocument<string>>>(), It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        using var store = new TextSearchStore<string>(this._vectorStoreMock.Object, "testCollection", 128);

        var documents = new List<TextSearchDocument>
        {
            new() { Text = "Sample text", Namespaces = ["ns1"], SourceId = "sid", SourceLink = "sl", SourceName = "sn" }
        };

        // Act
        await store.UpsertDocumentsAsync(documents, new() { PersistSourceText = false });

        // Assert
        this._recordCollectionMock.Verify(r => r.UpsertAsync(
            It.Is<IEnumerable<TextSearchStore<string>.TextRagStorageDocument<string>>>(doc =>
                doc.Count() == 1 &&
                doc.First().Text == null &&
                doc.First().Namespaces.Count == 1 &&
                doc.First().Namespaces[0] == "ns1" &&
                doc.First().SourceId == "sid" &&
                doc.First().SourceLink == "sl" &&
                doc.First().SourceName == "sn" &&
                doc.First().TextEmbedding == "Sample text"),
            It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task UpsertTextAsyncCreatesCollectionUpsertsDocument()
    {
        // Arrange
        this._recordCollectionMock
            .Setup(r => r.UpsertAsync(It.IsAny<IEnumerable<TextSearchStore<string>.TextRagStorageDocument<string>>>(), It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        using var store = new TextSearchStore<string>(this._vectorStoreMock.Object, "testCollection", 128);

        // Act
        await store.UpsertTextAsync(["Sample text"]);

        // Assert
        this._recordCollectionMock.Verify(r => r.EnsureCollectionExistsAsync(It.IsAny<CancellationToken>()), Times.Once);
        this._recordCollectionMock.Verify(r => r.UpsertAsync(
            It.Is<IEnumerable<TextSearchStore<string>.TextRagStorageDocument<string>>>(doc =>
                doc.Count() == 1 &&
                doc.First().Text == "Sample text" &&
                doc.First().Namespaces.Count == 0 &&
                doc.First().SourceId == null &&
                doc.First().SourceLink == null &&
                doc.First().SourceName == null &&
                doc.First().TextEmbedding == "Sample text"),
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
            .Setup(r => r.SearchAsync("query", 3, It.IsAny<VectorSearchOptions<TextSearchStore<string>.TextRagStorageDocument<string>>>(), It.IsAny<CancellationToken>()))
            .Returns(mockResults.ToAsyncEnumerable());

        using var store = new TextSearchStore<string>(this._vectorStoreMock.Object, "testCollection", 128);

        // Act
        var actualResults = await store.SearchAsync("query");

        // Assert
        var actualResultsList = await actualResults.Results.ToListAsync();
        Assert.Single(actualResultsList);
        Assert.Equal("Sample text", actualResultsList[0]);
    }

    [Fact]
    public async Task SearchAsyncWithHybridReturnsSearchResults()
    {
        // Arrange
        this._recordCollectionMock
            .Setup(r => r.GetService(typeof(IKeywordHybridSearchable<TextSearchStore<string>.TextRagStorageDocument<string>>), null))
            .Returns(this._keywordHybridSearchableMock.Object);

        var mockResults = new List<VectorSearchResult<TextSearchStore<string>.TextRagStorageDocument<string>>>
        {
            new(new TextSearchStore<string>.TextRagStorageDocument<string> { Text = "Sample text" }, 0.9f)
        };

        this._keywordHybridSearchableMock
            .Setup(r => r.HybridSearchAsync(
                "query word1 wordtwo",
                It.Is<ICollection<string>>(x => x.Contains("query") && x.Contains("word") && x.Contains("wordtwo")),
                3,
                It.IsAny<HybridSearchOptions<TextSearchStore<string>.TextRagStorageDocument<string>>>(),
                It.IsAny<CancellationToken>()))
            .Returns(mockResults.ToAsyncEnumerable());

        using var store = new TextSearchStore<string>(this._vectorStoreMock.Object, "testCollection", 128);

        // Act
        var actualResults = await store.SearchAsync("query word1 wordtwo");

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
            .Setup(r => r.SearchAsync("query", 3, It.IsAny<VectorSearchOptions<TextSearchStore<string>.TextRagStorageDocument<string>>>(), It.IsAny<CancellationToken>()))
            .Returns(mockResults.ToAsyncEnumerable());

        using var store = new TextSearchStore<string>(
            this._vectorStoreMock.Object,
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
