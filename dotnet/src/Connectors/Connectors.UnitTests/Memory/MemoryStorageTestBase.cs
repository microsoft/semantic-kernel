// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.Memory;
public abstract class MemoryStorageTestBase
{
    protected virtual string CreateRandomCollectionName()
    {
        return $"Collection_{Guid.NewGuid()}";
    }

    /// <summary>
    /// Create <see cref="IMemoryStore"/> instance for unit tests
    /// </summary>
    /// <remarks>
    /// you can override <see cref="CloseStoreAsync"/> in case you need extra clean up control
    /// </remarks>
    /// <returns><see cref="IMemoryStore"/> The instance for tests</returns>
    protected abstract Task<IMemoryStore> CreateStoreAsync();

    /// <summary>
    /// Override to add cleanup code for your <see cref="IMemoryStore"/> instance after unit test
    /// </summary>
    /// <param name="memoryStore"></param>
    /// <returns></returns>
    protected virtual Task CloseStoreAsync(IMemoryStore memoryStore)
    {
        return Task.CompletedTask;
    }

    protected virtual async Task WithStorageAsync(Func<IMemoryStore, Task> factAsync)
    {
        var store = await this.CreateStoreAsync();
        await factAsync(store);
        await this.CloseStoreAsync(store);
    }

    [Fact]
    public virtual Task ItCanCreateAndGetCollectionAsync()
    {
        return this.WithStorageAsync(async db =>
        {
            // Arrange
            string collection = this.CreateRandomCollectionName();

            // Act
            await db.CreateCollectionAsync(collection);
            var collections = db.GetCollectionsAsync();

            // Assert
            Assert.NotEmpty(collections.ToEnumerable());
            Assert.True(await collections.ContainsAsync(collection));
        });
    }

    [Fact]
    public virtual Task ItCanCheckIfCollectionExistsAsync()
    {
        return this.WithStorageAsync(async db =>
        {
            // Arrange
            string collection = this.CreateRandomCollectionName();

            // Act
            await db.CreateCollectionAsync(collection);

            // Assert
            Assert.True(await db.DoesCollectionExistAsync(collection));
            Assert.False(await db.DoesCollectionExistAsync(this.CreateRandomCollectionName()));
        });
    }

    [Fact]
    public virtual Task CreatingDuplicateCollectionDoesNothingAsync()
    {
        return this.WithStorageAsync(async db =>
        {
            // Arrange
            string collection = this.CreateRandomCollectionName();

            // Act
            await db.CreateCollectionAsync(collection);
            var collections = await db.GetCollectionsAsync().ToListAsync();
            await db.CreateCollectionAsync(collection);

            // Assert
            var collections2 = await db.GetCollectionsAsync().ToListAsync();
            Assert.Equal(collections.Count, collections.Count);
        });
    }

    [Fact]
    public virtual Task CollectionsCanBeDeletedAsync()
    {
        return this.WithStorageAsync(async db =>
        {
            // Arrange
            string collection = this.CreateRandomCollectionName();
            await db.CreateCollectionAsync(collection);
            var collections = await db.GetCollectionsAsync().ToListAsync();
            Assert.True(collections.Count > 0);

            // Act
            foreach (var c in collections)
            {
                await db.DeleteCollectionAsync(c);
            }

            // Assert
            var collections2 = db.GetCollectionsAsync();
            Assert.True(await collections2.CountAsync() == 0);
        });
    }

    [Fact]
    public virtual Task ItCanInsertIntoNonExistentCollectionAsync()
    {
        return this.WithStorageAsync(async db =>
        {
            // Arrange
            MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test",
            text: "text",
            description: "description",
            embedding: new Embedding<float>(new float[] { 1, 2, 3 }),
            key: null,
            timestamp: null);

            // Arrange
            string collection = this.CreateRandomCollectionName();
            var key = await db.UpsertAsync(collection, testRecord);
            var actual = await db.GetAsync(collection, key, true);

            // Assert
            Assert.NotNull(actual);
            Assert.Equal(testRecord.Metadata.Id, key);
            Assert.Equal(testRecord.Metadata.Id, actual.Key);
            Assert.Equal(testRecord.Embedding.Vector, actual.Embedding.Vector);
            Assert.Equal(testRecord.Metadata.Text, actual.Metadata.Text);
            Assert.Equal(testRecord.Metadata.Description, actual.Metadata.Description);
            Assert.Equal(testRecord.Metadata.ExternalSourceName, actual.Metadata.ExternalSourceName);
            Assert.Equal(testRecord.Metadata.Id, actual.Metadata.Id);
        });
    }

    [Fact]
    public virtual Task GetAsyncReturnsEmptyEmbeddingUnlessSpecifiedAsync()
    {
        return this.WithStorageAsync(async db =>
        {
            // Arrange
            MemoryRecord testRecord = MemoryRecord.LocalRecord(
            id: "test",
            text: "text",
            description: "description",
            embedding: new Embedding<float>(new float[] { 1, 2, 3 }),
            key: null,
            timestamp: null);
            string collection = this.CreateRandomCollectionName();

            // Act
            await db.CreateCollectionAsync(collection);
            var key = await db.UpsertAsync(collection, testRecord);
            var actualDefault = await db.GetAsync(collection, key);
            var actualWithEmbedding = await db.GetAsync(collection, key, true);

            // Assert
            Assert.NotNull(actualDefault);
            Assert.NotNull(actualWithEmbedding);
            Assert.Empty(actualDefault.Embedding.Vector);
            Assert.NotEmpty(actualWithEmbedding.Embedding.Vector);
        });
    }

    [Fact]
    public virtual Task ItCanUpsertAndRetrieveARecordWithNoTimestampAsync()
    {
        return this.WithStorageAsync(async db =>
        {
            // Arrange
            MemoryRecord testRecord = MemoryRecord.LocalRecord(
                id: "test",
                text: "text",
                description: "description",
                embedding: new Embedding<float>(new float[] { 1, 2, 3 }),
                key: null,
                timestamp: null);
            string collection = this.CreateRandomCollectionName();

            // Act
            await db.CreateCollectionAsync(collection);
            var key = await db.UpsertAsync(collection, testRecord);
            var actual = await db.GetAsync(collection, key, true);

            // Assert
            Assert.NotNull(actual);
            Assert.Equal(testRecord.Metadata.Id, key);
            Assert.Equal(testRecord.Metadata.Id, actual.Key);
            Assert.Equal(testRecord.Embedding.Vector, actual.Embedding.Vector);
            Assert.Equal(testRecord.Metadata.Text, actual.Metadata.Text);
            Assert.Equal(testRecord.Metadata.Description, actual.Metadata.Description);
            Assert.Equal(testRecord.Metadata.ExternalSourceName, actual.Metadata.ExternalSourceName);
            Assert.Equal(testRecord.Metadata.Id, actual.Metadata.Id);
        });
    }

    [Fact]
    public virtual Task ItCanUpsertAndRetrieveARecordWithTimestampAsync()
    {
        return this.WithStorageAsync(async db =>
        {
            // Arrange
            MemoryRecord testRecord = MemoryRecord.LocalRecord(
                id: "test",
                text: "text",
                description: "description",
                embedding: new Embedding<float>(new float[] { 1, 2, 3 }),
                key: null,
                timestamp: DateTimeOffset.UtcNow);
            string collection = this.CreateRandomCollectionName();

            // Act
            await db.CreateCollectionAsync(collection);
            var key = await db.UpsertAsync(collection, testRecord);
            var actual = await db.GetAsync(collection, key, true);

            // Assert
            Assert.NotNull(actual);
            Assert.Equal(testRecord.Metadata.Id, key);
            Assert.Equal(testRecord.Metadata.Id, actual.Key);
            Assert.Equal(testRecord.Embedding.Vector, actual.Embedding.Vector);
            Assert.Equal(testRecord.Metadata.Text, actual.Metadata.Text);
            Assert.Equal(testRecord.Metadata.Description, actual.Metadata.Description);
            Assert.Equal(testRecord.Metadata.ExternalSourceName, actual.Metadata.ExternalSourceName);
            Assert.Equal(testRecord.Metadata.Id, actual.Metadata.Id);
        });
    }

    [Fact]
    public virtual Task UpsertReplacesExistingRecordWithSameIdAsync()
    {
        return this.WithStorageAsync(async db =>
        {
            // Arrange
            string commonId = "test";
            MemoryRecord testRecord = MemoryRecord.LocalRecord(
                id: commonId,
                text: "text",
                description: "description",
                embedding: new Embedding<float>(new float[] { 1, 2, 3 }));
            MemoryRecord testRecord2 = MemoryRecord.LocalRecord(
                id: commonId,
                text: "text2",
                description: "description2",
                embedding: new Embedding<float>(new float[] { 1, 2, 4 }));
            string collection = this.CreateRandomCollectionName();

            // Act
            await db.CreateCollectionAsync(collection);
            var key = await db.UpsertAsync(collection, testRecord);
            var key2 = await db.UpsertAsync(collection, testRecord2);
            var actual = await db.GetAsync(collection, key, true);

            // Assert
            Assert.NotNull(actual);
            Assert.Equal(testRecord.Metadata.Id, key);
            Assert.Equal(testRecord2.Metadata.Id, actual.Key);
            Assert.NotEqual(testRecord.Embedding.Vector, actual.Embedding.Vector);
            Assert.Equal(testRecord2.Embedding.Vector, actual.Embedding.Vector);
            Assert.NotEqual(testRecord.Metadata.Text, actual.Metadata.Text);
            Assert.Equal(testRecord2.Metadata.Description, actual.Metadata.Description);
        });
    }

    [Fact]
    public virtual Task ExistingRecordCanBeRemovedAsync()
    {
        return this.WithStorageAsync(async db =>
        {
            // Arrange
            MemoryRecord testRecord = MemoryRecord.LocalRecord(
                id: "test",
                text: "text",
                description: "description",
                embedding: new Embedding<float>(new float[] { 1, 2, 3 }));
            string collection = this.CreateRandomCollectionName();

            // Act
            await db.CreateCollectionAsync(collection);
            var key = await db.UpsertAsync(collection, testRecord);
            await db.RemoveAsync(collection, key);

            // Assert
            Assert.Null(await db.GetAsync(collection, key));
        });
    }

    [Fact]
    public virtual Task RemovingNonExistingRecordDoesNothingAsync()
    {
        return this.WithStorageAsync(async db =>
        {
            // Arrange
            string collection = this.CreateRandomCollectionName();

            // Act
            await db.CreateCollectionAsync(collection);
            await db.RemoveAsync(collection, "key");
            var actual = await db.GetAsync(collection, "key");

            // Assert
            Assert.Null(actual);
        });
    }

    [Fact]
    public virtual Task ItCanListAllDatabaseCollectionsAsync()
    {
        return this.WithStorageAsync(async db =>
        {
            // Arrange
            string[] testCollections = { this.CreateRandomCollectionName(), this.CreateRandomCollectionName(), this.CreateRandomCollectionName() };
            await db.CreateCollectionAsync(testCollections[0]);
            await db.CreateCollectionAsync(testCollections[1]);
            await db.CreateCollectionAsync(testCollections[2]);

            // Act
            var collections = await db.GetCollectionsAsync().ToListAsync();

#pragma warning disable CA1851 // Possible multiple enumerations of 'IEnumerable' collection
            // Assert
            foreach (var collection in testCollections)
            {
                Assert.True(await db.DoesCollectionExistAsync(collection));
            }

            Assert.NotNull(collections);
            Assert.NotEmpty(collections);
            //Assert.Equal(testCollections.Length, collections.Count);
            Assert.True(collections.Contains(testCollections[0]),
                $"Collections does not contain the newly-created collection {testCollections[0]}");
            Assert.True(collections.Contains(testCollections[1]),
                $"Collections does not contain the newly-created collection {testCollections[1]}");
            Assert.True(collections.Contains(testCollections[2]),
                $"Collections does not contain the newly-created collection {testCollections[2]}");
#pragma warning restore CA1851 // Possible multiple enumerations of 'IEnumerable' collection
        });
    }

    [Fact]
    public virtual Task GetNearestMatchesReturnsAllResultsWithNoMinScoreAsync()
    {
        return this.WithStorageAsync(async db =>
        {
            // Arrange
            var compareEmbedding = new Embedding<float>(new float[] { 1, 1, 1 });
            int topN = 4;
            string collection = this.CreateRandomCollectionName();
            await db.CreateCollectionAsync(collection);
            int i = 0;
            MemoryRecord testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { 1, 1, 1 }));
            _ = await db.UpsertAsync(collection, testRecord);

            i++;
            testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { -1, -1, -1 }));
            _ = await db.UpsertAsync(collection, testRecord);

            i++;
            testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { 1, 2, 3 }));
            _ = await db.UpsertAsync(collection, testRecord);

            i++;
            testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { -1, -2, -3 }));
            _ = await db.UpsertAsync(collection, testRecord);

            i++;
            testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { 1, -1, -2 }));
            _ = await db.UpsertAsync(collection, testRecord);

            // Act
            double threshold = -1;
            var topNResults = db.GetNearestMatchesAsync(collection, compareEmbedding, limit: topN, minRelevanceScore: threshold).ToEnumerable().ToArray();

            // Assert
            Assert.Equal(topN, topNResults.Length);
            for (int j = 0; j < topN - 1; j++)
            {
                int compare = topNResults[j].Item2.CompareTo(topNResults[j + 1].Item2);
                Assert.True(compare >= 0);
            }
        });
    }

    [Fact]
    public virtual Task GetNearestMatchAsyncReturnsEmptyEmbeddingUnlessSpecifiedAsync()
    {
        return this.WithStorageAsync(async db =>
        {
            // Arrange
            var compareEmbedding = new Embedding<float>(new float[] { 1, 1, 1 });
            string collection = this.CreateRandomCollectionName();
            await db.CreateCollectionAsync(collection);
            int i = 0;
            MemoryRecord testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { 1, 1, 1 }));
            _ = await db.UpsertAsync(collection, testRecord);

            i++;
            testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { -1, -1, -1 }));
            _ = await db.UpsertAsync(collection, testRecord);

            i++;
            testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { 1, 2, 3 }));
            _ = await db.UpsertAsync(collection, testRecord);

            i++;
            testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { -1, -2, -3 }));
            _ = await db.UpsertAsync(collection, testRecord);

            i++;
            testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { 1, -1, -2 }));
            _ = await db.UpsertAsync(collection, testRecord);

            // Act
            double threshold = 0.75;
            var topNResultDefault = await db.GetNearestMatchAsync(collection, compareEmbedding, minRelevanceScore: threshold);
            var topNResultWithEmbedding = await db.GetNearestMatchAsync(collection, compareEmbedding, minRelevanceScore: threshold, withEmbedding: true);

            // Assert
            Assert.NotNull(topNResultDefault);
            Assert.NotNull(topNResultWithEmbedding);
            Assert.Empty(topNResultDefault.Value.Item1.Embedding.Vector);
            Assert.NotEmpty(topNResultWithEmbedding.Value.Item1.Embedding.Vector);
        });
    }

    [Fact]
    public virtual Task GetNearestMatchAsyncReturnsExpectedAsync()
    {
        return this.WithStorageAsync(async db =>
        {
            // Arrange
            var compareEmbedding = new Embedding<float>(new float[] { 1, 1, 1 });
            string collection = this.CreateRandomCollectionName();
            await db.CreateCollectionAsync(collection);
            int i = 0;
            MemoryRecord testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { 1, 1, 1 }));
            _ = await db.UpsertAsync(collection, testRecord);

            i++;
            testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { -1, -1, -1 }));
            _ = await db.UpsertAsync(collection, testRecord);

            i++;
            testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { 1, 2, 3 }));
            _ = await db.UpsertAsync(collection, testRecord);

            i++;
            testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { -1, -2, -3 }));
            _ = await db.UpsertAsync(collection, testRecord);

            i++;
            testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { 1, -1, -2 }));
            _ = await db.UpsertAsync(collection, testRecord);

            // Act
            double threshold = 0.75;
            var topNResult = await db.GetNearestMatchAsync(collection, compareEmbedding, minRelevanceScore: threshold);

            // Assert
            Assert.NotNull(topNResult);
            Assert.Equal("test0", topNResult.Value.Item1.Metadata.Id);
            Assert.True(topNResult.Value.Item2 >= threshold);
        });
    }

    [Fact]
    public virtual Task GetNearestMatchesDifferentiatesIdenticalVectorsByKeyAsync()
    {
        return this.WithStorageAsync(async db =>
        {
            // Arrange
            var compareEmbedding = new Embedding<float>(new float[] { 1, 1, 1 });
            int topN = 4;
            string collection = this.CreateRandomCollectionName();
            await db.CreateCollectionAsync(collection);

            for (int i = 0; i < 10; i++)
            {
                MemoryRecord testRecord = MemoryRecord.LocalRecord(
                    id: "test" + i,
                    text: "text" + i,
                    description: "description" + i,
                    embedding: new Embedding<float>(new float[] { 1, 1, 1 }));
                _ = await db.UpsertAsync(collection, testRecord);
            }

            // Act
            var topNResults = db.GetNearestMatchesAsync(collection, compareEmbedding, limit: topN, minRelevanceScore: 0.75).ToEnumerable().ToArray();
            IEnumerable<string> topNKeys = topNResults.Select(x => x.Item1.Key).ToImmutableSortedSet();

            // Assert
            Assert.Equal(topN, topNResults.Length);
            Assert.Equal(topN, topNKeys.Count());

            for (int i = 0; i < topNResults.Length; i++)
            {
                int compare = topNResults[i].Item2.CompareTo(0.75);
                Assert.True(compare >= 0);
            }
        });
    }

    [Fact]
    public virtual Task ItCanBatchUpsertRecordsAsync()
    {
        return this.WithStorageAsync(async db =>
        {
            // Arrange
            int numRecords = 10;
            string collection = this.CreateRandomCollectionName();
            IEnumerable<MemoryRecord> records = this.CreateBatchRecords(numRecords);

            // Act
            await db.CreateCollectionAsync(collection);
            var keys = db.UpsertBatchAsync(collection, records);
            var resultRecords = db.GetBatchAsync(collection, keys.ToEnumerable());

            // Assert
            Assert.NotNull(keys);
            Assert.Equal(numRecords, keys.ToEnumerable().Count());
            Assert.Equal(numRecords, resultRecords.ToEnumerable().Count());
        });
    }

    [Fact]
    public virtual Task ItCanBatchGetRecordsAsync()
    {
        return this.WithStorageAsync(async db =>
        {
            // Arrange
            int numRecords = 10;
            string collection = this.CreateRandomCollectionName();
            IEnumerable<MemoryRecord> records = this.CreateBatchRecords(numRecords);
            var keys = db.UpsertBatchAsync(collection, records);

            // Act
            await db.CreateCollectionAsync(collection);
            var results = db.GetBatchAsync(collection, keys.ToEnumerable());

            // Assert
            Assert.NotNull(keys);
            Assert.NotNull(results);
            Assert.Equal(numRecords, results.ToEnumerable().Count());
        });
    }

    [Fact]
    public virtual Task ItCanBatchRemoveRecordsAsync()
    {
        return this.WithStorageAsync(async db =>
        {
            // Arrange
            int numRecords = 10;
            string collection = this.CreateRandomCollectionName();
            IEnumerable<MemoryRecord> records = this.CreateBatchRecords(numRecords);
            await db.CreateCollectionAsync(collection);

            List<string> keys = new();

            // Act
            await foreach (var key in db.UpsertBatchAsync(collection, records))
            {
                keys.Add(key);
            }

            await db.RemoveBatchAsync(collection, keys);

            // Assert
            await foreach (var result in db.GetBatchAsync(collection, keys))
            {
                Assert.Null(result);
            }
        });
    }

    [Fact]
    public virtual Task DeletingNonExistentCollectionDoesNothingAsync()
    {
        return this.WithStorageAsync(async db =>
        {
            // Arrange
            string collection = this.CreateRandomCollectionName();

            // Act
            await db.DeleteCollectionAsync(collection);
        });
    }

    protected virtual IEnumerable<MemoryRecord> CreateBatchRecords(int numRecords)
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
                embedding: new Embedding<float>(new float[] { 1, 1, 1 }));
            records = records.Append(testRecord);
        }

        for (int i = numRecords / 2; i < numRecords; i++)
        {
            var testRecord = MemoryRecord.ReferenceRecord(
                externalId: "test" + i,
                sourceName: "sourceName" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { 1, 2, 3 }));
            records = records.Append(testRecord);
        }

        return records;
    }
}
