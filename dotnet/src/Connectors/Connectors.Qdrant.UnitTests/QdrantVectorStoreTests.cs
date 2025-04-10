// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Moq;
using Qdrant.Client;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.Qdrant.UnitTests;

/// <summary>
/// Contains tests for the <see cref="QdrantVectorStore"/> class.
/// </summary>
public class QdrantVectorStoreTests
{
    private const string TestCollectionName = "testcollection";

    private readonly Mock<MockableQdrantClient> _qdrantClientMock;

    private readonly CancellationToken _testCancellationToken = new(false);

    public QdrantVectorStoreTests()
    {
        this._qdrantClientMock = new Mock<MockableQdrantClient>(MockBehavior.Strict);
    }

    [Fact]
    public void GetCollectionReturnsCollection()
    {
        // Arrange.
        var sut = new QdrantVectorStore(this._qdrantClientMock.Object);

        // Act.
        var actual = sut.GetCollection<ulong, SinglePropsModel<ulong>>(TestCollectionName);

        // Assert.
        Assert.NotNull(actual);
        Assert.IsType<QdrantVectorStoreRecordCollection<ulong, SinglePropsModel<ulong>>>(actual);
    }

#pragma warning disable CS0618 // IQdrantVectorStoreRecordCollectionFactory is obsolete
    [Fact]
    public void GetCollectionCallsFactoryIfProvided()
    {
        // Arrange.
        var factoryMock = new Mock<IQdrantVectorStoreRecordCollectionFactory>(MockBehavior.Strict);
        var collectionMock = new Mock<IVectorStoreRecordCollection<ulong, SinglePropsModel<ulong>>>(MockBehavior.Strict);
        factoryMock
            .Setup(x => x.CreateVectorStoreRecordCollection<ulong, SinglePropsModel<ulong>>(It.IsAny<QdrantClient>(), TestCollectionName, null))
            .Returns(collectionMock.Object);
        var sut = new QdrantVectorStore(this._qdrantClientMock.Object, new() { VectorStoreCollectionFactory = factoryMock.Object });

        // Act.
        var actual = sut.GetCollection<ulong, SinglePropsModel<ulong>>(TestCollectionName);

        // Assert.
        Assert.Equal(collectionMock.Object, actual);
        factoryMock.Verify(x => x.CreateVectorStoreRecordCollection<ulong, SinglePropsModel<ulong>>(It.IsAny<QdrantClient>(), TestCollectionName, null), Times.Once);
    }
#pragma warning restore CS0618

    [Fact]
    public void GetCollectionThrowsForInvalidKeyType()
    {
        // Arrange.
        var sut = new QdrantVectorStore(this._qdrantClientMock.Object);

        // Act & Assert.
        Assert.Throws<NotSupportedException>(() => sut.GetCollection<string, SinglePropsModel<string>>(TestCollectionName));
    }

    [Fact]
    public async Task ListCollectionNamesCallsSDKAsync()
    {
        // Arrange.
        this._qdrantClientMock
            .Setup(x => x.ListCollectionsAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(new[] { "collection1", "collection2" });
        var sut = new QdrantVectorStore(this._qdrantClientMock.Object);

        // Act.
        var collectionNames = sut.ListCollectionNamesAsync(this._testCancellationToken);

        // Assert.
        var collectionNamesList = await collectionNames.ToListAsync();
        Assert.Equal(new[] { "collection1", "collection2" }, collectionNamesList);
    }

    public sealed class SinglePropsModel<TKey>
    {
        [VectorStoreRecordKey]
        public required TKey Key { get; set; }

        [VectorStoreRecordData]
        public string Data { get; set; } = string.Empty;

        [VectorStoreRecordVector(4)]
        public ReadOnlyMemory<float>? Vector { get; set; }

        public string? NotAnnotated { get; set; }
    }
}
