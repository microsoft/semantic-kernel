// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.memory;

import static org.junit.jupiter.api.Assertions.*;

import com.microsoft.semantickernel.ai.embeddings.Embedding;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.time.ZonedDateTime;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.List;

class VolatileMemoryStoreTests {
    private VolatileMemoryStore _db;

    @BeforeEach
    void setUp() {
        this._db = new VolatileMemoryStore();
    }

    private int _collectionNum = 0;

    private static final String NULL_ADDITIONAL_METADATA = null;
    private static final String NULL_KEY = null;
    private static final ZonedDateTime NULL_TIMESTAMP = null;

    private Collection<MemoryRecord> createBatchRecords(int numRecords) {
        assertTrue(numRecords % 2 == 0, "Number of records must be even");
        assertTrue(numRecords > 0, "Number of records must be greater than 0");

        List<MemoryRecord> records = new ArrayList<>(numRecords);
        for (int i = 0; i < numRecords / 2; i++) {
            MemoryRecord testRecord =
                    MemoryRecord.localRecord(
                            "test" + i,
                            "text" + i,
                            "description" + i,
                            new Embedding<Float>(Arrays.asList(1f, 1f, 1f)),
                            NULL_ADDITIONAL_METADATA,
                            NULL_KEY,
                            NULL_TIMESTAMP);
            records.add(testRecord);
        }

        for (int i = numRecords / 2; i < numRecords; i++) {
            MemoryRecord testRecord =
                    MemoryRecord.referenceRecord(
                            "test" + i,
                            "sourceName" + i,
                            "description" + i,
                            new Embedding<Float>(Arrays.asList(1f, 2f, 3f)),
                            NULL_ADDITIONAL_METADATA,
                            NULL_KEY,
                            NULL_TIMESTAMP);
            records.add(testRecord);
        }

        return records;
    }

    @Test
    void initializeDbConnectionSucceeds() {
        assertNotNull(this._db);
    }

    @Test
    void itCanCreateAndGetCollectionAsync() {
        // Arrange
        String collection = "test_collection" + this._collectionNum;
        this._collectionNum++;

        // Act
        this._db.createCollectionAsync(collection).block();
        Collection<String> collections = this._db.getCollectionsAsync().block();

        // Assert
        assertNotNull(collections);
        assertFalse(collections.isEmpty());
        assertTrue(collections.contains(collection));
    }

    @Test
    void itCannotCreateDuplicateCollectionAsync() {
        // Arrange
        String collection = "test_collection" + this._collectionNum;
        this._collectionNum++;

        // Act
        this._db.createCollectionAsync(collection).block();

        // Assert
        assertThrows(
                MemoryException.class,
                () -> this._db.createCollectionAsync(collection).block(),
                "Should not be able to create duplicate collection");
    }

    @Test
    void itCannotInsertIntoNonExistentCollectionAsync() {

        // Arrange
        MemoryRecord testRecord =
                MemoryRecord.localRecord(
                        "test",
                        "text",
                        "description",
                        new Embedding<Float>(Arrays.asList(1f, 2f, 3f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        String collection = "test_collection" + this._collectionNum;
        this._collectionNum++;

        // Assert
        assertThrows(
                MemoryException.class,
                () -> this._db.upsertAsync(collection, testRecord).block(),
                "Should not be able to insert into a non-existent collection");
    }

    @Test
    void GetAsyncReturnsEmptyEmbeddingUnlessSpecifiedAsync() {
        // Arrange
        MemoryRecord testRecord =
                MemoryRecord.localRecord(
                        "test",
                        "text",
                        "description",
                        new Embedding<Float>(Arrays.asList(1f, 2f, 3f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        String collection = "test_collection" + this._collectionNum;
        this._collectionNum++;

        // Act
        this._db.createCollectionAsync(collection).block();
        String key = this._db.upsertAsync(collection, testRecord).block();
        MemoryRecord actualDefault = this._db.getAsync(collection, key, false).block();
        MemoryRecord actualWithEmbedding = this._db.getAsync(collection, key, true).block();

        // Assert
        assertNotNull(actualDefault);
        assertNotNull(actualDefault.getEmbedding());
        assertTrue(actualDefault.getEmbedding().getVector().isEmpty());
        assertNotNull(actualWithEmbedding);
        assertNotNull(actualWithEmbedding.getEmbedding());
        assertFalse(actualWithEmbedding.getEmbedding().getVector().isEmpty());
        assertNotEquals(testRecord, actualDefault);
        assertEquals(testRecord, actualWithEmbedding);
    }
    /*
        @Test
        void itCanUpsertAndRetrieveARecordWithNoTimestampAsync()
        {
            // Arrange
            MemoryRecord testRecord = MemoryRecord.LocalRecord(
                id: "test",
                text: "text",
                description: "description",
                embedding: new Embedding<float>(new float[] { 1, 2, 3 }),
                key: null,
                timestamp: null);
            String collection = "test_collection" + this._collectionNum;
            this._collectionNum++;

            // Act
            await this._db.CreateCollectionAsync(collection);
            var key = await this._db.UpsertAsync(collection, testRecord);
            var actual = await this._db.GetAsync(collection, key, true);

            // Assert
            Assert.NotNull(actual);
            Assert.Equal(testRecord, actual);
        }

        @Test
        void itCanUpsertAndRetrieveARecordWithTimestampAsync()
        {
            // Arrange
            MemoryRecord testRecord = MemoryRecord.LocalRecord(
                id: "test",
                text: "text",
                description: "description",
                embedding: new Embedding<float>(new float[] { 1, 2, 3 }),
                key: null,
                timestamp: DateTimeOffset.UtcNow);
            String collection = "test_collection" + this._collectionNum;
            this._collectionNum++;

            // Act
            await this._db.CreateCollectionAsync(collection);
            var key = await this._db.UpsertAsync(collection, testRecord);
            var actual = await this._db.GetAsync(collection, key, true);

            // Assert
            Assert.NotNull(actual);
            Assert.Equal(testRecord, actual);
        }

        @Test
        void UpsertReplacesExistingRecordWithSameIdAsync()
        {
            // Arrange
            String commonId = "test";
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
            String collection = "test_collection" + this._collectionNum;
            this._collectionNum++;

            // Act
            await this._db.CreateCollectionAsync(collection);
            var key = await this._db.UpsertAsync(collection, testRecord);
            var key2 = await this._db.UpsertAsync(collection, testRecord2);
            var actual = await this._db.GetAsync(collection, key, true);

            // Assert
            Assert.NotNull(actual);
            Assert.NotEqual(testRecord, actual);
            Assert.Equal(key, key2);
            Assert.Equal(testRecord2, actual);
        }

        @Test
        void ExistingRecordCanBeRemovedAsync()
        {
            // Arrange
            MemoryRecord testRecord = MemoryRecord.LocalRecord(
                id: "test",
                text: "text",
                description: "description",
                embedding: new Embedding<float>(new float[] { 1, 2, 3 }));
            String collection = "test_collection" + this._collectionNum;
            this._collectionNum++;

            // Act
            await this._db.CreateCollectionAsync(collection);
            var key = await this._db.UpsertAsync(collection, testRecord);
            await this._db.RemoveAsync(collection, key);
            var actual = await this._db.GetAsync(collection, key);

            // Assert
            Assert.Null(actual);
        }

        @Test
        void RemovingNonExistingRecordDoesNothingAsync()
        {
            // Arrange
            String collection = "test_collection" + this._collectionNum;
            this._collectionNum++;

            // Act
            await this._db.RemoveAsync(collection, "key");
            var actual = await this._db.GetAsync(collection, "key");

            // Assert
            Assert.Null(actual);
        }

        @Test
        void itCanListAllDatabaseCollectionsAsync()
        {
            // Arrange
            String[] testCollections = { "test_collection5", "test_collection6", "test_collection7" };
            this._collectionNum += 3;
            await this._db.CreateCollectionAsync(testCollections[0]);
            await this._db.CreateCollectionAsync(testCollections[1]);
            await this._db.CreateCollectionAsync(testCollections[2]);

            // Act
            var collections = this._db.GetCollectionsAsync().ToEnumerable();

    #pragma warning disable CA1851 // Possible multiple enumerations of 'IEnumerable' collection
            // Assert
            Assert.NotNull(collections);
            assertTrue(collections.Any(), "Collections is empty");
            Assert.Equal(3, collections.Count());
            assertTrue(collections.Contains(testCollections[0]),
                $"Collections does not contain the newly-created collection {testCollections[0]}");
            assertTrue(collections.Contains(testCollections[1]),
                $"Collections does not contain the newly-created collection {testCollections[1]}");
            assertTrue(collections.Contains(testCollections[2]),
                $"Collections does not contain the newly-created collection {testCollections[2]}");
        }
    #pragma warning restore CA1851 // Possible multiple enumerations of 'IEnumerable' collection

        @Test
        void GetNearestMatchesReturnsAllResultsWithNoMinScoreAsync()
        {
            // Arrange
            var compareEmbedding = new Embedding<float>(new float[] { 1, 1, 1 });
            int topN = 4;
            String collection = "test_collection" + this._collectionNum;
            this._collectionNum++;
            await this._db.CreateCollectionAsync(collection);
            int i = 0;
            MemoryRecord testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { 1, 1, 1 }));
            _ = await this._db.UpsertAsync(collection, testRecord);

            i++;
            testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { -1, -1, -1 }));
            _ = await this._db.UpsertAsync(collection, testRecord);

            i++;
            testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { 1, 2, 3 }));
            _ = await this._db.UpsertAsync(collection, testRecord);

            i++;
            testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { -1, -2, -3 }));
            _ = await this._db.UpsertAsync(collection, testRecord);

            i++;
            testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { 1, -1, -2 }));
            _ = await this._db.UpsertAsync(collection, testRecord);

            // Act
            double threshold = -1;
            var topNResults = this._db.GetNearestMatchesAsync(collection, compareEmbedding, limit: topN, minRelevanceScore: threshold).ToEnumerable().ToArray();

            // Assert
            Assert.Equal(topN, topNResults.Length);
            for (int j = 0; j < topN - 1; j++)
            {
                int compare = topNResults[j].Item2.CompareTo(topNResults[j + 1].Item2);
                assertTrue(compare >= 0);
            }
        }

        @Test
        void GetNearestMatchAsyncReturnsEmptyEmbeddingUnlessSpecifiedAsync()
        {
            // Arrange
            var compareEmbedding = new Embedding<float>(new float[] { 1, 1, 1 });
            String collection = "test_collection" + this._collectionNum;
            this._collectionNum++;
            await this._db.CreateCollectionAsync(collection);
            int i = 0;
            MemoryRecord testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { 1, 1, 1 }));
            _ = await this._db.UpsertAsync(collection, testRecord);

            i++;
            testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { -1, -1, -1 }));
            _ = await this._db.UpsertAsync(collection, testRecord);

            i++;
            testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { 1, 2, 3 }));
            _ = await this._db.UpsertAsync(collection, testRecord);

            i++;
            testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { -1, -2, -3 }));
            _ = await this._db.UpsertAsync(collection, testRecord);

            i++;
            testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { 1, -1, -2 }));
            _ = await this._db.UpsertAsync(collection, testRecord);

            // Act
            double threshold = 0.75;
            var topNResultDefault = await this._db.GetNearestMatchAsync(collection, compareEmbedding, minRelevanceScore: threshold);
            var topNResultWithEmbedding = await this._db.GetNearestMatchAsync(collection, compareEmbedding, minRelevanceScore: threshold, withEmbedding: true);

            // Assert
            Assert.NotNull(topNResultDefault);
            Assert.NotNull(topNResultWithEmbedding);
            Assert.Empty(topNResultDefault.Value.Item1.Embedding.Vector);
            Assert.NotEmpty(topNResultWithEmbedding.Value.Item1.Embedding.Vector);
        }

        @Test
        void GetNearestMatchAsyncReturnsExpectedAsync()
        {
            // Arrange
            var compareEmbedding = new Embedding<float>(new float[] { 1, 1, 1 });
            String collection = "test_collection" + this._collectionNum;
            this._collectionNum++;
            await this._db.CreateCollectionAsync(collection);
            int i = 0;
            MemoryRecord testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { 1, 1, 1 }));
            _ = await this._db.UpsertAsync(collection, testRecord);

            i++;
            testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { -1, -1, -1 }));
            _ = await this._db.UpsertAsync(collection, testRecord);

            i++;
            testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { 1, 2, 3 }));
            _ = await this._db.UpsertAsync(collection, testRecord);

            i++;
            testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { -1, -2, -3 }));
            _ = await this._db.UpsertAsync(collection, testRecord);

            i++;
            testRecord = MemoryRecord.LocalRecord(
                id: "test" + i,
                text: "text" + i,
                description: "description" + i,
                embedding: new Embedding<float>(new float[] { 1, -1, -2 }));
            _ = await this._db.UpsertAsync(collection, testRecord);

            // Act
            double threshold = 0.75;
            var topNResult = await this._db.GetNearestMatchAsync(collection, compareEmbedding, minRelevanceScore: threshold);

            // Assert
            Assert.NotNull(topNResult);
            Assert.Equal("test0", topNResult.Value.Item1.Metadata.Id);
            assertTrue(topNResult.Value.Item2 >= threshold);
        }

        @Test
        void GetNearestMatchesDifferentiatesIdenticalVectorsByKeyAsync()
        {
            // Arrange
            var compareEmbedding = new Embedding<float>(new float[] { 1, 1, 1 });
            int topN = 4;
            String collection = "test_collection" + this._collectionNum;
            this._collectionNum++;
            await this._db.CreateCollectionAsync(collection);

            for (int i = 0; i < 10; i++)
            {
                MemoryRecord testRecord = MemoryRecord.LocalRecord(
                    id: "test" + i,
                    text: "text" + i,
                    description: "description" + i,
                    embedding: new Embedding<float>(new float[] { 1, 1, 1 }));
                _ = await this._db.UpsertAsync(collection, testRecord);
            }

            // Act
            var topNResults = this._db.GetNearestMatchesAsync(collection, compareEmbedding, limit: topN, minRelevanceScore: 0.75).ToEnumerable().ToArray();
            IEnumerable<String> topNKeys = topNResults.Select(x => x.Item1.Key).ToImmutableSortedSet();

            // Assert
            Assert.Equal(topN, topNResults.Length);
            Assert.Equal(topN, topNKeys.Count());

            for (int i = 0; i < topNResults.Length; i++)
            {
                int compare = topNResults[i].Item2.CompareTo(0.75);
                assertTrue(compare >= 0);
            }
        }

        @Test
        void itCanBatchUpsertRecordsAsync()
        {
            // Arrange
            int numRecords = 10;
            String collection = "test_collection" + this._collectionNum;
            this._collectionNum++;
            await this._db.CreateCollectionAsync(collection);
            IEnumerable<MemoryRecord> records = this.CreateBatchRecords(numRecords);

            // Act
            var keys = this._db.UpsertBatchAsync(collection, records);
            var resultRecords = this._db.GetBatchAsync(collection, keys.ToEnumerable());

            // Assert
            Assert.NotNull(keys);
            Assert.Equal(numRecords, keys.ToEnumerable().Count());
            Assert.Equal(numRecords, resultRecords.ToEnumerable().Count());
        }

        @Test
        void itCanBatchGetRecordsAsync()
        {
            // Arrange
            int numRecords = 10;
            String collection = "test_collection" + this._collectionNum;
            this._collectionNum++;
            await this._db.CreateCollectionAsync(collection);
            IEnumerable<MemoryRecord> records = this.CreateBatchRecords(numRecords);
            var keys = this._db.UpsertBatchAsync(collection, records);

            // Act
            var results = this._db.GetBatchAsync(collection, keys.ToEnumerable());

            // Assert
            Assert.NotNull(keys);
            Assert.NotNull(results);
            Assert.Equal(numRecords, results.ToEnumerable().Count());
        }

        @Test
        void itCanBatchRemoveRecordsAsync()
        {
            // Arrange
            int numRecords = 10;
            String collection = "test_collection" + this._collectionNum;
            this._collectionNum++;
            await this._db.CreateCollectionAsync(collection);
            IEnumerable<MemoryRecord> records = this.CreateBatchRecords(numRecords);

            List<String> keys = new List<String>();
            await foreach (var key in this._db.UpsertBatchAsync(collection, records))
            {
                keys.Add(key);
            }

            // Act
            await this._db.RemoveBatchAsync(collection, keys);

            // Assert
            await foreach (var result in this._db.GetBatchAsync(collection, keys))
            {
                assertNull(result);
            }
        }

        @Test
        void CollectionsCanBeDeletedAsync()
        {
            // Arrange
            var collections = this._db.GetCollectionsAsync().ToEnumerable();
            int numCollections = collections.Count();
            assertTrue(numCollections == this._collectionNum);

            // Act
            foreach (var collection in collections)
            {
                await this._db.DeleteCollectionAsync(collection);
            }

            // Assert
            collections = this._db.GetCollectionsAsync().ToEnumerable();
            numCollections = collections.Count();
            assertTrue(numCollections == 0);
            this._collectionNum = 0;
        }

        @Test
        void itThrowsWhenDeletingNonExistentCollectionAsync()
        {
            // Arrange
            String collection = "test_collection" + this._collectionNum;
            this._collectionNum++;

            // Act
            await Assert.ThrowsAsync<MemoryException>(() => this._db.DeleteCollectionAsync(collection));
        }

     */
}
