// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Moq;
using StackExchange.Redis;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.Redis.UnitTests;

/// <summary>
/// Contains tests for the <see cref="RedisVectorStore"/> class.
/// </summary>
public class RedisVectorStoreTests
{
    private const string TestCollectionName = "testcollection";

    private readonly Mock<IDatabase> _redisDatabaseMock;

    public RedisVectorStoreTests()
    {
        this._redisDatabaseMock = new Mock<IDatabase>(MockBehavior.Strict);
        this._redisDatabaseMock.Setup(l => l.Database).Returns(0);

        var batchMock = new Mock<IBatch>();
        this._redisDatabaseMock.Setup(x => x.CreateBatch(It.IsAny<object>())).Returns(batchMock.Object);
    }

    [Fact]
    public void GetCollectionReturnsJsonCollection()
    {
        // Arrange.
        var sut = new RedisVectorStore(this._redisDatabaseMock.Object);

        // Act.
        var actual = sut.GetCollection<string, SinglePropsModel<string>>(TestCollectionName);

        // Assert.
        Assert.NotNull(actual);
        Assert.IsType<RedisJsonVectorStoreRecordCollection<string, SinglePropsModel<string>>>(actual);
    }

    [Fact]
    public void GetCollectionReturnsHashSetCollection()
    {
        // Arrange.
        var sut = new RedisVectorStore(this._redisDatabaseMock.Object, new() { StorageType = RedisStorageType.HashSet });

        // Act.
        var actual = sut.GetCollection<string, SinglePropsModel<string>>(TestCollectionName);

        // Assert.
        Assert.NotNull(actual);
        Assert.IsType<RedisHashSetVectorStoreRecordCollection<string, SinglePropsModel<string>>>(actual);
    }

#pragma warning disable CS0618 // IRedisVectorStoreRecordCollectionFactory is obsolete
    [Fact]
    public void GetCollectionCallsFactoryIfProvided()
    {
        // Arrange.
        var factoryMock = new Mock<IRedisVectorStoreRecordCollectionFactory>(MockBehavior.Strict);
        var collectionMock = new Mock<IVectorStoreRecordCollection<string, SinglePropsModel<string>>>(MockBehavior.Strict);
        factoryMock
            .Setup(x => x.CreateVectorStoreRecordCollection<string, SinglePropsModel<string>>(It.IsAny<IDatabase>(), TestCollectionName, null))
            .Returns(collectionMock.Object);
        var sut = new RedisVectorStore(this._redisDatabaseMock.Object, new() { VectorStoreCollectionFactory = factoryMock.Object });

        // Act.
        var actual = sut.GetCollection<string, SinglePropsModel<string>>(TestCollectionName);

        // Assert.
        Assert.Equal(collectionMock.Object, actual);
        factoryMock.Verify(x => x.CreateVectorStoreRecordCollection<string, SinglePropsModel<string>>(It.IsAny<IDatabase>(), TestCollectionName, null), Times.Once);
    }
#pragma warning restore CS0618

    [Fact]
    public void GetCollectionThrowsForInvalidKeyType()
    {
        // Arrange.
        var sut = new RedisVectorStore(this._redisDatabaseMock.Object);

        // Act & Assert.
        Assert.Throws<NotSupportedException>(() => sut.GetCollection<int, SinglePropsModel<int>>(TestCollectionName));
    }

    [Fact]
    public async Task ListCollectionNamesCallsSDKAsync()
    {
        // Arrange.
        var redisResultStrings = new string[] { "collection1", "collection2" };
        var results = redisResultStrings
            .Select(x => RedisResult.Create(new RedisValue(x)))
            .ToArray();
        this._redisDatabaseMock
            .Setup(
                x => x.ExecuteAsync(
                    It.IsAny<string>(),
                It.IsAny<object[]>()))
            .ReturnsAsync(RedisResult.Create(results));
        var sut = new RedisVectorStore(this._redisDatabaseMock.Object);

        // Act.
        var collectionNames = sut.ListCollectionNamesAsync();

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
