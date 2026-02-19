// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Moq;
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
        using var sut = new QdrantVectorStore(this._qdrantClientMock.Object);

        // Act.
        var actual = sut.GetCollection<ulong, SinglePropsModel<ulong>>(TestCollectionName);

        // Assert.
        Assert.NotNull(actual);
        Assert.IsType<QdrantCollection<ulong, SinglePropsModel<ulong>>>(actual);
    }

    [Fact]
    public void GetCollectionThrowsForInvalidKeyType()
    {
        // Arrange.
        using var sut = new QdrantVectorStore(this._qdrantClientMock.Object);

        // Act & Assert.
        Assert.Throws<NotSupportedException>(() => sut.GetCollection<string, SinglePropsModel<string>>(TestCollectionName));
    }

    [Fact]
    public void QdrantModelBuilderExposesKeyTypeValidationCompatibilityMethod()
    {
        // Arrange.
        var method = typeof(QdrantModelBuilder).GetMethod(
            "IsKeyPropertyTypeValid",
            BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.DeclaredOnly);
        var sut = new QdrantModelBuilder(hasNamedVectors: false);
        var validArgs = new object?[] { typeof(ulong), null };
        var invalidArgs = new object?[] { typeof(string), null };

        // Act.
        var validResult = (bool?)method?.Invoke(sut, validArgs);
        var invalidResult = (bool?)method?.Invoke(sut, invalidArgs);

        // Assert.
        Assert.NotNull(method);
        Assert.True(validResult);
        Assert.Null(validArgs[1]);
        Assert.False(invalidResult);
        Assert.Equal("ulong, Guid", invalidArgs[1]);
    }

    [Fact]
    public async Task ListCollectionNamesCallsSDKAsync()
    {
        // Arrange.
        this._qdrantClientMock
            .Setup(x => x.ListCollectionsAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(new[] { "collection1", "collection2" });
        using var sut = new QdrantVectorStore(this._qdrantClientMock.Object);

        // Act.
        var collectionNames = sut.ListCollectionNamesAsync(this._testCancellationToken);

        // Assert.
        var collectionNamesList = await collectionNames.ToListAsync();
        Assert.Equal(new[] { "collection1", "collection2" }, collectionNamesList);
    }

    public sealed class SinglePropsModel<TKey>
    {
        [VectorStoreKey]
        public required TKey Key { get; set; }

        [VectorStoreData]
        public string Data { get; set; } = string.Empty;

        [VectorStoreVector(4)]
        public ReadOnlyMemory<float>? Vector { get; set; }

        public string? NotAnnotated { get; set; }
    }
}
