// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Postgres;
using Moq;
using Npgsql;
using Xunit;

namespace SemanticKernel.Connectors.Postgres.UnitTests;

/// <summary>
/// Contains tests for the <see cref="PostgresVectorStore"/> class.
/// </summary>
public class PostgresVectorStoreTests
{
    private const string TestCollectionName = "testcollection";

    private readonly Mock<IPostgresVectorStoreDbClient> _postgresClientMock;
    private readonly CancellationToken _testCancellationToken = new(false);

    public PostgresVectorStoreTests()
    {
        this._postgresClientMock = new Mock<IPostgresVectorStoreDbClient>(MockBehavior.Strict);
        this._postgresClientMock.Setup(l => l.DatabaseName).Returns("TestDatabase");
    }

    [Fact]
    public void GetCollectionReturnsCollection()
    {
        // Arrange.
        var sut = new PostgresVectorStore(this._postgresClientMock.Object);

        // Act.
        var actual = sut.GetCollection<long, SinglePropsModel<long>>(TestCollectionName);

        // Assert.
        Assert.NotNull(actual);
        Assert.IsType<PostgresVectorStoreRecordCollection<long, SinglePropsModel<long>>>(actual);
    }

    [Fact]
    public void GetCollectionThrowsForInvalidKeyType()
    {
        // Arrange.
        var sut = new PostgresVectorStore(this._postgresClientMock.Object);

        // Act and Assert.
        Assert.Throws<NotSupportedException>(() => sut.GetCollection<ulong, SinglePropsModel<ulong>>(TestCollectionName));
    }

#pragma warning disable CS0618 // IPostgresVectorStoreRecordCollectionFactory is obsolete
    [Fact]
    public void GetCollectionCallsFactoryIfProvided()
    {
        // Arrange.
        var factoryMock = new Mock<IPostgresVectorStoreRecordCollectionFactory>(MockBehavior.Strict);
        var collectionMock = new Mock<IVectorStoreRecordCollection<int, SinglePropsModel<int>>>(MockBehavior.Strict);
        var clientMock = new Mock<IPostgresVectorStoreDbClient>(MockBehavior.Strict);

        clientMock.Setup(x => x.DataSource).Returns<NpgsqlDataSource>(null);
        clientMock.Setup(x => x.DatabaseName).Returns("TestDatabase");

        factoryMock
            .Setup(x => x.CreateVectorStoreRecordCollection<int, SinglePropsModel<int>>(It.IsAny<NpgsqlDataSource>(), TestCollectionName, null))
            .Returns(collectionMock.Object);
        var sut = new PostgresVectorStore(clientMock.Object, new() { VectorStoreCollectionFactory = factoryMock.Object });

        // Act.
        var actual = sut.GetCollection<int, SinglePropsModel<int>>(TestCollectionName);

        // Assert.
        Assert.Equal(collectionMock.Object, actual);
    }
#pragma warning restore CS0618

    [Fact]
    public async Task ListCollectionNamesCallsSDKAsync()
    {
        // Arrange
        var expectedCollections = new List<string> { "fake-collection-1", "fake-collection-2", "fake-collection-3" };

        this._postgresClientMock
            .Setup(client => client.GetTablesAsync(CancellationToken.None))
            .Returns(expectedCollections.ToAsyncEnumerable());

        var sut = new PostgresVectorStore(this._postgresClientMock.Object);

        // Act.
        var actual = sut.ListCollectionNamesAsync(this._testCancellationToken);

        // Assert
        Assert.NotNull(actual);
        var actualList = await actual.ToListAsync();
        Assert.Equal(expectedCollections, actualList);
    }

    [Fact]
    public async Task ListCollectionNamesThrowsCorrectExceptionAsync()
    {
        // Arrange
        var expectedCollections = new List<string> { "fake-collection-1", "fake-collection-2", "fake-collection-3" };

        this._postgresClientMock
            .Setup(client => client.GetTablesAsync(CancellationToken.None))
            .Returns(this.ThrowingAsyncEnumerableAsync);

        var sut = new PostgresVectorStore(this._postgresClientMock.Object);

        // Act.
        var actual = sut.ListCollectionNamesAsync(this._testCancellationToken);

        // Assert
        Assert.NotNull(actual);
        await Assert.ThrowsAsync<VectorStoreOperationException>(async () => await actual.ToListAsync());
    }

    private async IAsyncEnumerable<string> ThrowingAsyncEnumerableAsync()
    {
        int itemIndex = 0;
        await foreach (var item in new List<string> { "item1", "item2", "item3" }.ToAsyncEnumerable())
        {
            if (itemIndex == 1)
            {
                throw new InvalidOperationException("Test exception");
            }
            yield return item;
            itemIndex++;
        }
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
