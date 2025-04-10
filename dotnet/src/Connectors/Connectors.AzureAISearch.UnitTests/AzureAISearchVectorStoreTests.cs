// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Azure.Search.Documents;
using Azure.Search.Documents.Indexes;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.AzureAISearch.UnitTests;

/// <summary>
/// Contains tests for the <see cref="AzureAISearchVectorStore"/> class.
/// </summary>
public class AzureAISearchVectorStoreTests
{
    private const string TestCollectionName = "testcollection";

    private readonly Mock<SearchIndexClient> _searchIndexClientMock;
    private readonly Mock<SearchClient> _searchClientMock;

    private readonly CancellationToken _testCancellationToken = new(false);

    public AzureAISearchVectorStoreTests()
    {
        this._searchClientMock = new Mock<SearchClient>(MockBehavior.Strict);
        this._searchIndexClientMock = new Mock<SearchIndexClient>(MockBehavior.Strict);
        this._searchIndexClientMock.Setup(x => x.GetSearchClient(TestCollectionName)).Returns(this._searchClientMock.Object);
        this._searchIndexClientMock.Setup(x => x.ServiceName).Returns("TestService");
    }

    [Fact]
    public void GetCollectionReturnsCollection()
    {
        // Arrange.
        var sut = new AzureAISearchVectorStore(this._searchIndexClientMock.Object);

        // Act.
        var actual = sut.GetCollection<string, SinglePropsModel>(TestCollectionName);

        // Assert.
        Assert.NotNull(actual);
        Assert.IsType<AzureAISearchVectorStoreRecordCollection<string, SinglePropsModel>>(actual);
    }

#pragma warning disable CS0618 // IAzureAISearchVectorStoreRecordCollectionFactory is obsolete
    [Fact]
    public void GetCollectionCallsFactoryIfProvided()
    {
        // Arrange.
        var factoryMock = new Mock<IAzureAISearchVectorStoreRecordCollectionFactory>(MockBehavior.Strict);
        var collectionMock = new Mock<IVectorStoreRecordCollection<string, SinglePropsModel>>(MockBehavior.Strict);
        factoryMock
            .Setup(x => x.CreateVectorStoreRecordCollection<string, SinglePropsModel>(this._searchIndexClientMock.Object, TestCollectionName, null))
            .Returns(collectionMock.Object);
        var sut = new AzureAISearchVectorStore(this._searchIndexClientMock.Object, new() { VectorStoreCollectionFactory = factoryMock.Object });

        // Act.
        var actual = sut.GetCollection<string, SinglePropsModel>(TestCollectionName);

        // Assert.
        Assert.Equal(collectionMock.Object, actual);
    }
#pragma warning restore CS0618 // Type or member is obsolete

    [Fact]
    public void GetCollectionThrowsForInvalidKeyType()
    {
        // Arrange.
        var sut = new AzureAISearchVectorStore(this._searchIndexClientMock.Object);

        // Act & Assert.
        Assert.Throws<NotSupportedException>(() => sut.GetCollection<int, SinglePropsModel>(TestCollectionName));
    }

    [Fact]
    public async Task ListCollectionNamesCallsSDKAsync()
    {
        // Arrange async enumerator mock.
        var iterationCounter = 0;
        var asyncEnumeratorMock = new Mock<IAsyncEnumerator<string>>(MockBehavior.Strict);
        asyncEnumeratorMock.Setup(x => x.MoveNextAsync()).Returns(() => ValueTask.FromResult(iterationCounter++ <= 4));
        asyncEnumeratorMock.Setup(x => x.Current).Returns(() => $"testcollection{iterationCounter}");

        // Arrange pageable mock.
        var pageableMock = new Mock<AsyncPageable<string>>(MockBehavior.Strict);
        pageableMock.Setup(x => x.GetAsyncEnumerator(this._testCancellationToken)).Returns(asyncEnumeratorMock.Object);

        // Arrange search index client mock and sut.
        this._searchIndexClientMock
            .Setup(x => x.GetIndexNamesAsync(this._testCancellationToken))
            .Returns(pageableMock.Object);
        var sut = new AzureAISearchVectorStore(this._searchIndexClientMock.Object);

        // Act.
        var actual = sut.ListCollectionNamesAsync(this._testCancellationToken);

        // Assert.
        Assert.NotNull(actual);
        var actualList = await actual.ToListAsync();
        Assert.Equal(5, actualList.Count);
        Assert.All(actualList, (value, index) => Assert.Equal($"testcollection{index + 1}", value));
    }

    public sealed class SinglePropsModel
    {
        [VectorStoreRecordKey]
        public string Key { get; set; } = string.Empty;

        [VectorStoreRecordData]
        public string Data { get; set; } = string.Empty;

        [VectorStoreRecordVector(4)]
        public ReadOnlyMemory<float>? Vector { get; set; }

        public string? NotAnnotated { get; set; }
    }
}
