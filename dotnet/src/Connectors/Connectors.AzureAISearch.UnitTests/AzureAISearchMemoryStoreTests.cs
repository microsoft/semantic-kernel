// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Azure.Search.Documents;
using Azure.Search.Documents.Indexes;
using Azure.Search.Documents.Indexes.Models;
using Azure.Search.Documents.Models;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Microsoft.SemanticKernel.Memory;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.Memory.AzureAISearch;

/// <summary>
/// Unit tests for <see cref="AzureAISearchMemoryStore"/> class.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted")]
public sealed class AzureAISearchMemoryStoreTests
{
    private readonly Mock<SearchIndexClient> _mockSearchIndexClient = new();
    private readonly Mock<SearchClient> _mockSearchClient = new();

    private readonly AzureAISearchMemoryStore _service;

    public AzureAISearchMemoryStoreTests()
    {
        this._mockSearchIndexClient
            .Setup(x => x.GetSearchClient(It.IsAny<string>()))
            .Returns(this._mockSearchClient.Object);

        this._service = new AzureAISearchMemoryStore(this._mockSearchIndexClient.Object);
    }

    [Fact]
    public async Task GetCollectionsReturnsIndexNamesAsync()
    {
        // Arrange
        Page<SearchIndex> page = Page<SearchIndex>.FromValues(
        [
            new SearchIndex("index-1"),
            new SearchIndex("index-2"),
        ], null, Mock.Of<Response>());

        var pageable = AsyncPageable<SearchIndex>.FromPages([page]);

        this._mockSearchIndexClient
            .Setup(x => x.GetIndexesAsync(It.IsAny<CancellationToken>()))
            .Returns(pageable);

        // Act
        var indexes = new List<string>();

        await foreach (var index in this._service.GetCollectionsAsync())
        {
            indexes.Add(index);
        }

        // Assert
        Assert.Equal("index-1", indexes[0]);
        Assert.Equal("index-2", indexes[1]);
    }

    [Fact]
    public async Task GetCollectionsOnErrorThrowsHttpOperationExceptionAsync()
    {
        // Arrange
        this._mockSearchIndexClient
            .Setup(x => x.GetIndexesAsync(It.IsAny<CancellationToken>()))
            .Throws(new RequestFailedException((int)HttpStatusCode.InternalServerError, "test error response"));

        // Act & Assert
        var indexes = new List<string>();

        var exception = await Assert.ThrowsAsync<HttpOperationException>(async () =>
        {
            await foreach (var index in this._service.GetCollectionsAsync())
            {
            }
        });

        Assert.Equal("test error response", exception.Message);
        Assert.Equal(HttpStatusCode.InternalServerError, exception.StatusCode);
    }

    [Theory]
    [InlineData("index-1", true)]
    [InlineData("index-2", true)]
    [InlineData("index-3", false)]
    public async Task DoesCollectionExistReturnsValidResultAsync(string collectionName, bool expectedResult)
    {
        // Arrange
        Page<SearchIndex> page = Page<SearchIndex>.FromValues(
        [
            new SearchIndex("index-1"),
            new SearchIndex("index-2"),
        ], null, Mock.Of<Response>());

        var pageable = AsyncPageable<SearchIndex>.FromPages([page]);

        this._mockSearchIndexClient
            .Setup(x => x.GetIndexesAsync(It.IsAny<CancellationToken>()))
            .Returns(pageable);

        // Act
        var result = await this._service.DoesCollectionExistAsync(collectionName);

        // Assert
        Assert.Equal(expectedResult, result);
    }

    [Fact]
    public async Task DoesCollectionExistOnErrorThrowsHttpOperationExceptionAsync()
    {
        // Arrange
        this._mockSearchIndexClient
            .Setup(x => x.GetIndexesAsync(It.IsAny<CancellationToken>()))
            .Throws(new RequestFailedException((int)HttpStatusCode.InternalServerError, "test error response"));

        // Act
        var exception = await Assert.ThrowsAsync<HttpOperationException>(() => this._service.DoesCollectionExistAsync("test-index"));

        // Assert
        Assert.Equal("test error response", exception.Message);
        Assert.Equal(HttpStatusCode.InternalServerError, exception.StatusCode);
    }

    [Fact]
    public async Task DeleteCollectionCallsDeleteIndexMethodAsync()
    {
        // Arrange
        this._mockSearchIndexClient
            .Setup(x => x.DeleteIndexAsync(It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(It.IsAny<Response>());

        // Act
        await this._service.DeleteCollectionAsync("test-index");

        // Assert
        this._mockSearchIndexClient.Verify(x => x.DeleteIndexAsync("test-index", It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task DeleteCollectionOnErrorThrowsHttpOperationExceptionAsync()
    {
        // Arrange
        this._mockSearchIndexClient
            .Setup(x => x.DeleteIndexAsync(It.IsAny<string>(), It.IsAny<CancellationToken>()))
            .Throws(new RequestFailedException((int)HttpStatusCode.InternalServerError, "test error response"));

        // Act
        var exception = await Assert.ThrowsAsync<HttpOperationException>(() => this._service.DeleteCollectionAsync("test-index"));

        // Assert
        Assert.Equal("test error response", exception.Message);
        Assert.Equal(HttpStatusCode.InternalServerError, exception.StatusCode);
    }

    [Fact]
    public async Task UpsertReturnsValidRecordKeyAsync()
    {
        // Arrange
        var indexingResult = SearchModelFactory.IndexingResult("record-id", null, true, 200);
        var results = SearchModelFactory.IndexDocumentsResult([indexingResult]);

        this._mockSearchClient
            .Setup(x => x.IndexDocumentsAsync<AzureAISearchMemoryRecord>(
                It.IsAny<IndexDocumentsBatch<AzureAISearchMemoryRecord>>(),
                It.IsAny<IndexDocumentsOptions>(),
                It.IsAny<CancellationToken>()))
            .ReturnsAsync(Response.FromValue(results, Mock.Of<Response>()));

        // Act
        var result = await this._service.UpsertAsync("test-index", this.GetTestMemoryRecord("record-id"));

        // Assert
        Assert.Equal("record-id", result);
    }

    [Fact]
    public async Task UpsertOnInternalServerErrorThrowsHttpOperationExceptionAsync()
    {
        // Arrange
        this._mockSearchClient
            .Setup(x => x.IndexDocumentsAsync<AzureAISearchMemoryRecord>(
                It.IsAny<IndexDocumentsBatch<AzureAISearchMemoryRecord>>(),
                It.IsAny<IndexDocumentsOptions>(),
                It.IsAny<CancellationToken>()))
            .Throws(new RequestFailedException((int)HttpStatusCode.InternalServerError, "test error response"));

        // Act
        var exception = await Assert.ThrowsAsync<HttpOperationException>(() => this._service.UpsertAsync("test-index", this.GetTestMemoryRecord("record-id")));

        // Assert
        Assert.Equal("test error response", exception.Message);
        Assert.Equal(HttpStatusCode.InternalServerError, exception.StatusCode);
    }

    [Fact]
    public async Task UpsertOnNotFoundErrorCreatesIndexAsync()
    {
        // Arrange
        var indexingResult = SearchModelFactory.IndexingResult("record-id", null, true, 200);
        var results = SearchModelFactory.IndexDocumentsResult([indexingResult]);

        this._mockSearchClient
            .SetupSequence(x => x.IndexDocumentsAsync<AzureAISearchMemoryRecord>(
                It.IsAny<IndexDocumentsBatch<AzureAISearchMemoryRecord>>(),
                It.IsAny<IndexDocumentsOptions>(),
                It.IsAny<CancellationToken>()))
            .Throws(new RequestFailedException((int)HttpStatusCode.NotFound, "not found"))
            .ReturnsAsync(Response.FromValue(results, Mock.Of<Response>()));

        this._mockSearchIndexClient
            .Setup(x => x.CreateIndexAsync(It.IsAny<SearchIndex>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(Response.FromValue(new SearchIndex("test-index"), Mock.Of<Response>()));

        // Act
        var result = await this._service.UpsertAsync("test-index", this.GetTestMemoryRecord("record-id"));

        // Assert
        Assert.Equal("record-id", result);
        this._mockSearchIndexClient
            .Verify(x => x.CreateIndexAsync(It.IsAny<SearchIndex>(), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task GetReturnsValidRecordAsync()
    {
        // Arrange
        this._mockSearchClient
            .Setup(x => x.GetDocumentAsync<AzureAISearchMemoryRecord>(It.IsAny<string>(), It.IsAny<GetDocumentOptions>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(Response.FromValue(new AzureAISearchMemoryRecord("record-id"), Mock.Of<Response>()));

        // Act
        var result = await this._service.GetAsync("test-index", "record-id");

        // Assert
        Assert.NotNull(result);
        Assert.Equal(AzureAISearchMemoryRecord.EncodeId("record-id"), result.Key);
    }

    [Fact]
    public async Task GetReturnsNullWhenRecordDoesNotExistAsync()
    {
        // Arrange
        this._mockSearchClient
            .Setup(x => x.GetDocumentAsync<AzureAISearchMemoryRecord>(It.IsAny<string>(), It.IsAny<GetDocumentOptions>(), It.IsAny<CancellationToken>()))
            .ThrowsAsync(new RequestFailedException((int)HttpStatusCode.NotFound, "test error response"));

        // Act
        var result = await this._service.GetAsync("test-collection", "test-record");

        // Assert
        Assert.Null(result);
    }

    [Fact]
    public async Task GetNearestMatchesReturnsValidRecordAsync()
    {
        // Arrange
        var searchMemoryRecord = new AzureAISearchMemoryRecord("record-id");
        var searchResult = SearchModelFactory.SearchResult<AzureAISearchMemoryRecord>(searchMemoryRecord, 0.8, null);
        var results = SearchModelFactory.SearchResults<AzureAISearchMemoryRecord>([searchResult], 1, null, 0.9, Mock.Of<Response>());

        this._mockSearchClient
            .Setup(x => x.SearchAsync<AzureAISearchMemoryRecord>(It.IsAny<string>(), It.IsAny<SearchOptions>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(Response.FromValue(results, Mock.Of<Response>()));

        ReadOnlyMemory<float> embedding = new[] { 1f, 3f, 5f };

        // Act
        var recordKeys = new List<string>();

        await foreach (var (record, score) in this._service.GetNearestMatchesAsync("test-index", embedding, 1))
        {
            recordKeys.Add(record.Key);
        }

        // Assert
        Assert.Equal(AzureAISearchMemoryRecord.EncodeId("record-id"), recordKeys[0]);
    }

    [Fact]
    public async Task GetNearestMatchesOnInternalServerErrorThrowsHttpOperationExceptionAsync()
    {
        // Arrange
        this._mockSearchClient
            .Setup(x => x.SearchAsync<AzureAISearchMemoryRecord>(It.IsAny<string>(), It.IsAny<SearchOptions>(), It.IsAny<CancellationToken>()))
            .Throws(new RequestFailedException((int)HttpStatusCode.InternalServerError, "test error response"));

        ReadOnlyMemory<float> embedding = new[] { 1f, 3f, 5f };

        // Act
        var exception = await Assert.ThrowsAsync<HttpOperationException>(async () =>
        {
            await foreach (var (record, score) in this._service.GetNearestMatchesAsync("test-index", embedding, 1))
            {
            }
        });

        // Assert
        Assert.Equal("test error response", exception.Message);
        Assert.Equal(HttpStatusCode.InternalServerError, exception.StatusCode);
    }

    [Fact]
    public async Task GetNearestMatchesOnNotFoundErrorReturnsEmptyAsync()
    {
        // Arrange
        this._mockSearchClient
            .Setup(x => x.SearchAsync<AzureAISearchMemoryRecord>(It.IsAny<string>(), It.IsAny<SearchOptions>(), It.IsAny<CancellationToken>()))
            .Throws(new RequestFailedException((int)HttpStatusCode.NotFound, "not found"));

        ReadOnlyMemory<float> embedding = new[] { 1f, 3f, 5f };

        // Act
        var recordKeys = new List<string>();

        await foreach (var (record, score) in this._service.GetNearestMatchesAsync("test-index", embedding, 1))
        {
            recordKeys.Add(record.Key);
        }

        // Assert
        Assert.Empty(recordKeys);
    }

    [Fact]
    public async Task RemoveBatchCallsDeleteDocumentsMethodAsync()
    {
        // Arrange
        var indexingResult = SearchModelFactory.IndexingResult("record-id", null, true, 200);
        var results = SearchModelFactory.IndexDocumentsResult([indexingResult]);

        this._mockSearchClient
            .Setup(x => x.DeleteDocumentsAsync<AzureAISearchMemoryRecord>(
                It.IsAny<IEnumerable<AzureAISearchMemoryRecord>>(),
                It.IsAny<IndexDocumentsOptions>(),
                It.IsAny<CancellationToken>()))
            .ReturnsAsync(Response.FromValue(results, Mock.Of<Response>()));

        // Act
        var exception = await Record.ExceptionAsync(() => this._service.RemoveBatchAsync("text-index", ["record-id"]));

        // Assert
        Assert.Null(exception);

        this._mockSearchClient
            .Verify(x => x.DeleteDocumentsAsync<AzureAISearchMemoryRecord>(
                It.IsAny<IEnumerable<AzureAISearchMemoryRecord>>(),
                It.IsAny<IndexDocumentsOptions>(),
                It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task RemoveBatchOnNotFoundErrorDoesNotThrowExceptionAsync()
    {
        // Arrange
        this._mockSearchClient
            .Setup(x => x.DeleteDocumentsAsync<AzureAISearchMemoryRecord>(
                It.IsAny<IEnumerable<AzureAISearchMemoryRecord>>(),
                It.IsAny<IndexDocumentsOptions>(),
                It.IsAny<CancellationToken>()))
            .Throws(new RequestFailedException((int)HttpStatusCode.NotFound, "not found"));

        // Act
        var exception = await Record.ExceptionAsync(() => this._service.RemoveBatchAsync("text-index", ["record-id"]));

        // Assert
        Assert.Null(exception);

        this._mockSearchClient
            .Verify(x => x.DeleteDocumentsAsync<AzureAISearchMemoryRecord>(
                It.IsAny<IEnumerable<AzureAISearchMemoryRecord>>(),
                It.IsAny<IndexDocumentsOptions>(),
                It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task RemoveBatchOnInternalServerErrorThrowsHttpOperationExceptionAsync()
    {
        // Arrange
        this._mockSearchClient
            .Setup(x => x.DeleteDocumentsAsync<AzureAISearchMemoryRecord>(
                It.IsAny<IEnumerable<AzureAISearchMemoryRecord>>(),
                It.IsAny<IndexDocumentsOptions>(),
                It.IsAny<CancellationToken>()))
            .Throws(new RequestFailedException((int)HttpStatusCode.InternalServerError, "test error response"));

        // Act
        var exception = await Assert.ThrowsAsync<HttpOperationException>(() => this._service.RemoveBatchAsync("text-index", ["record-id"]));

        // Assert
        Assert.Equal("test error response", exception.Message);
        Assert.Equal(HttpStatusCode.InternalServerError, exception.StatusCode);

        this._mockSearchClient
            .Verify(x => x.DeleteDocumentsAsync<AzureAISearchMemoryRecord>(
                It.IsAny<IEnumerable<AzureAISearchMemoryRecord>>(),
                It.IsAny<IndexDocumentsOptions>(),
                It.IsAny<CancellationToken>()), Times.Once());
    }

    #region private

    private MemoryRecord GetTestMemoryRecord(string id)
    {
        ReadOnlyMemory<float> embedding = new[] { 1f, 3f, 5f };
        return MemoryRecord.LocalRecord(id, "text", "description", embedding);
    }

    #endregion
}
