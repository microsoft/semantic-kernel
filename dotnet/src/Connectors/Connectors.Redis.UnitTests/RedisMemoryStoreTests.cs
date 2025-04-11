// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.Linq;
using System.Numerics.Tensors;
using System.Runtime.InteropServices;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Redis;
using Microsoft.SemanticKernel.Memory;
using Moq;
using NRedisStack;
using StackExchange.Redis;
using Xunit;

namespace SemanticKernel.Connectors.Redis.UnitTests;

/// <summary>
/// Unit tests of <see cref="RedisMemoryStore"/>.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted")]
public class RedisMemoryStoreTests
{
    private readonly Mock<IDatabase> _mockDatabase;
    private readonly Dictionary<string, List<MemoryRecord>> _collections;

    public RedisMemoryStoreTests()
    {
        this._mockDatabase = new Mock<IDatabase>();
        this._collections = [];
    }

    [Fact]
    public void ConnectionCanBeInitialized()
    {
        // Arrange
        using RedisMemoryStore store = new(this._mockDatabase.Object, vectorSize: 3);
    }

    [Fact]
    public async Task ItCanCreateAndGetCollectionAsync()
    {
        // Arrange
        using RedisMemoryStore store = new(this._mockDatabase.Object, vectorSize: 3);
        string collection = "test_collection";
        this.MockCreateIndex(collection);

        // Act
        await store.CreateCollectionAsync(collection);
        var collections = store.GetCollectionsAsync();

        // Assert
        Assert.NotEmpty(collections.ToEnumerable());
        Assert.True(await collections.ContainsAsync(collection));
    }

    [Fact]
    public async Task ItCanCheckIfCollectionExistsAsync()
    {
        // Arrange
        using RedisMemoryStore store = new(this._mockDatabase.Object, vectorSize: 3);
        string collection = "my_collection";
        this.MockCreateIndex(collection);

        // Act
        await store.CreateCollectionAsync(collection);

        // Assert
        Assert.True(await store.DoesCollectionExistAsync("my_collection"));
        Assert.False(await store.DoesCollectionExistAsync("my_collection2"));
    }

    [Fact]
    public async Task CollectionsCanBeDeletedAsync()
    {
        // Arrange
        using RedisMemoryStore store = new(this._mockDatabase.Object, vectorSize: 3);
        string collection = "test_collection";
        this.MockCreateIndex(collection, () =>
        {
            this.MockDropIndex(collection);
        });

        await store.CreateCollectionAsync(collection);
        var collections = await store.GetCollectionsAsync().ToListAsync();
        Assert.True(collections.Count > 0);

        // Act
        foreach (var c in collections)
        {
            await store.DeleteCollectionAsync(c);
        }

        // Assert
        var collections2 = store.GetCollectionsAsync();
        Assert.Equal(0, await collections2.CountAsync());
    }

    [Fact]
    public async Task ItCanInsertIntoNonExistentCollectionAsync()
    {
        // Arrange
        using RedisMemoryStore store = new(this._mockDatabase.Object, vectorSize: 3);
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test",
            text: "text",
            description: "description",
            embedding: new float[] { 1, 2, 3 },
            key: null,
            timestamp: null);
        string collection = "random collection";
        string redisKey = $"{collection}:{testRecord.Metadata.Id}";
        byte[] embedding = MemoryMarshal.Cast<float, byte>(testRecord.Embedding.Span).ToArray();
        this._mockDatabase
            .Setup<Task>(x => x.HashSetAsync(
                It.Is<RedisKey>(x => x == redisKey),
                It.Is<HashEntry[]>(x => x.Length == 4 &&
                    x[0].Name == "key" && x[1].Name == "metadata" && x[2].Name == "embedding" && x[3].Name == "timestamp" &&
                    x[0].Value == testRecord.Key && x[1].Value == testRecord.GetSerializedMetadata() && embedding.SequenceEqual((byte[])x[2].Value!) && x[3].Value == -1
                    ),
                It.IsAny<CommandFlags>())
            )
            .Callback(() =>
            {
                this._mockDatabase
                    .Setup<Task<HashEntry[]>>(x => x.HashGetAllAsync(It.Is<RedisKey>(x => x == redisKey), It.IsAny<CommandFlags>()))
                    .ReturnsAsync(new[] {
                        new HashEntry("key", testRecord.Key),
                        new HashEntry("metadata", testRecord.GetSerializedMetadata()),
                        new HashEntry("embedding", embedding),
                        new HashEntry("timestamp", -1)
                    });
            });

        // Arrange
        var key = await store.UpsertAsync(collection, testRecord);
        var actual = await store.GetAsync(collection, key, true);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(testRecord.Metadata.Id, key);
        Assert.Equal(testRecord.Metadata.Id, actual.Key);
        Assert.True(testRecord.Embedding.Span.SequenceEqual(actual.Embedding.Span));
        Assert.Equal(testRecord.Metadata.Text, actual.Metadata.Text);
        Assert.Equal(testRecord.Metadata.Description, actual.Metadata.Description);
        Assert.Equal(testRecord.Metadata.ExternalSourceName, actual.Metadata.ExternalSourceName);
        Assert.Equal(testRecord.Metadata.Id, actual.Metadata.Id);
    }

    [Fact]
    public async Task GetAsyncReturnsEmptyEmbeddingUnlessSpecifiedAsync()
    {
        // Arrange
        using RedisMemoryStore store = new(this._mockDatabase.Object, vectorSize: 3);
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test",
            text: "text",
            description: "description",
            embedding: new float[] { 1, 2, 3 },
            key: null,
            timestamp: null);
        string collection = "test_collection";
        string redisKey = $"{collection}:{testRecord.Metadata.Id}";

        this.MockCreateIndex(collection, () =>
        {
            this.MockHashSet(collection, testRecord);
        });

        // Act
        await store.CreateCollectionAsync(collection);
        var key = await store.UpsertAsync(collection, testRecord);
        var actualDefault = await store.GetAsync(collection, key);
        var actualWithEmbedding = await store.GetAsync(collection, key, true);

        // Assert
        Assert.NotNull(actualDefault);
        Assert.NotNull(actualWithEmbedding);
        Assert.True(actualDefault.Embedding.IsEmpty);
        Assert.False(actualWithEmbedding.Embedding.IsEmpty);
    }

    [Fact]
    public async Task ItCanUpsertAndRetrieveARecordWithNoTimestampAsync()
    {
        // Arrange
        using RedisMemoryStore store = new(this._mockDatabase.Object, vectorSize: 3);
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test",
            text: "text",
            description: "description",
            embedding: new float[] { 1, 2, 3 },
            key: null,
            timestamp: null);
        string collection = "test_collection";
        this.MockCreateIndex(collection, () =>
        {
            this.MockHashSet(collection, testRecord);
        });

        // Act
        await store.CreateCollectionAsync(collection);
        var key = await store.UpsertAsync(collection, testRecord);
        var actual = await store.GetAsync(collection, key, true);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(testRecord.Metadata.Id, key);
        Assert.Equal(testRecord.Metadata.Id, actual.Key);
        Assert.True(testRecord.Embedding.Span.SequenceEqual(actual.Embedding.Span));
        Assert.Equal(testRecord.Metadata.Text, actual.Metadata.Text);
        Assert.Equal(testRecord.Metadata.Description, actual.Metadata.Description);
        Assert.Equal(testRecord.Metadata.ExternalSourceName, actual.Metadata.ExternalSourceName);
        Assert.Equal(testRecord.Metadata.Id, actual.Metadata.Id);
    }

    [Fact]
    public async Task ItCanUpsertAndRetrieveARecordWithTimestampAsync()
    {
        // Arrange
        using RedisMemoryStore store = new(this._mockDatabase.Object, vectorSize: 3);
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test",
            text: "text",
            description: "description",
            embedding: new float[] { 1, 2, 3 },
            key: null,
            timestamp: DateTimeOffset.UtcNow);
        string collection = "test_collection";
        this.MockCreateIndex(collection, () =>
        {
            this.MockHashSet(collection, testRecord);
        });

        // Act
        await store.CreateCollectionAsync(collection);
        var key = await store.UpsertAsync(collection, testRecord);
        var actual = await store.GetAsync(collection, key, true);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(testRecord.Metadata.Id, key);
        Assert.Equal(testRecord.Metadata.Id, actual.Key);
        Assert.True(testRecord.Embedding.Span.SequenceEqual(actual.Embedding.Span));
        Assert.Equal(testRecord.Metadata.Text, actual.Metadata.Text);
        Assert.Equal(testRecord.Metadata.Description, actual.Metadata.Description);
        Assert.Equal(testRecord.Metadata.ExternalSourceName, actual.Metadata.ExternalSourceName);
        Assert.Equal(testRecord.Metadata.Id, actual.Metadata.Id);
    }

    [Fact]
    public async Task UpsertReplacesExistingRecordWithSameIdAsync()
    {
        // Arrange
        using RedisMemoryStore store = new(this._mockDatabase.Object, vectorSize: 3);
        string commonId = "test";
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: commonId,
            text: "text",
            description: "description",
            embedding: new float[] { 1, 2, 3 });
        MemoryRecord testRecord2 = MemoryRecord.LocalRecord(
            id: commonId,
            text: "text2",
            description: "description2",
            embedding: new float[] { 1, 2, 4 });
        string collection = "test_collection";
        this.MockCreateIndex(collection, () =>
        {
            this.MockHashSet(collection, testRecord);
            this.MockHashSet(collection, testRecord2);
        });

        // Act
        await store.CreateCollectionAsync(collection);
        var key = await store.UpsertAsync(collection, testRecord);
        var key2 = await store.UpsertAsync(collection, testRecord2);
        var actual = await store.GetAsync(collection, key, true);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(testRecord.Metadata.Id, key);
        Assert.Equal(testRecord2.Metadata.Id, actual.Key);
        Assert.False(testRecord.Embedding.Span.SequenceEqual(actual.Embedding.Span));
        Assert.True(testRecord2.Embedding.Span.SequenceEqual(actual.Embedding.Span));
        Assert.NotEqual(testRecord.Metadata.Text, actual.Metadata.Text);
        Assert.Equal(testRecord2.Metadata.Description, actual.Metadata.Description);
    }

    [Fact]
    public async Task ExistingRecordCanBeRemovedAsync()
    {
        // Arrange
        using RedisMemoryStore store = new(this._mockDatabase.Object, vectorSize: 3);
        MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test",
            text: "text",
            description: "description",
            embedding: new float[] { 1, 2, 3 });
        string collection = "test_collection";
        this.MockCreateIndex(collection, () =>
        {
            this.MockHashSet(collection, testRecord, () =>
            {
                this.MockKeyDelete(collection, testRecord.Metadata.Id);
            });
        });

        // Act
        await store.CreateCollectionAsync(collection);
        var key = await store.UpsertAsync(collection, testRecord);
        await store.RemoveAsync(collection, key);
        var actual = await store.GetAsync(collection, key);

        // Assert
        Assert.Null(actual);
    }

    [Fact]
    public async Task RemovingNonExistingRecordDoesNothingAsync()
    {
        // Arrange
        using RedisMemoryStore store = new(this._mockDatabase.Object, vectorSize: 3);
        string collection = "test_collection";
        this.MockCreateIndex(collection, () =>
        {
            this.MockKeyDelete(collection, "key");
        });

        // Act
        await store.CreateCollectionAsync(collection);
        await store.RemoveAsync(collection, "key");
        var actual = await store.GetAsync(collection, "key");

        // Assert
        Assert.Null(actual);
    }

    [Fact]
    public async Task ItCanListAllDatabaseCollectionsAsync()
    {
        // Arrange
        using RedisMemoryStore store = new(this._mockDatabase.Object, vectorSize: 3);
        string[] testCollections = { "random_collection1", "random_collection2", "random_collection3" };
        foreach (var collection in testCollections)
        {
            this.MockCreateIndex(collection, () =>
            {
                this.MockDropIndex(collection);
            });
        }
        await store.CreateCollectionAsync(testCollections[0]);
        await store.CreateCollectionAsync(testCollections[1]);
        await store.CreateCollectionAsync(testCollections[2]);

        // Act
        var collections = await store.GetCollectionsAsync().ToListAsync();

        // Assert
        foreach (var collection in testCollections)
        {
            Assert.True(await store.DoesCollectionExistAsync(collection));
        }

        Assert.NotNull(collections);
        Assert.NotEmpty(collections);
        Assert.Equal(testCollections.Length, collections.Count);
        Assert.True(collections.Contains(testCollections[0]),
            $"Collections does not contain the newly-created collection {testCollections[0]}");
        Assert.True(collections.Contains(testCollections[1]),
            $"Collections does not contain the newly-created collection {testCollections[1]}");
        Assert.True(collections.Contains(testCollections[2]),
            $"Collections does not contain the newly-created collection {testCollections[2]}");
    }

    [Fact]
    public async Task GetNearestMatchesReturnsAllResultsWithNoMinScoreAsync()
    {
        // Arrange
        using RedisMemoryStore store = new(this._mockDatabase.Object, vectorSize: 3);
        var compareEmbedding = new float[] { 1, 1, 1 };
        string collection = "test_collection";
        int topN = 4;
        double threshold = -1;
        var testEmbeddings = new[]
        {
            new float[] { 1, 1, 1 },
            new float[] { -1, -1, -1 },
            new float[] { 1, 2, 3 },
            new float[] { -1, -2, -3 },
            new float[] { 1, -1, -2 }
        };
        var testRecords = new List<MemoryRecord>();
        for (int i = 0; i < testEmbeddings.Length; i++)
        {
            testRecords.Add(MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: testEmbeddings[i]));
        }
        this.MockCreateIndex(collection, () =>
        {
            for (int i = 0; i < testRecords.Count; i++)
            {
                if (i + 1 < testRecords.Count)
                {
                    this.MockHashSet(collection, testRecords[i]);
                }
                else
                {
                    this.MockHashSet(collection, testRecords[i], () => this.MockSearch(collection, compareEmbedding, topN, threshold));
                }
            }
        });
        await store.CreateCollectionAsync(collection);
        foreach (var testRecord in testRecords)
        {
            _ = await store.UpsertAsync(collection, testRecord);
        }

        // Act
        var topNResults = store.GetNearestMatchesAsync(collection, compareEmbedding, limit: topN, minRelevanceScore: threshold).ToEnumerable().ToArray();

        // Assert
        Assert.Equal(topN, topNResults.Length);
        for (int j = 0; j < topN - 1; j++)
        {
            int compare = topNResults[j].Item2.CompareTo(topNResults[j + 1].Item2);
            Assert.True(compare >= 0);
        }
    }

    [Fact]
    public async Task GetNearestMatchAsyncReturnsEmptyEmbeddingUnlessSpecifiedAsync()
    {
        // Arrange
        using RedisMemoryStore store = new(this._mockDatabase.Object, vectorSize: 3);
        var compareEmbedding = new float[] { 1, 1, 1 };
        string collection = "test_collection";
        int topN = 1;
        double threshold = 0.75;
        var testEmbeddings = new[]
        {
            new float[] { 1, 1, 1 },
            new float[] { -1, -1, -1 },
            new float[] { 1, 2, 3 },
            new float[] { -1, -2, -3 },
            new float[] { 1, -1, -2 }
        };
        var testRecords = new List<MemoryRecord>();
        for (int i = 0; i < testEmbeddings.Length; i++)
        {
            testRecords.Add(MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: testEmbeddings[i]));
        }
        this.MockCreateIndex(collection, () =>
        {
            for (int i = 0; i < testRecords.Count; i++)
            {
                if (i + 1 < testRecords.Count)
                {
                    this.MockHashSet(collection, testRecords[i]);
                }
                else
                {
                    this.MockHashSet(collection, testRecords[i], () =>
                    {
                        this.MockSearch(collection, compareEmbedding, topN, threshold);
                    });
                }
            }
        });
        await store.CreateCollectionAsync(collection);
        foreach (var testRecord in testRecords)
        {
            _ = await store.UpsertAsync(collection, testRecord);
        }

        // Act
        var topNResultDefault = await store.GetNearestMatchAsync(collection, compareEmbedding, minRelevanceScore: threshold);
        var topNResultWithEmbedding = await store.GetNearestMatchAsync(collection, compareEmbedding, minRelevanceScore: threshold, withEmbedding: true);

        // Assert
        Assert.NotNull(topNResultDefault);
        Assert.NotNull(topNResultWithEmbedding);
        Assert.True(topNResultDefault.Value.Item1.Embedding.IsEmpty);
        Assert.False(topNResultWithEmbedding.Value.Item1.Embedding.IsEmpty);
    }

    [Fact]
    public async Task GetNearestMatchAsyncReturnsExpectedAsync()
    {
        // Arrange
        using RedisMemoryStore store = new(this._mockDatabase.Object, vectorSize: 3);
        var compareEmbedding = new float[] { 1, 1, 1 };
        string collection = "test_collection";
        int topN = 1;
        double threshold = 0.75;
        var testEmbeddings = new[]
        {
            new float[] { 1, 1, 1 },
            new float[] { -1, -1, -1 },
            new float[] { 1, 2, 3 },
            new float[] { -1, -2, -3 },
            new float[] { 1, -1, -2 }
        };
        var testRecords = new List<MemoryRecord>();
        for (int i = 0; i < testEmbeddings.Length; i++)
        {
            testRecords.Add(MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: testEmbeddings[i]));
        }
        this.MockCreateIndex(collection, () =>
        {
            for (int i = 0; i < testRecords.Count; i++)
            {
                if (i + 1 < testRecords.Count)
                {
                    this.MockHashSet(collection, testRecords[i]);
                }
                else
                {
                    this.MockHashSet(collection, testRecords[i], () =>
                    {
                        this.MockSearch(collection, compareEmbedding, topN, threshold);
                    });
                }
            }
        });
        await store.CreateCollectionAsync(collection);
        foreach (var testRecord in testRecords)
        {
            _ = await store.UpsertAsync(collection, testRecord);
        }

        // Act
        var topNResult = await store.GetNearestMatchAsync(collection, compareEmbedding, minRelevanceScore: threshold);

        // Assert
        Assert.NotNull(topNResult);
        Assert.Equal("test0", topNResult.Value.Item1.Metadata.Id);
        Assert.True(topNResult.Value.Item2 >= threshold);
    }

    [Fact]
    public async Task GetNearestMatchesDifferentiatesIdenticalVectorsByKeyAsync()
    {
        // Arrange
        using RedisMemoryStore store = new(this._mockDatabase.Object, vectorSize: 3);
        var compareEmbedding = new float[] { 1, 1, 1 };
        int topN = 4;
        double threshold = 0.75;
        string collection = "test_collection";
        var testRecords = new List<MemoryRecord>();
        for (int i = 0; i < 10; i++)
        {
            testRecords.Add(MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new float[] { 1, 1, 1 }));
        }
        this.MockCreateIndex(collection, () =>
        {
            for (int i = 0; i < testRecords.Count; i++)
            {
                if (i + 1 < testRecords.Count)
                {
                    this.MockHashSet(collection, testRecords[i]);
                }
                else
                {
                    this.MockHashSet(collection, testRecords[i], () =>
                    {
                        this.MockSearch(collection, compareEmbedding, topN, threshold);
                    });
                }
            }
        });
        await store.CreateCollectionAsync(collection);
        foreach (var testRecord in testRecords)
        {
            _ = await store.UpsertAsync(collection, testRecord);
        }

        // Act
        var topNResults = store.GetNearestMatchesAsync(collection, compareEmbedding, limit: topN, minRelevanceScore: threshold).ToEnumerable().ToArray();
        IEnumerable<string> topNKeys = topNResults.Select(x => x.Item1.Key).ToImmutableSortedSet();

        // Assert
        Assert.Equal(topN, topNResults.Length);
        Assert.Equal(topN, topNKeys.Count());

        for (int i = 0; i < topNResults.Length; i++)
        {
            int compare = topNResults[i].Item2.CompareTo(threshold);
            Assert.True(compare >= 0);
        }
    }

    [Fact]
    public async Task ItCanBatchUpsertRecordsAsync()
    {
        // Arrange
        using RedisMemoryStore store = new(this._mockDatabase.Object, vectorSize: 3);
        int numRecords = 10;
        string collection = "test_collection";
        IEnumerable<MemoryRecord> records = this.CreateBatchRecords(numRecords);
        this.MockCreateIndex(collection, () =>
        {
            foreach (var testRecord in records)
            {
                this.MockHashSet(collection, testRecord);
            }
        });

        // Act
        await store.CreateCollectionAsync(collection);
        var keys = store.UpsertBatchAsync(collection, records);
        var resultRecords = store.GetBatchAsync(collection, keys.ToEnumerable());

        // Assert
        Assert.NotNull(keys);
        Assert.Equal(numRecords, keys.ToEnumerable().Count());
        Assert.Equal(numRecords, resultRecords.ToEnumerable().Count());
    }

    [Fact]
    public async Task ItCanBatchGetRecordsAsync()
    {
        // Arrange
        using RedisMemoryStore store = new(this._mockDatabase.Object, vectorSize: 3);
        int numRecords = 10;
        string collection = "test_collection";
        IEnumerable<MemoryRecord> records = this.CreateBatchRecords(numRecords);
        this.MockCreateIndex(collection, () =>
        {
            foreach (var testRecord in records)
            {
                this.MockHashSet(collection, testRecord);
            }
        });
        var keys = store.UpsertBatchAsync(collection, records);

        // Act
        await store.CreateCollectionAsync(collection);
        var results = store.GetBatchAsync(collection, keys.ToEnumerable());

        // Assert
        Assert.NotNull(keys);
        Assert.NotNull(results);
        Assert.Equal(numRecords, results.ToEnumerable().Count());
    }

    [Fact]
    public async Task ItCanBatchRemoveRecordsAsync()
    {
        // Arrange
        using RedisMemoryStore store = new(this._mockDatabase.Object, vectorSize: 3);
        int numRecords = 10;
        string collection = "test_collection";
        IEnumerable<MemoryRecord> records = this.CreateBatchRecords(numRecords);
        this.MockCreateIndex(collection, () =>
        {
            foreach (var testRecord in records)
            {
                this.MockHashSet(collection, testRecord, () => this.MockKeyDelete(collection, testRecord.Metadata.Id));
            }
            this.MockKeyDelete(collection, records.Select(x => x.Metadata.Id));
        });
        await store.CreateCollectionAsync(collection);

        List<string> keys = [];

        // Act
        await foreach (var key in store.UpsertBatchAsync(collection, records))
        {
            keys.Add(key);
        }

        await store.RemoveBatchAsync(collection, keys);

        // Assert
        await foreach (var result in store.GetBatchAsync(collection, keys))
        {
            Assert.Null(result);
        }
    }

    [Fact]
    public async Task GetNearestMatchAsyncThrowsExceptionOnInvalidVectorScoreAsync()
    {
        // Arrange
        using RedisMemoryStore store = new(this._mockDatabase.Object, vectorSize: 3);
        var compareEmbedding = new float[] { 1, 1, 1 };
        string collection = "test_collection";
        int topN = 1;
        double threshold = 0.75;
        var testEmbeddings = new[]
        {
            new float[] { 1, 1, 1 },
            new float[] { -1, -1, -1 },
            new float[] { 1, 2, 3 },
            new float[] { -1, -2, -3 },
            new float[] { 1, -1, -2 }
        };
        var testRecords = new List<MemoryRecord>();
        for (int i = 0; i < testEmbeddings.Length; i++)
        {
            testRecords.Add(MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: testEmbeddings[i]));
        }
        this.MockCreateIndex(collection, () =>
        {
            for (int i = 0; i < testRecords.Count; i++)
            {
                if (i + 1 < testRecords.Count)
                {
                    this.MockHashSet(collection, testRecords[i]);
                }
                else
                {
                    this.MockHashSet(collection, testRecords[i], () =>
                    {
                        this.MockSearch(collection, compareEmbedding, topN, threshold, returnStringVectorScore: true);
                    });
                }
            }
        });
        await store.CreateCollectionAsync(collection);
        foreach (var testRecord in testRecords)
        {
            _ = await store.UpsertAsync(collection, testRecord);
        }

        // Assert
        var ex = await Assert.ThrowsAsync<KernelException>(async () =>
        {
            // Act
            await store.GetNearestMatchAsync(collection, compareEmbedding, minRelevanceScore: threshold);
        });
        Assert.Equal("Invalid or missing vector score value.", ex.Message);
    }

    #region private

    private void MockCreateIndex(string collection, Action? callback = null)
    {
        var mockBatch = new Mock<IBatch>();

        this._mockDatabase
            .Setup(x => x.CreateBatch(It.IsAny<object>()))
            .Returns(mockBatch.Object);

        this._mockDatabase
            .Setup<Task<RedisResult>>(x => x.ExecuteAsync(
                It.Is<string>(x => x == "FT.CREATE"),
                It.Is<object[]>(x => x[0].ToString() == collection))
            )
            .ReturnsAsync(RedisResult.Create("OK", ResultType.SimpleString))
            .Callback(() =>
            {
                this._collections.TryAdd(collection, []);

                this._mockDatabase
                    .Setup<Task<RedisResult>>(x => x.ExecuteAsync(
                        It.Is<string>(x => x == "FT.INFO"),
                        It.Is<object[]>(x => x[0].ToString() == collection))
                    )
                    .ReturnsAsync(RedisResult.Create(new[] {
                        RedisResult.Create("index_name", ResultType.BulkString),
                        RedisResult.Create(collection, ResultType.BulkString)
                    }));

                this._mockDatabase
                    .Setup<Task<RedisResult>>(x => x.ExecuteAsync(
                        It.Is<string>(x => x == "FT._LIST"),
                        It.IsAny<object[]>())
                    )
                    .ReturnsAsync(RedisResult.Create(this._collections.Select(x => RedisResult.Create(x.Key, ResultType.BulkString)).ToArray()));

                callback?.Invoke();
            });

        this._mockDatabase
            .Setup<Task<RedisResult>>(x => x.ExecuteAsync(It.Is<string>(x => x == "FT.INFO"), It.IsAny<object[]>()))
            .Throws(new RedisServerException("Unknown Index name"));
    }

    private void MockDropIndex(string collection, Action? callback = null)
    {
        this._mockDatabase
                .Setup<Task<RedisResult>>(x => x.ExecuteAsync(
                    It.Is<string>(x => x == "FT.DROPINDEX"),
                    It.Is<object[]>(x => x[0].ToString() == collection && x[1].ToString() == "DD"))
                )
                .ReturnsAsync(RedisResult.Create("OK", ResultType.SimpleString))
                .Callback(() =>
                {
                    this._collections.Remove(collection);

                    this._mockDatabase
                        .Setup<Task<RedisResult>>(x => x.ExecuteAsync(
                            It.Is<string>(x => x == "FT.INFO"),
                            It.Is<object[]>(x => x[0].ToString() == collection))
                        )
                        .Throws(new RedisServerException("Unknown Index name"));

                    this._mockDatabase
                        .Setup<Task<RedisResult>>(x => x.ExecuteAsync(
                            It.Is<string>(x => x == "FT._LIST"),
                            It.IsAny<object[]>())
                        )
                        .ReturnsAsync(RedisResult.Create(this._collections.Select(x => RedisResult.Create(x.Key, ResultType.BulkString)).ToArray()));
                });
    }

    private void MockHashSet(string collection, MemoryRecord record, Action? callback = null)
    {
        string redisKey = $"{collection}:{record.Metadata.Id}";
        byte[] embedding = MemoryMarshal.Cast<float, byte>(record.Embedding.Span).ToArray();
        long timestamp = record.Timestamp?.ToUnixTimeMilliseconds() ?? -1;

        this._mockDatabase
            .Setup<Task>(x => x.HashSetAsync(
                It.Is<RedisKey>(x => x == redisKey),
                It.Is<HashEntry[]>(x => x.Length == 4 &&
                    x[0].Name == "key" && x[1].Name == "metadata" && x[2].Name == "embedding" && x[3].Name == "timestamp" &&
                    x[0].Value == record.Key && x[1].Value == record.GetSerializedMetadata() && embedding.SequenceEqual((byte[])x[2].Value!) && x[3].Value == timestamp
                    ),
                It.IsAny<CommandFlags>())
            )
            .Callback(() =>
            {
                (this._collections[collection] ??= []).Add(record);

                this._mockDatabase
                    .Setup<Task<HashEntry[]>>(x => x.HashGetAllAsync(It.Is<RedisKey>(x => x == redisKey), It.IsAny<CommandFlags>()))
                    .ReturnsAsync(new[] {
                        new HashEntry("key", record.Key),
                        new HashEntry("metadata", record.GetSerializedMetadata()),
                        new HashEntry("embedding", embedding),
                        new HashEntry("timestamp", timestamp)
                    });

                callback?.Invoke();
            });
    }

    private void MockKeyDelete(string collection, string key, Action? callback = null)
    {
        string redisKey = $"{collection}:{key}";

        this._mockDatabase
            .Setup<Task<bool>>(x => x.KeyDeleteAsync(
                It.Is<RedisKey>(x => x == redisKey),
                It.IsAny<CommandFlags>())
            )
            .ReturnsAsync(true)
            .Callback(() =>
            {
                (this._collections[collection] ??= []).RemoveAll(x => x.Key == key);

                this._mockDatabase
                    .Setup<Task<HashEntry[]>>(x => x.HashGetAllAsync(It.Is<RedisKey>(x => x == redisKey), It.IsAny<CommandFlags>()))
                    .ReturnsAsync([]);

                callback?.Invoke();
            });
    }

    private void MockKeyDelete(string collection, IEnumerable<string> keys, Action? callback = null)
    {
        RedisKey[] redisKeys = keys.Distinct().Select(key => new RedisKey($"{collection}:{key}")).ToArray();

        this._mockDatabase
            .Setup<Task<long>>(x => x.KeyDeleteAsync(
                It.Is<RedisKey[]>(x => redisKeys.SequenceEqual(x)),
                It.IsAny<CommandFlags>())
            )
            .ReturnsAsync(redisKeys.Length)
            .Callback(() =>
            {
                (this._collections[collection] ??= []).RemoveAll(x => keys.Contains(x.Key));

                foreach (var redisKey in redisKeys)
                {
                    this._mockDatabase
                    .Setup<Task<HashEntry[]>>(x => x.HashGetAllAsync(It.Is<RedisKey>(x => x == redisKey), It.IsAny<CommandFlags>()))
                    .ReturnsAsync([]);
                }

                callback?.Invoke();
            });
    }

    private void MockSearch(string collection, ReadOnlyMemory<float> compareEmbedding, int topN, double threshold, bool returnStringVectorScore = false)
    {
        List<(MemoryRecord Record, double Score)> embeddings = [];

        List<MemoryRecord> records = this._collections.TryGetValue(collection, out var value) ? value : [];

        foreach (var record in records)
        {
            double similarity = TensorPrimitives.CosineSimilarity(compareEmbedding.Span, record.Embedding.Span);
            if (similarity >= threshold)
            {
                embeddings.Add(new(record, similarity));
            }
        }

        embeddings = embeddings.OrderByDescending(l => l.Score).Take(topN).ToList();

        string redisKey = $"{collection}";

        var redisResults = new List<RedisResult>
        {
            RedisResult.Create(embeddings.Count)
        };

        foreach (var item in embeddings)
        {
            long timestamp = item.Record.Timestamp?.ToUnixTimeMilliseconds() ?? -1;
            byte[] embedding = MemoryMarshal.Cast<float, byte>(item.Record.Embedding.Span).ToArray();
            redisResults.Add(RedisResult.Create($"{collection}:{item.Record.Metadata.Id}", ResultType.BulkString));
            redisResults.Add(RedisResult.Create(
                new RedisResult[]
                {
                    RedisResult.Create("key", ResultType.BulkString),
                    RedisResult.Create(item.Record.Metadata.Id, ResultType.BulkString),
                    RedisResult.Create("metadata", ResultType.BulkString),
                    RedisResult.Create(item.Record.GetSerializedMetadata(), ResultType.BulkString),
                    RedisResult.Create("embedding", ResultType.BulkString),
                    RedisResult.Create(embedding, ResultType.BulkString),
                    RedisResult.Create("timestamp", ResultType.BulkString),
                    RedisResult.Create(timestamp, ResultType.BulkString),
                    RedisResult.Create("vector_score", ResultType.BulkString),
                    RedisResult.Create(returnStringVectorScore ? $"score:{1-item.Score}" : 1-item.Score, ResultType.BulkString),
                })
            );
        }

        this._mockDatabase
            .Setup<Task<RedisResult>>(x => x.ExecuteAsync(
                It.Is<string>(x => x == "FT.SEARCH"),
                It.Is<object[]>(x => x[0].ToString() == collection && x[1].ToString() == $"*=>[KNN {topN} @embedding $embedding AS vector_score]"))
            )
            .ReturnsAsync(RedisResult.Create(redisResults.ToArray()));
    }

    private IEnumerable<MemoryRecord> CreateBatchRecords(int numRecords)
    {
        Assert.True(numRecords % 2 == 0, "Number of records must be even");
        Assert.True(numRecords > 0, "Number of records must be greater than 0");

        IEnumerable<MemoryRecord> records = new List<MemoryRecord>(numRecords);
        for (int i = 0; i < numRecords / 2; i++)
        {
            var testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new float[] { 1, 1, 1 });
            records = records.Append(testRecord);
        }

        for (int i = numRecords / 2; i < numRecords; i++)
        {
            var testRecord = MemoryRecord.ReferenceRecord(
                externalId: "test" + i,
                sourceName: "sourceName" + i,
                description: "description" + i,
                embedding: new float[] { 1, 2, 3 });
            records = records.Append(testRecord);
        }

        return records;
    }

    #endregion
}
