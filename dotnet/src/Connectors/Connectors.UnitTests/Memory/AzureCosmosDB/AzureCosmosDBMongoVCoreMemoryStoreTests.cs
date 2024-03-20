// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoVCore;
using Microsoft.SemanticKernel.Memory;
using MongoDB.Bson;
using MongoDB.Driver;
using MongoDB.Driver.Core.Clusters;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.AzureCosmosDB;

/// <summary>
/// Unit tests for <see cref="AzureCosmosDBMongoVCoreMemoryStore"/> class.
/// </summary>
public class AzureCosmosDBMongoVCoreMemoryStoreTests
{
    private const string CollectionName = "test-collection";
    private const string DatabaseName = "test-database";

    private readonly Mock<IMongoClient> _mongoClientMock;
    private readonly Mock<ICluster> _mongoClusterMock;
    private readonly Mock<
        IMongoCollection<AzureCosmosDBMongoVCoreMemoryRecord>
    > _mongoCollectionMock;
    private readonly Mock<IMongoDatabase> _mongoDatabaseMock;
    private readonly Mock<MongoClientSettings> _mongoSettingsMock;

    public AzureCosmosDBMongoVCoreMemoryStoreTests()
    {
        this._mongoClientMock = new Mock<IMongoClient>();
        this._mongoDatabaseMock = new Mock<IMongoDatabase>();
        this._mongoCollectionMock =
            new Mock<IMongoCollection<AzureCosmosDBMongoVCoreMemoryRecord>>();
        this._mongoClusterMock = new Mock<ICluster>();
        this._mongoSettingsMock = new Mock<MongoClientSettings>();

        _mockMongoClient.Setup(client => client.Settings).Returns(this._mongoSettingsMock.Object);
        _mockMongoSettings.SetupProperty(
            settings => settings.ApplicationName,
            "DotNet_Semantic_Kernel"
        );
        this._mongoClientMock.Setup(client => client.GetDatabase(DatabaseName, null))
            .Returns(this._mongoDatabaseMock.Object);
        this._mongoClientMock.Setup(client => client.Cluster)
            .Returns(this._mongoClusterMock.Object);
        this._mongoDatabaseMock.Setup(client =>
            client.GetCollection<AzureCosmosDBMongoVCoreMemoryRecord>(CollectionName, null)
        )
            .Returns(this._mongoCollectionMock.Object);
    }

    [Fact]
    public async Task ItCanCreateCollectionAsync()
    {
        // Arrange
        using var memoryStore = new AzureCosmosDBMongoVCoreMemoryStore(
            this._mongoClientMock.Object,
            DatabaseName
        );

        // Act
        await memoryStore.CreateCollectionAsync(CollectionName);

        // Assert
        this._mongoDatabaseMock.Verify(
            d => d.CreateCollectionAsync(CollectionName, default, default),
            Times.Once()
        );
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanCheckWhetherCollectionExistsAsync(bool collectionExists)
    {
        // Arrange
        using var memoryStore = new AzureCosmosDBMongoVCoreMemoryStore(
            this._mongoClientMock.Object,
            DatabaseName
        );
        using var cursorMock = collectionExists
            ? new AsyncCursorMock<string>(CollectionName)
            : new AsyncCursorMock<string>();
        this._mongoDatabaseMock.Setup(client => client.ListCollectionNamesAsync(default, default))
            .ReturnsAsync(cursorMock);

        // Act
        var actualCollectionExists = await memoryStore.DoesCollectionExistAsync(CollectionName);

        // Assert
        Assert.Equal(collectionExists, actualCollectionExists);
        this._mongoDatabaseMock.Verify(
            client => client.ListCollectionNamesAsync(default, default),
            Times.Once()
        );
    }

    [Fact]
    public async Task ItCanDeleteCollectionAsync()
    {
        // Arrange
        using var memoryStore = new AzureCosmosDBMongoVCoreMemoryStore(
            this._mongoClientMock.Object,
            DatabaseName
        );

        // Act
        await memoryStore.DeleteCollectionAsync(CollectionName);

        // Assert
        this._mongoDatabaseMock.Verify(
            client => client.DropCollectionAsync(CollectionName, default),
            Times.Once()
        );
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItCanGetAsync(bool entryExists)
    {
        // Arrange
        using var memoryStore = new AzureCosmosDBMongoVCoreMemoryStore(
            this._mongoClientMock.Object,
            DatabaseName
        );
        var memoryRecord = CreateRecord("id");

        using var cursorMock = entryExists
            ? new AsyncCursorMock<AzureCosmosDBMongoVCoreMemoryRecord>(
                new AzureCosmosDBMongoVCoreMemoryRecord(memoryRecord)
            )
            : new AsyncCursorMock<AzureCosmosDBMongoVCoreMemoryRecord>();

        this._mongoCollectionMock.Setup(c =>
            c.FindAsync(
                It.IsAny<FilterDefinition<AzureCosmosDBMongoVCoreMemoryRecord>>(),
                It.IsAny<FindOptions<AzureCosmosDBMongoVCoreMemoryRecord>>(),
                default
            )
        )
            .ReturnsAsync(cursorMock);

        // Act
        var actualMemoryRecord = await memoryStore.GetAsync(
            CollectionName,
            memoryRecord.Key,
            withEmbedding: true
        );

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
        using var memoryStore = new AzureCosmosDBMongoVCoreMemoryStore(
            this._mongoClientMock.Object,
            DatabaseName
        );
        var (memoryRecords, keys) = CreateRecords(10);

        using var cursorMock = new AsyncCursorMock<AzureCosmosDBMongoVCoreMemoryRecord>(
            memoryRecords.Select(r => new AzureCosmosDBMongoVCoreMemoryRecord(r)).ToArray()
        );

        this._mongoCollectionMock.Setup(c =>
            c.FindAsync(
                It.IsAny<FilterDefinition<AzureCosmosDBMongoVCoreMemoryRecord>>(),
                It.IsAny<FindOptions<AzureCosmosDBMongoVCoreMemoryRecord>>(),
                default
            )
        )
            .ReturnsAsync(cursorMock);

        // Act
        var actualMemoryRecords = await memoryStore
            .GetBatchAsync(CollectionName, keys, withEmbeddings: true)
            .ToListAsync();

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
        var collections = new[] { "collection1", "collection2", "collection3" };
        using var memoryStore = new AzureCosmosDBMongoVCoreMemoryStore(
            this._mongoClientMock.Object,
            DatabaseName
        );
        using var cursorMock = new AsyncCursorMock<string>(collections);

        this._mongoDatabaseMock.Setup(client => client.ListCollectionNamesAsync(default, default))
            .ReturnsAsync(cursorMock);

        // Act
        var actualCollections = await memoryStore.GetCollectionsAsync().ToListAsync();

        // Assert
        Assert.True(collections.SequenceEqual(actualCollections));
    }

    [Fact]
    public async Task ItCanGetNearestMatchAsync()
    {
        // Arrange
        using var memoryStore = new AzureCosmosDBMongoVCoreMemoryStore(
            this._mongoClientMock.Object,
            DatabaseName
        );
        var memoryRecord = CreateRecord("id");
        using var cursorMock = new AsyncCursorMock<BsonDocument>(
            createNearestMatchResult(memoryRecord)
        );

        // Act
        this._mongoCollectionMock.Setup(c =>
            c.AggregateAsync<BsonDocument>(
                It.IsAny<PipelineDefinition<AzureCosmosDBMongoVCoreMemoryRecord, BsonDocument>>(),
                It.IsAny<AggregateOptions>(),
                default
            )
        )
            .ReturnsAsync(cursorMock);
        var match = await memoryStore.GetNearestMatchAsync(CollectionName, new(new[] { 1f }));

        // Assert
        AssertMemoryRecordEqual(memoryRecord, match.Value.Item1);
    }

    [Fact]
    public async Task ItCanRemoveAsync()
    {
        // Arrange
        const string Key = "key";
        using var memoryStore = new AzureCosmosDBMongoVCoreMemoryStore(
            this._mongoClientMock.Object,
            DatabaseName
        );

        // Act
        await memoryStore.RemoveAsync(CollectionName, Key);

        // Assert
        this._mongoCollectionMock.Verify(
            c =>
                c.DeleteOneAsync(
                    It.IsAny<FilterDefinition<AzureCosmosDBMongoVCoreMemoryRecord>>(),
                    default
                ),
            Times.Once()
        );
    }

    [Fact]
    public async Task ItCanRemoveBatchAsync()
    {
        // Arrange
        var keys = new string[] { "key1", "key2", "key3" };
        using var memoryStore = new AzureCosmosDBMongoVCoreMemoryStore(
            this._mongoClientMock.Object,
            DatabaseName
        );

        // Act
        await memoryStore.RemoveBatchAsync(CollectionName, keys);

        // Assert
        this._mongoCollectionMock.Verify(
            c =>
                c.DeleteManyAsync(
                    It.IsAny<FilterDefinition<AzureCosmosDBMongoVCoreMemoryRecord>>(),
                    default
                ),
            Times.Once()
        );
    }

    [Fact]
    public async Task ItCanUpsertAsync()
    {
        // Arrange
        using var memoryStore = new AzureCosmosDBMongoVCoreMemoryStore(
            this._mongoClientMock.Object,
            DatabaseName
        );
        var memoryRecord = CreateRecord("id");

        this._mongoCollectionMock.Setup(c =>
            c.ReplaceOneAsync(
                It.IsAny<FilterDefinition<AzureCosmosDBMongoVCoreMemoryRecord>>(),
                It.Is<AzureCosmosDBMongoVCoreMemoryRecord>(e => e.Id == memoryRecord.Key),
                It.IsAny<ReplaceOptions>(),
                default
            )
        )
            .ReturnsAsync(new ReplaceOneResult.Acknowledged(0, 0, memoryRecord.Key));

        // Act
        var actualMemoryRecordKey = await memoryStore.UpsertAsync(CollectionName, memoryRecord);

        // Assert
        Assert.Equal(memoryRecord.Key, actualMemoryRecordKey);

        this._mongoCollectionMock.Verify(c =>
            c.ReplaceOneAsync(
                It.IsAny<FilterDefinition<AzureCosmosDBMongoVCoreMemoryRecord>>(),
                It.Is<AzureCosmosDBMongoVCoreMemoryRecord>(e => e.Id == memoryRecord.Key),
                It.IsAny<ReplaceOptions>(),
                default
            )
        );
    }

    [Fact]
    public async Task ItCanUpsertBatchAsync()
    {
        // Arrange
        using var memoryStore = new AzureCosmosDBMongoVCoreMemoryStore(
            this._mongoClientMock.Object,
            DatabaseName
        );
        var (memoryRecords, keys) = CreateRecords(10);

        foreach (var key in keys)
        {
            var entryMatch = It.Is<AzureCosmosDBMongoVCoreMemoryRecord>(e => e.Id == key);
            this._mongoCollectionMock.Setup(c =>
                c.ReplaceOneAsync(
                    It.IsAny<FilterDefinition<AzureCosmosDBMongoVCoreMemoryRecord>>(),
                    It.Is<AzureCosmosDBMongoVCoreMemoryRecord>(e => e.Id == key),
                    It.IsAny<ReplaceOptions>(),
                    default
                )
            )
                .ReturnsAsync(new ReplaceOneResult.Acknowledged(0, 0, key));
        }

        // Act
        var actualMemoryRecordKeys = await memoryStore
            .UpsertBatchAsync(CollectionName, memoryRecords)
            .ToListAsync();

        for (int i = 0; i < memoryRecords.Length; i++)
        {
            Assert.Equal(memoryRecords[i].Key, actualMemoryRecordKeys[i]);

            this._mongoCollectionMock.Verify(c =>
                c.ReplaceOneAsync(
                    It.IsAny<FilterDefinition<AzureCosmosDBMongoVCoreMemoryRecord>>(),
                    It.Is<AzureCosmosDBMongoVCoreMemoryRecord>(e => e.Id == memoryRecords[i].Key),
                    It.IsAny<ReplaceOptions>(),
                    default
                )
            );
        }
    }

    [Fact]
    public void ItDisposesClusterOnDispose()
    {
        // Arrange
        var memoryStore = new AzureCosmosDBMongoVCoreMemoryStore(
            this._mongoClientMock.Object,
            DatabaseName
        );

        // Act
        memoryStore.Dispose();

        // Assert
        this._mongoClusterMock.Verify(c => c.Dispose(), Times.Once());
    }

    #region private ================================================================================

    private sealed class AsyncCursorMock<T> : IAsyncCursor<T>
    {
        private T[] _items;

        public IEnumerable<T>? Current { get; private set; }

        public AsyncCursorMock(params T[] items)
        {
            this._items = items ?? Array.Empty<T>();
        }

        public void Dispose() { }

        public bool MoveNext(CancellationToken cancellationToken = default)
        {
            this.Current = this._items;
            this._items = Array.Empty<T>();

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
            embedding: new[] { 1.1f, 2.2f, 3.3f }
        );

    private static (MemoryRecord[], string[]) CreateRecords(int count)
    {
        var keys = Enumerable.Range(0, count).Select(i => $"{i}").ToArray();
        var memoryRecords = keys.Select(k => CreateRecord(k)).ToArray();

        return (memoryRecords, keys);
    }

    private static BsonDocument createNearestMatchResult(MemoryRecord memoryRecord)
    {
        var document = new BsonDocument
        {
            { "_id", memoryRecord.Key },
            { "similarityScore", 1.0 },
            {
                "document",
                new BsonDocument
                {
                    { "_id", memoryRecord.Key },
                    { "embedding", new BsonArray(memoryRecord.Embedding.ToArray()) },
                    {
                        "metadata",
                        new BsonDocument
                        {
                            { "id", memoryRecord.Metadata.Id },
                            { "description", memoryRecord.Metadata.Description },
                            { "text", memoryRecord.Metadata.Text },
                            { "additionalMetadata", memoryRecord.Metadata.AdditionalMetadata },
                            { "externalSourceName", memoryRecord.Metadata.ExternalSourceName },
                            { "isReference", memoryRecord.Metadata.IsReference }
                        }
                    },
                    { "timestamp", DateTime.UtcNow }
                }
            }
        };
        return document;
    }

    private static List<BsonDocument> createNearestMatchesResult(MemoryRecord[] memoryRecords)
    {
        var bsonDocuments = new List<BsonDocument>();
        foreach (var memoryRecord in memoryRecords)
        {
            var document = new BsonDocument
            {
                { "_id", memoryRecord.Key },
                { "similarityScore", 1.0 },
                {
                    "document",
                    new BsonDocument
                    {
                        { "_id", memoryRecord.Key },
                        { "embedding", new BsonArray(memoryRecord.Embedding.ToArray()) },
                        {
                            "metadata",
                            new BsonDocument
                            {
                                { "id", memoryRecord.Metadata.Id },
                                { "description", memoryRecord.Metadata.Description },
                                { "text", memoryRecord.Metadata.Text },
                                { "additionalMetadata", memoryRecord.Metadata.AdditionalMetadata },
                                { "externalSourceName", memoryRecord.Metadata.ExternalSourceName },
                                { "isReference", memoryRecord.Metadata.IsReference }
                            }
                        },
                        { "timestamp", DateTime.UtcNow }
                    }
                }
            };
            bsonDocuments.Add(document);
        }
        return bsonDocuments;
    }

    private static void AssertMemoryRecordEqual(
        MemoryRecord expectedRecord,
        MemoryRecord actualRecord,
        bool assertEmbeddingEqual = true
    )
    {
        Assert.Equal(expectedRecord.Key, actualRecord.Key);
        Assert.Equal(expectedRecord.Metadata.Id, actualRecord.Metadata.Id);
        Assert.Equal(expectedRecord.Metadata.Text, actualRecord.Metadata.Text);
        Assert.Equal(expectedRecord.Metadata.Description, actualRecord.Metadata.Description);
        Assert.Equal(
            expectedRecord.Metadata.AdditionalMetadata,
            actualRecord.Metadata.AdditionalMetadata
        );
        Assert.Equal(expectedRecord.Metadata.IsReference, actualRecord.Metadata.IsReference);
        Assert.Equal(
            expectedRecord.Metadata.ExternalSourceName,
            actualRecord.Metadata.ExternalSourceName
        );

        if (assertEmbeddingEqual)
        {
            Assert.True(expectedRecord.Embedding.Span.SequenceEqual(actualRecord.Embedding.Span));
        }
        else
        {
            Assert.True(actualRecord.Embedding.Span.IsEmpty);
        }
    }

    #endregion
}
