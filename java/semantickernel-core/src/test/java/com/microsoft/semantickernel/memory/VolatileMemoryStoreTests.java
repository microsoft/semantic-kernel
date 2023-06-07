// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.memory;

import static org.junit.jupiter.api.Assertions.*;

import com.microsoft.semantickernel.ai.embeddings.Embedding;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import reactor.util.function.Tuple2;

import java.time.ZonedDateTime;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Iterator;
import java.util.List;
import java.util.stream.Collectors;

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
    void getAsyncReturnsEmptyEmbeddingUnlessSpecifiedAsync() {
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
        assertNotNull(actualDefault.getEmbedding().getVector());
        assertTrue(actualDefault.getEmbedding().getVector().isEmpty());
        assertNotNull(actualWithEmbedding);
        assertNotNull(actualWithEmbedding.getEmbedding());
        assertNotNull(actualWithEmbedding.getEmbedding().getVector());
        assertFalse(actualWithEmbedding.getEmbedding().getVector().isEmpty());
        assertNotEquals(testRecord, actualDefault);
        assertEquals(testRecord, actualWithEmbedding);
    }

    @Test
    void itCanUpsertAndRetrieveARecordWithNoTimestampAsync() {
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
        MemoryRecord actual = this._db.getAsync(collection, key, true).block();

        // Assert
        assertNotNull(actual);
        assertEquals(testRecord, actual);
    }

    @Test
    void itCanUpsertAndRetrieveARecordWithTimestampAsync() {
        // Arrange
        MemoryRecord testRecord =
                MemoryRecord.localRecord(
                        "test",
                        "text",
                        "description",
                        new Embedding<Float>(Arrays.asList(1f, 2f, 3f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        ZonedDateTime.now());
        String collection = "test_collection" + this._collectionNum;
        this._collectionNum++;

        // Act
        this._db.createCollectionAsync(collection).block();
        String key = this._db.upsertAsync(collection, testRecord).block();
        MemoryRecord actual = this._db.getAsync(collection, key, true).block();

        // Assert
        assertNotNull(actual);
        assertEquals(testRecord, actual);
    }

    @Test
    void UpsertReplacesExistingRecordWithSameIdAsync() {
        // Arrange
        String commonId = "test";
        MemoryRecord testRecord =
                MemoryRecord.localRecord(
                        commonId,
                        "text",
                        "description",
                        new Embedding<Float>(Arrays.asList(1f, 2f, 3f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        MemoryRecord testRecord2 =
                MemoryRecord.localRecord(
                        commonId,
                        "text2",
                        "description2",
                        new Embedding<Float>(Arrays.asList(1f, 2f, 4f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        String collection = "test_collection" + this._collectionNum;
        this._collectionNum++;

        // Act
        this._db.createCollectionAsync(collection).block();
        String key = this._db.upsertAsync(collection, testRecord).block();
        String key2 = this._db.upsertAsync(collection, testRecord2).block();
        MemoryRecord actual = this._db.getAsync(collection, key, true).block();

        // Assert
        assertNotNull(actual);
        assertNotEquals(testRecord, actual);
        assertEquals(key, key2);
        assertEquals(testRecord2, actual);
    }

    @Test
    void ExistingRecordCanBeRemovedAsync() {
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
        assertNotNull(key);
        this._db.removeAsync(collection, key).block();
        MemoryRecord actual = this._db.getAsync(collection, key, false).block();

        // Assert
        assertNull(actual);
    }

    @Test
    void RemovingNonExistingRecordDoesNothingAsync() {
        // Arrange
        String collection = "test_collection" + this._collectionNum;
        this._collectionNum++;

        // Act
        this._db.removeAsync(collection, "key").block();
        MemoryRecord actual = this._db.getAsync(collection, "key", false).block();

        // Assert
        assertNull(actual);
    }

    @Test
    void itCanListAllDatabaseCollectionsAsync() {
        // Arrange
        String[] testCollections = {"test_collection5", "test_collection6", "test_collection7"};
        this._collectionNum += 3;
        this._db.createCollectionAsync(testCollections[0]).block();
        this._db.createCollectionAsync(testCollections[1]).block();
        this._db.createCollectionAsync(testCollections[2]).block();

        // Act
        Collection<String> collections = this._db.getCollectionsAsync().block();

        // Assert
        assertNotNull(collections);
        assertEquals(3, collections.size());
        assertTrue(
                collections.contains(testCollections[0]),
                "Collections does not contain the newly-created collection " + testCollections[0]);
        assertTrue(
                collections.contains(testCollections[1]),
                "Collections does not contain the newly-created collection " + testCollections[1]);
        assertTrue(
                collections.contains(testCollections[2]),
                "Collections does not contain the newly-created collection " + testCollections[2]);
    }

    @Test
    void GetNearestMatchesReturnsAllResultsWithNoMinScoreAsync() {
        // Arrange
        Embedding<Float> compareEmbedding = new Embedding<>(Arrays.asList(1f, 1f, 1f));
        int topN = 4;
        String collection = "test_collection" + this._collectionNum;
        this._collectionNum++;
        this._db.createCollectionAsync(collection).block();
        int i = 0;
        MemoryRecord testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding<Float>(Arrays.asList(1f, 1f, 1f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        this._db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding<Float>(Arrays.asList(-1f, -1f, -1f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        this._db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding<Float>(Arrays.asList(1f, 2f, 3f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        this._db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding<Float>(Arrays.asList(-1f, -2f, -3f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        this._db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding<Float>(Arrays.asList(1f, -1f, -2f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        this._db.upsertAsync(collection, testRecord).block();

        // Act
        double threshold = -1;
        Collection<Tuple2<MemoryRecord, Number>> topNResults =
                this._db
                        .getNearestMatchesAsync(
                                collection, compareEmbedding, topN, threshold, false)
                        .block();

        // Assert
        assertNotNull(topNResults);
        assertEquals(topN, topNResults.size());
        Tuple2<MemoryRecord, Number>[] topNResultsArray = topNResults.toArray(new Tuple2[0]);
        for (int j = 0; j < topN - 1; j++) {
            int compare =
                    Double.compare(
                            topNResultsArray[j].getT2().doubleValue(),
                            topNResultsArray[j + 1].getT2().doubleValue());
            assertTrue(compare >= 0);
        }
    }

    @Test
    void GetNearestMatchAsyncReturnsEmptyEmbeddingUnlessSpecifiedAsync() {
        // Arrange
        Embedding<Float> compareEmbedding = new Embedding<>(Arrays.asList(1f, 1f, 1f));
        int topN = 4;
        String collection = "test_collection" + this._collectionNum;
        this._collectionNum++;
        this._db.createCollectionAsync(collection).block();
        int i = 0;
        MemoryRecord testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding<Float>(Arrays.asList(1f, 1f, 1f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        this._db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding<Float>(Arrays.asList(-1f, -1f, -1f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        this._db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding<Float>(Arrays.asList(1f, 2f, 3f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        this._db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding<Float>(Arrays.asList(-1f, -2f, -3f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        this._db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding<Float>(Arrays.asList(1f, -1f, -2f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        this._db.upsertAsync(collection, testRecord).block();

        // Act
        double threshold = 0.75;
        Tuple2<MemoryRecord, ? extends Number> topNResultDefault =
                this._db
                        .getNearestMatchAsync(collection, compareEmbedding, threshold, false)
                        .block();
        Tuple2<MemoryRecord, ? extends Number> topNResultWithEmbedding =
                this._db
                        .getNearestMatchAsync(collection, compareEmbedding, threshold, true)
                        .block();

        // Assert
        assertNotNull(topNResultDefault);
        assertNotNull(topNResultWithEmbedding);
        assertNotNull(topNResultDefault.getT1().getEmbedding());
        assertNotNull(topNResultDefault.getT1().getEmbedding().getVector());
        assertTrue(topNResultDefault.getT1().getEmbedding().getVector().isEmpty());
        assertNotNull(topNResultWithEmbedding.getT1().getEmbedding());
        assertNotNull(topNResultWithEmbedding.getT1().getEmbedding().getVector());
        assertFalse(topNResultWithEmbedding.getT1().getEmbedding().getVector().isEmpty());
    }

    @Test
    void GetNearestMatchAsyncReturnsExpectedAsync() {
        // Arrange
        Embedding<Float> compareEmbedding = new Embedding<>(Arrays.asList(1f, 1f, 1f));
        int topN = 4;
        String collection = "test_collection" + this._collectionNum;
        this._collectionNum++;
        this._db.createCollectionAsync(collection).block();
        int i = 0;
        MemoryRecord testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding<Float>(Arrays.asList(1f, 1f, 1f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        this._db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding<Float>(Arrays.asList(-1f, -1f, -1f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        this._db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding<Float>(Arrays.asList(1f, 2f, 3f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        this._db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding<Float>(Arrays.asList(-1f, -2f, -3f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        this._db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding<Float>(Arrays.asList(1f, -1f, -2f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        this._db.upsertAsync(collection, testRecord).block();

        // Act
        double threshold = 0.75;
        Tuple2<MemoryRecord, ? extends Number> topNResult =
                this._db
                        .getNearestMatchAsync(collection, compareEmbedding, threshold, false)
                        .block();

        // Assert
        assertNotNull(topNResult);
        assertEquals("test0", topNResult.getT1().getMetadata().getId());
        assertTrue(topNResult.getT2().doubleValue() >= threshold);
    }

    @Test
    void getNearestMatchesDifferentiatesIdenticalVectorsByKeyAsync() {
        // Arrange
        Embedding<Float> compareEmbedding = new Embedding<>(Arrays.asList(1f, 1f, 1f));
        int topN = 4;
        String collection = "test_collection" + this._collectionNum;
        this._collectionNum++;
        this._db.createCollectionAsync(collection).block();

        for (int i = 0; i < 10; i++) {
            MemoryRecord testRecord =
                    MemoryRecord.localRecord(
                            "test" + i,
                            "text" + i,
                            "description" + i,
                            new Embedding<>(Arrays.asList(1f, 1f, 1f)),
                            NULL_ADDITIONAL_METADATA,
                            NULL_KEY,
                            NULL_TIMESTAMP);
            this._db.upsertAsync(collection, testRecord).block();
        }

        // Act
        Collection<Tuple2<MemoryRecord, Number>> topNResults =
                this._db
                        .getNearestMatchesAsync(collection, compareEmbedding, topN, 0.75, true)
                        .block();
        Collection<String> topNKeys =
                topNResults.stream()
                        .map(tuple -> tuple.getT1().getKey())
                        .sorted()
                        .collect(Collectors.toList());

        // Assert
        assertEquals(topN, topNResults.size());
        assertEquals(topN, topNKeys.size());
        for (Iterator<Tuple2<MemoryRecord, Number>> iterator = topNResults.iterator();
                iterator.hasNext(); ) {
            Tuple2<MemoryRecord, Number> tuple = iterator.next();
            int compare = Double.compare(tuple.getT2().doubleValue(), 0.75);
            assertTrue(topNKeys.contains(tuple.getT1().getKey()));
            assertTrue(compare >= 0);
        }
    }

    @Test
    void itCanBatchUpsertRecordsAsync() {
        // Arrange
        int numRecords = 10;
        String collection = "test_collection" + this._collectionNum;
        this._collectionNum++;
        this._db.createCollectionAsync(collection).block();
        Collection<MemoryRecord> records = this.createBatchRecords(numRecords);

        // Act
        Collection<String> keys = this._db.upsertBatchAsync(collection, records).block();
        Collection<MemoryRecord> resultRecords =
                this._db.getBatchAsync(collection, keys, false).block();

        // Assert
        assertNotNull(keys);
        assertEquals(numRecords, keys.size());
        assertEquals(numRecords, resultRecords.size());
    }

    @Test
    void itCanBatchGetRecordsAsync() {
        // Arrange
        int numRecords = 10;
        String collection = "test_collection" + this._collectionNum;
        this._collectionNum++;
        this._db.createCollectionAsync(collection).block();
        Collection<MemoryRecord> records = this.createBatchRecords(numRecords);
        Collection<String> keys = this._db.upsertBatchAsync(collection, records).block();

        // Act
        Collection<MemoryRecord> results = this._db.getBatchAsync(collection, keys, false).block();

        // Assert
        assertNotNull(keys);
        assertNotNull(results);
        assertEquals(numRecords, results.size());
    }

    @Test
    void itCanBatchRemoveRecordsAsync() {
        // Arrange
        int numRecords = 10;
        String collection = "test_collection" + this._collectionNum;
        this._collectionNum++;
        this._db.createCollectionAsync(collection).block();
        Collection<MemoryRecord> records = this.createBatchRecords(numRecords);

        List<String> keys = new ArrayList<>();
        for (String key : this._db.upsertBatchAsync(collection, records).block()) {
            keys.add(key);
        }

        // Act
        this._db.removeBatchAsync(collection, keys);

        // Assert
        for (MemoryRecord result : this._db.getBatchAsync(collection, keys, false).block()) {
            assertNull(result);
        }
    }

    @Test
    void CollectionsCanBeDeletedAsync() {
        // Arrange
        Collection<String> collections = this._db.getCollectionsAsync().block();
        int numCollections = collections.size();
        assertEquals(this._collectionNum, numCollections);

        // Act
        for (String collection : collections) {
            this._db.deleteCollectionAsync(collection);
        }

        // Assert
        collections = this._db.getCollectionsAsync().block();
        numCollections = collections.size();
        assertEquals(0, numCollections);
        this._collectionNum = 0;
    }

    @Test
    void itThrowsWhenDeletingNonExistentCollectionAsync() {
        // Arrange
        String collection = "test_collection" + this._collectionNum;
        this._collectionNum++;

        // Act
        assertThrows(
                MemoryException.class, () -> this._db.deleteCollectionAsync(collection).block());
    }
}
