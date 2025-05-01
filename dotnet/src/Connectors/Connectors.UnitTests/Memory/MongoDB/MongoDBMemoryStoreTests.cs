// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.MongoDB;
using Microsoft.SemanticKernel.Memory;
using MongoDB.Driver;
using MongoDB.Driver.Core.Clusters;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.MongoDB;

/// <summary>
/// Unit tests for <see cref="MongoDBMemoryStore"/> class.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted")]
public class MongoDBMemoryStoreTests
{
    private const string CollectionName = "test-collection";
    private const string DatabaseName = "test-database";

    private readonly Mock<IMongoClient> _mongoClientMock;
    private readonly Mock<ICluster> _mongoClusterMock;
    private readonly Mock<IMongoCollection<MongoDBMemoryEntry>> _mongoCollectionMock;
    private readonly Mock<IMongoDatabase> _mongoDatabaseMock;

    public MongoDBMemoryStoreTests()
    {
        this._mongoClientMock = new Mock<IMongoClient>();
        this._mongoDatabaseMock = new Mock<IMongoDatabase>();
        this._mongoCollectionMock = new Mock<IMongoCollection<MongoDBMemoryEntry>>();
        this._mongoClusterMock = new Mock<ICluster>();

        this._mongoClientMock
            .Setup(client => client.GetDatabase(DatabaseName, null))
            .Returns(this._mongoDatabaseMock.Object);
        this._mongoClientMock
            .Setup(client => client.Cluster)
            .Returns(this._mongoClusterMock.Object);
        this._mongoDatabaseMock
            .Setup(client => client.GetCollection<MongoDBMemoryEntry>(CollectionName, null))
            .Returns(this._mongoCollectionMock.Object);
    }

    [Fact]
    public async Task ItCanCreateCollectionAsync()
    {
        // Arrange
        using var memoryStore = new MongoDBMemoryStore(this._mongoClientMock.Object, DatabaseName);

        // Act
        await memoryStore.CreateCollectionAsync(CollectionName);

        // Assert
        this._mongoDatabaseMock.Verify(d => d.CreateCollectionAsync(CollectionName, default, default), Times.Once());
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanCheckWhetherCollectionExistsAsync(bool collectionExists)
    {
        // Arrange
        using var memoryStore = new MongoDBMemoryStore(this._mongoClientMock.Object, DatabaseName);
        using var cursorMock = collectionExists ? new AsyncCursorMock<string>(CollectionName) : new AsyncCursorMock<string>();
        this._mongoDatabaseMock
            .Setup(client => client.ListCollectionNamesAsync(default, default))
            .ReturnsAsync(cursorMock);

        // Act
        var actualCollectionExists = await memoryStore.DoesCollectionExistAsync(CollectionName);

        // Assert
        Assert.Equal(collectionExists, actualCollectionExists);
        this._mongoDatabaseMock.Verify(client => client.ListCollectionNamesAsync(default, default), Times.Once());
    }

    [Fact]
    public async Task ItCanDeleteCollectionAsync()
    {
        // Arrange
        using var memoryStore = new MongoDBMemoryStore(this._mongoClientMock.Object, DatabaseName);

        // Act
        await memoryStore.DeleteCollectionAsync(CollectionName);

        // Assert
        this._mongoDatabaseMock.Verify(client => client.DropCollectionAsync(CollectionName, default), Times.Once());
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanGetAsync(bool entryExists)
    {
        // Arrange
        using var memoryStore = new MongoDBMemoryStore(this._mongoClientMock.Object, DatabaseName);
        var memoryRecord = CreateRecord("id");

        using var cursorMock = entryExists ?
            new AsyncCursorMock<MongoDBMemoryEntry>(new MongoDBMemoryEntry(memoryRecord)) :
            new AsyncCursorMock<MongoDBMemoryEntry>();

        this._mongoCollectionMock
            .Setup(c => c.FindAsync(
                It.IsAny<FilterDefinition<MongoDBMemoryEntry>>(),
                It.IsAny<FindOptions<MongoDBMemoryEntry>>(),
                default))
            .ReturnsAsync(cursorMock);

        // Act
        var actualMemoryRecord = await memoryStore.GetAsync(CollectionName, memoryRecord.Key, withEmbedding: true);

        // Assert
        if (entryExists)
        {
            Assert.NotNull(actualMemoryRecord);
            AssertMemoryRecordEqual(memoryRecord, actualMemoryRecord);
        }
        else
        {
            Assert.Null(actualMemoryRecord);
        }
    }

    [Fact]
    public async Task ItCanGetBatchAsync()
    {
        // Arrange
        using var memoryStore = new MongoDBMemoryStore(this._mongoClientMock.Object, DatabaseName);
        var (memoryRecords, keys) = CreateRecords(10);

        using var cursorMock = new AsyncCursorMock<MongoDBMemoryEntry>(memoryRecords.Select(r => new MongoDBMemoryEntry(r)).ToArray());

        this._mongoCollectionMock
            .Setup(c => c.FindAsync(
                It.IsAny<FilterDefinition<MongoDBMemoryEntry>>(),
                It.IsAny<FindOptions<MongoDBMemoryEntry>>(),
                default))
            .ReturnsAsync(cursorMock);

        // Act
        var actualMemoryRecords = await memoryStore.GetBatchAsync(CollectionName, keys, withEmbeddings: true).ToListAsync();

        // Assert
        Assert.Equal(memoryRecords.Length, actualMemoryRecords.Count);

        for (var i = 0; i < memoryRecords.Length; i++)
        {
            AssertMemoryRecordEqual(memoryRecords[i], actualMemoryRecords[i]);
        }
    }

    [Fact]
    public async Task ItCanGetCollectionsAsync()
    {
        // Arrange
        string[] collections = ["collection1", "collection2", "collection3"];
        using var memoryStore = new MongoDBMemoryStore(this._mongoClientMock.Object, DatabaseName);
        using var cursorMock = new AsyncCursorMock<string>(collections);

        this._mongoDatabaseMock
            .Setup(client => client.ListCollectionNamesAsync(default, default))
            .ReturnsAsync(cursorMock);

        // Act
        var actualCollections = await memoryStore.GetCollectionsAsync().ToListAsync();

        // Assert
        Assert.True(collections.SequenceEqual(actualCollections));
    }

    [Theory]
    [InlineData(null)]
    [InlineData("myIndexName")]
    public async Task ItCanGetNearestMatchAsync(string? indexName)
    {
        // Arrange
        var actualIndexName = indexName ?? "default";
        string expectedStage = $"{{ \"$vectorSearch\" : {{ \"queryVector\" : [1.0], \"path\" : \"embedding\", \"limit\" : 1, \"numCandidates\" : 10, \"index\" : \"{actualIndexName}\" }} }}";

        using var memoryStore = new MongoDBMemoryStore(this._mongoClientMock.Object, DatabaseName, indexName);
        var memoryRecord = CreateRecord("id");
        using var cursorMock = new AsyncCursorMock<MongoDBMemoryEntry>(new MongoDBMemoryEntry(memoryRecord));

        // Act
        this._mongoCollectionMock
            .Setup(c => c.AggregateAsync<MongoDBMemoryEntry>(It.IsAny<PipelineDefinition<MongoDBMemoryEntry, MongoDBMemoryEntry>>(), It.IsAny<AggregateOptions>(), default))
            .ReturnsAsync(cursorMock);
        var match = await memoryStore.GetNearestMatchAsync(CollectionName, new[] { 1f });

        // Assert
        AssertMemoryRecordEqual(memoryRecord, match.Value.Item1);
        this._mongoCollectionMock.Verify(a => a.AggregateAsync(It.Is<PipelineDefinition<MongoDBMemoryEntry, MongoDBMemoryEntry>>(p => VerifyPipeline(p, expectedStage)), It.IsAny<AggregateOptions>(), default), Times.Once());
    }

    [Theory]
    [InlineData(null, 50)]
    [InlineData("myIndexName", 100)]
    public async Task ItCanGetNearestMatchesAsync(string? indexName, int limit)
    {
        // Arrange
        var actualIndexName = indexName ?? "default";
        string expectedStage = $"{{ \"$vectorSearch\" : {{ \"queryVector\" : [1.0], \"path\" : \"embedding\", \"limit\" : {limit}, \"numCandidates\" : {limit * 10}, \"index\" : \"{actualIndexName}\" }} }}";

        using var memoryStore = new MongoDBMemoryStore(this._mongoClientMock.Object, DatabaseName, indexName);
        var (memoryRecords, keys) = CreateRecords(10);
        using var cursorMock = new AsyncCursorMock<MongoDBMemoryEntry>(memoryRecords.Select(r => new MongoDBMemoryEntry(r)).ToArray());

        // Act
        this._mongoCollectionMock
            .Setup(c => c.AggregateAsync<MongoDBMemoryEntry>(It.IsAny<PipelineDefinition<MongoDBMemoryEntry, MongoDBMemoryEntry>>(), It.IsAny<AggregateOptions>(), default))
            .ReturnsAsync(cursorMock);
        var matches = await memoryStore.GetNearestMatchesAsync(CollectionName, new(new[] { 1f }), limit).ToListAsync();

        // Assert
        Assert.Equal(memoryRecords.Length, matches.Count);

        for (var i = 0; i < memoryRecords.Length; i++)
        {
            AssertMemoryRecordEqual(memoryRecords[i], matches[i].Item1);
        }

        this._mongoCollectionMock.Verify(a => a.AggregateAsync(It.Is<PipelineDefinition<MongoDBMemoryEntry, MongoDBMemoryEntry>>(p => VerifyPipeline(p, expectedStage)), It.IsAny<AggregateOptions>(), default), Times.Once());
    }

    [Fact]
    public async Task ItCanRemoveAsync()
    {
        // Arrange
        const string Key = "key";
        using var memoryStore = new MongoDBMemoryStore(this._mongoClientMock.Object, DatabaseName);

        // Act
        await memoryStore.RemoveAsync(CollectionName, Key);

        // Assert
        this._mongoCollectionMock.Verify(c => c.DeleteOneAsync(It.IsAny<FilterDefinition<MongoDBMemoryEntry>>(), default), Times.Once());
    }

    [Fact]
    public async Task ItCanRemoveBatchAsync()
    {
        // Arrange
        var keys = new string[] { "key1", "key2", "key3" };
        using var memoryStore = new MongoDBMemoryStore(this._mongoClientMock.Object, DatabaseName);

        // Act
        await memoryStore.RemoveBatchAsync(CollectionName, keys);

        // Assert
        this._mongoCollectionMock.Verify(c => c.DeleteManyAsync(It.IsAny<FilterDefinition<MongoDBMemoryEntry>>(), default), Times.Once());
    }

    [Fact]
    public async Task ItCanUpsertAsync()
    {
        // Arrange
        using var memoryStore = new MongoDBMemoryStore(this._mongoClientMock.Object, DatabaseName);
        var memoryRecord = CreateRecord("id");

        this._mongoCollectionMock
            .Setup(c => c.ReplaceOneAsync(
                It.IsAny<FilterDefinition<MongoDBMemoryEntry>>(),
                It.Is<MongoDBMemoryEntry>(e => e.Id == memoryRecord.Key),
                It.IsAny<ReplaceOptions>(), default))
            .ReturnsAsync(new ReplaceOneResult.Acknowledged(0, 0, memoryRecord.Key));

        // Act
        var actualMemoryRecordKey = await memoryStore.UpsertAsync(CollectionName, memoryRecord);

        // Assert
        Assert.Equal(memoryRecord.Key, actualMemoryRecordKey);

        this._mongoCollectionMock.Verify(c => c.ReplaceOneAsync(
            It.IsAny<FilterDefinition<MongoDBMemoryEntry>>(),
            It.Is<MongoDBMemoryEntry>(e => e.Id == memoryRecord.Key),
            It.IsAny<ReplaceOptions>(),
            default));
    }

    [Fact]
    public async Task ItCanUpsertBatchAsync()
    {
        // Arrange
        using var memoryStore = new MongoDBMemoryStore(this._mongoClientMock.Object, DatabaseName);
        var (memoryRecords, keys) = CreateRecords(10);

        foreach (var key in keys)
        {
            var entryMatch = It.Is<MongoDBMemoryEntry>(e => e.Id == key);
            this._mongoCollectionMock
                .Setup(c => c.ReplaceOneAsync(
                    It.IsAny<FilterDefinition<MongoDBMemoryEntry>>(),
                    It.Is<MongoDBMemoryEntry>(e => e.Id == key),
                    It.IsAny<ReplaceOptions>(),
                    default))
                .ReturnsAsync(new ReplaceOneResult.Acknowledged(0, 0, key));
        }

        // Act
        var actualMemoryRecordKeys = await memoryStore.UpsertBatchAsync(CollectionName, memoryRecords).ToListAsync();

        for (int i = 0; i < memoryRecords.Length; i++)
        {
            Assert.Equal(memoryRecords[i].Key, actualMemoryRecordKeys[i]);

            this._mongoCollectionMock.Verify(c => c.ReplaceOneAsync(
                It.IsAny<FilterDefinition<MongoDBMemoryEntry>>(),
                It.Is<MongoDBMemoryEntry>(e => e.Id == memoryRecords[i].Key),
                It.IsAny<ReplaceOptions>(),
                default));
        }
    }

    [Fact]
    public void ItDisposesClusterOnDispose()
    {
        // Arrange
        var memoryStore = new MongoDBMemoryStore(this._mongoClientMock.Object, DatabaseName);

        // Act
        memoryStore.Dispose();

        // Assert
        this._mongoClusterMock.Verify(c => c.Dispose(), Times.Once());
    }

    #region private ================================================================================

    private sealed class AsyncCursorMock<T>(params T[] items) : IAsyncCursor<T>
    {
        private T[] _items = items ?? [];

        public IEnumerable<T>? Current { get; private set; }

        public void Dispose()
        {
        }

        public bool MoveNext(CancellationToken cancellationToken = default)
        {
            this.Current = this._items;
            this._items = [];

            return this.Current.Any();
        }

        public Task<bool> MoveNextAsync(CancellationToken cancellationToken = default) =>
            Task.FromResult(this.MoveNext(cancellationToken));
    }

    private static MemoryRecord CreateRecord(string id) =>
        MemoryRecord.LocalRecord(
            id: id,
            text: $"text_{id}",
            description: $"description_{id}",
            key: id,
            embedding: new[] { 1.1f, 2.2f, 3.3f });

    private static (MemoryRecord[], string[]) CreateRecords(int count)
    {
        var keys = Enumerable.Range(0, count).Select(i => $"{i}").ToArray();
        var memoryRecords = keys.Select(CreateRecord).ToArray();

        return (memoryRecords, keys);
    }

    private static void AssertMemoryRecordEqual(MemoryRecord expectedRecord, MemoryRecord actualRecord, bool assertEmbeddingEqual = true)
    {
        Assert.Equal(expectedRecord.Key, actualRecord.Key);
        Assert.Equal(expectedRecord.Metadata.Id, actualRecord.Metadata.Id);
        Assert.Equal(expectedRecord.Metadata.Text, actualRecord.Metadata.Text);
        Assert.Equal(expectedRecord.Metadata.Description, actualRecord.Metadata.Description);
        Assert.Equal(expectedRecord.Metadata.AdditionalMetadata, actualRecord.Metadata.AdditionalMetadata);
        Assert.Equal(expectedRecord.Metadata.IsReference, actualRecord.Metadata.IsReference);
        Assert.Equal(expectedRecord.Metadata.ExternalSourceName, actualRecord.Metadata.ExternalSourceName);

        if (assertEmbeddingEqual)
        {
            Assert.True(expectedRecord.Embedding.Span.SequenceEqual(actualRecord.Embedding.Span));
        }
        else
        {
            Assert.True(actualRecord.Embedding.Span.IsEmpty);
        }
    }

    private static bool VerifyPipeline(PipelineDefinition<MongoDBMemoryEntry, MongoDBMemoryEntry> pipeline, string expectedStage)
    {
        if (pipeline.Stages.Count() != 2)
        {
            return false;
        }

        var actualStage = pipeline.Stages.First().ToString();
        return actualStage == expectedStage;
    }

    #endregion
}
