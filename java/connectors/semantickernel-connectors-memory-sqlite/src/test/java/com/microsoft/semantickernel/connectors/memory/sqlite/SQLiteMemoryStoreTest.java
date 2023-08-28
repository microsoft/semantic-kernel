// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.sqlite;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.microsoft.semantickernel.ai.embeddings.Embedding;
import com.microsoft.semantickernel.memory.MemoryException;
import com.microsoft.semantickernel.memory.MemoryRecord;
import com.microsoft.semantickernel.memory.MemoryStore;

import java.sql.DriverManager;
import java.sql.SQLException;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Iterator;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import reactor.core.publisher.Flux;
import reactor.util.function.Tuple2;

public class SQLiteMemoryStoreTest {

    private static MemoryStore _db;
    private static int _collectionNum = 0;
    private static final String NULL_ADDITIONAL_METADATA = null;
    private static final String NULL_KEY = null;
    private static final ZonedDateTime NULL_TIMESTAMP = null;

    @BeforeAll
    static void setUp() throws SQLException {
        _db = new SQLiteMemoryStore
                .Builder()
                .withFilename(":memory:")
                .build();

        ((SQLiteMemoryStore) _db).connectAsync().block();
    }

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
                            new Embedding(Arrays.asList(1f, 1f, 1f)),
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
                            new Embedding(Arrays.asList(1f, 2f, 3f)),
                            NULL_ADDITIONAL_METADATA,
                            NULL_KEY,
                            NULL_TIMESTAMP);
            records.add(testRecord);
        }

        return records;
    }

    @Test
    void initializeDbConnectionSucceeds() {
        assertNotNull(_db);
    }

    @Test
    void itCanCreateAndGetCollectionAsync() {
        // Arrange
        String collection = "test_collection" + _collectionNum;
        _collectionNum++;

        // Act
        _db.createCollectionAsync(collection).block();
        Collection<String> collections = _db.getCollectionsAsync().block();

        // Assert
        assertNotNull(collections);
        assertFalse(collections.isEmpty());
        assertTrue(collections.contains(collection));
    }

    @Test
    void itHandlesExceptionsWhenCreatingCollectionAsync() {
        // Arrange
        String collection = null;

        // Assert
        assertThrows(
                NullPointerException.class,
                () -> _db.createCollectionAsync(collection).block(),
                "Should not be able to create collection with null name");
    }

    @Test
    void itCannotInsertIntoNonExistentCollectionAsync() {

        // Arrange
        MemoryRecord testRecord =
                MemoryRecord.localRecord(
                        "test",
                        "text",
                        "description",
                        new Embedding(Arrays.asList(1f, 2f, 3f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        String collection = "test_collection" + _collectionNum;
        _collectionNum++;

        // Assert
        assertThrows(
                MemoryException.class,
                () -> _db.upsertAsync(collection, testRecord).block(),
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
                        new Embedding(Arrays.asList(1f, 2f, 3f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        String collection = "test_collection" + _collectionNum;
        _collectionNum++;

        // Act
        _db.createCollectionAsync(collection).block();
        String key = _db.upsertAsync(collection, testRecord).block();
        MemoryRecord actualDefault = _db.getAsync(collection, key, false).block();
        MemoryRecord actualWithEmbedding = _db.getAsync(collection, key, true).block();

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
        assertEquals(testRecord.getMetadata(), actualWithEmbedding.getMetadata());
        assertEquals(
                testRecord.getEmbedding().getVector(),
                actualWithEmbedding.getEmbedding().getVector());
    }

    @Test
    void itCanUpsertAndRetrieveARecordWithNoTimestampAsync() {
        // Arrange
        MemoryRecord testRecord =
                MemoryRecord.localRecord(
                        "test",
                        "text",
                        "description",
                        new Embedding(Arrays.asList(1f, 2f, 3f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        String collection = "test_collection" + _collectionNum;
        _collectionNum++;

        // Act
        _db.createCollectionAsync(collection).block();
        String key = _db.upsertAsync(collection, testRecord).block();
        MemoryRecord actual = _db.getAsync(collection, key, true).block();

        // Assert
        assertNotNull(actual);
        assertEquals(testRecord.getMetadata(), actual.getMetadata());
        assertEquals(testRecord.getEmbedding().getVector(), actual.getEmbedding().getVector());
    }

    @Test
    void itCanUpsertAndRetrieveARecordWithTimestampAsync() {
        // Arrange
        MemoryRecord testRecord =
                MemoryRecord.localRecord(
                        "test",
                        "text",
                        "description",
                        new Embedding(Arrays.asList(1f, 2f, 3f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        ZonedDateTime.now(ZoneId.of("UTC")));
        String collection = "test_collection" + _collectionNum;
        _collectionNum++;

        // Act
        _db.createCollectionAsync(collection).block();
        String key = _db.upsertAsync(collection, testRecord).block();
        MemoryRecord actual = _db.getAsync(collection, key, true).block();

        // Assert
        assertNotNull(actual);
        assertEquals(testRecord.getMetadata(), actual.getMetadata());
        assertEquals(testRecord.getEmbedding().getVector(), actual.getEmbedding().getVector());
    }

    @Test
    void upsertReplacesExistingRecordWithSameIdAsync() {
        // Arrange
        String commonId = "test";
        MemoryRecord testRecord =
                MemoryRecord.localRecord(
                        commonId,
                        "text",
                        "description",
                        new Embedding(Arrays.asList(1f, 2f, 3f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        MemoryRecord testRecord2 =
                MemoryRecord.localRecord(
                        commonId,
                        "text2",
                        "description2",
                        new Embedding(Arrays.asList(1f, 2f, 4f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        String collection = "test_collection" + _collectionNum;
        _collectionNum++;

        // Act
        _db.createCollectionAsync(collection).block();
        String key = _db.upsertAsync(collection, testRecord).block();
        String key2 = _db.upsertAsync(collection, testRecord2).block();
        MemoryRecord actual = _db.getAsync(collection, key, true).block();

        // Assert
        assertNotNull(actual);
        assertNotEquals(testRecord2, actual);
        assertEquals(key, key2);
        assertEquals(testRecord2.getMetadata(), actual.getMetadata());
        assertEquals(testRecord2.getEmbedding().getVector(), actual.getEmbedding().getVector());
    }

    @Test
    void existingRecordCanBeRemovedAsync() {
        // Arrange
        MemoryRecord testRecord =
                MemoryRecord.localRecord(
                        "test",
                        "text",
                        "description",
                        new Embedding(Arrays.asList(1f, 2f, 3f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        String collection = "test_collection" + _collectionNum;
        _collectionNum++;

        // Act
        _db.createCollectionAsync(collection).block();
        String key = _db.upsertAsync(collection, testRecord).block();
        assertNotNull(key);
        _db.removeAsync(collection, key).block();
        MemoryRecord actual = _db.getAsync(collection, key, false).block();

        // Assert
        assertNull(actual);
    }

    @Test
    void removingNonExistingRecordDoesNothingAsync() {
        // Arrange
        String collection = "test_collection" + _collectionNum;
        _collectionNum++;

        // Act
        _db.removeAsync(collection, "key").block();
        MemoryRecord actual = _db.getAsync(collection, "key", false).block();

        // Assert
        assertNull(actual);
    }

    @Test
    void itCanListAllDatabaseCollectionsAsync() {
        // Arrange
        int numCollections = 3;
        String[] testCollections =
                IntStream.range(_collectionNum, _collectionNum += numCollections)
                        .mapToObj(i -> "test_collection" + i)
                        .toArray(String[]::new);

        Collection<String> collections = this._db.getCollectionsAsync().block();
        assertNotNull(collections);
        int initialSize = collections.size();

        Flux.fromArray(testCollections)
                .concatMap(collection -> this._db.createCollectionAsync(collection))
                .blockLast();

        // Act
        collections = this._db.getCollectionsAsync().block();

        // Assert
        assertNotNull(collections);
        assertEquals(initialSize + numCollections, collections.size());
        for (String collection : testCollections) {
            assertTrue(
                    collections.contains(collection),
                    "Collections does not contain the newly-created collection " + collection);
        }
    }

    @Test
    void getNearestMatchesReturnsAllResultsWithNoMinScoreAsync() {
        // Arrange
        Embedding compareEmbedding = new Embedding(Arrays.asList(1f, 1f, 1f));
        int topN = 4;
        String collection = "test_collection" + _collectionNum;
        _collectionNum++;
        _db.createCollectionAsync(collection).block();
        int i = 0;
        MemoryRecord testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding(Arrays.asList(1f, 1f, 1f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        _db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding(Arrays.asList(-1f, -1f, -1f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        _db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding(Arrays.asList(1f, 2f, 3f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        _db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding(Arrays.asList(-1f, -2f, -3f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        _db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding(Arrays.asList(1f, -1f, -2f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        _db.upsertAsync(collection, testRecord).block();

        // Act
        double threshold = -1;
        Collection<Tuple2<MemoryRecord, Float>> topNResults =
                _db
                        .getNearestMatchesAsync(
                                collection, compareEmbedding, topN, threshold, false)
                        .block();

        // Assert
        assertNotNull(topNResults);
        assertEquals(topN, topNResults.size());
        Tuple2<MemoryRecord, Float>[] topNResultsArray = topNResults.toArray(new Tuple2[0]);
        for (int j = 0; j < topN - 1; j++) {
            int compare =
                    Double.compare(topNResultsArray[j].getT2(), topNResultsArray[j + 1].getT2());
            assertTrue(compare >= 0);
        }
    }

    @Test
    void getNearestMatchesReturnsLimit() {
        // Arrange
        Embedding compareEmbedding = new Embedding(Arrays.asList(1f, 1f, 1f));
        String collection = "test_collection" + _collectionNum;
        _collectionNum++;
        _db.createCollectionAsync(collection).block();
        int i = 0;
        MemoryRecord testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding(Arrays.asList(1f, 1f, 1f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        _db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding(Arrays.asList(-1f, -1f, -1f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        _db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding(Arrays.asList(1f, 2f, 3f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        _db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding(Arrays.asList(-1f, -2f, -3f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        _db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding(Arrays.asList(1f, -1f, -2f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        _db.upsertAsync(collection, testRecord).block();

        // Act
        double threshold = -1;
        Collection<Tuple2<MemoryRecord, Float>> topNResults =
                _db
                        .getNearestMatchesAsync(
                                collection, compareEmbedding, i / 2, threshold, false)
                        .block();

        // Assert
        assertNotNull(topNResults);
        assertEquals(i / 2, topNResults.size());
    }

    @Test
    void getNearestMatchesReturnsEmptyIfLimitZero() {
        // Arrange
        Embedding compareEmbedding = new Embedding(Arrays.asList(1f, 1f, 1f));
        String collection = "test_collection" + _collectionNum;
        _collectionNum++;
        _db.createCollectionAsync(collection).block();
        int i = 0;
        MemoryRecord testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding(Arrays.asList(1f, 1f, 1f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        _db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding(Arrays.asList(-1f, -1f, -1f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        _db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding(Arrays.asList(1f, 2f, 3f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        _db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding(Arrays.asList(-1f, -2f, -3f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        _db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding(Arrays.asList(1f, -1f, -2f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        _db.upsertAsync(collection, testRecord).block();

        // Act
        double threshold = -1;
        Collection<Tuple2<MemoryRecord, Float>> topNResults =
                _db
                        .getNearestMatchesAsync(collection, compareEmbedding, 0, threshold, false)
                        .block();

        // Assert
        assertNotNull(topNResults);
        assertTrue(topNResults.isEmpty());
    }

    @Test
    void getNearestMatchesReturnsEmptyIfCollectionEmpty() {
        // Arrange
        Embedding compareEmbedding = new Embedding(Arrays.asList(1f, 1f, 1f));
        String collection = "test_collection" + _collectionNum;
        _collectionNum++;
        _db.createCollectionAsync(collection).block();

        // Act
        double threshold = -1;
        Collection<Tuple2<MemoryRecord, Float>> topNResults =
                _db
                        .getNearestMatchesAsync(
                                collection, compareEmbedding, Integer.MAX_VALUE, threshold, false)
                        .block();

        // Assert
        assertNotNull(topNResults);
        assertTrue(topNResults.isEmpty());
    }

    @Test
    void getNearestMatchAsyncReturnsEmptyEmbeddingUnlessSpecifiedAsync() {
        // Arrange
        Embedding compareEmbedding = new Embedding(Arrays.asList(1f, 1f, 1f));
        int topN = 4;
        String collection = "test_collection" + _collectionNum;
        _collectionNum++;
        _db.createCollectionAsync(collection).block();
        int i = 0;
        MemoryRecord testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding(Arrays.asList(1f, 1f, 1f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        _db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding(Arrays.asList(-1f, -1f, -1f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        _db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding(Arrays.asList(1f, 2f, 3f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        _db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding(Arrays.asList(-1f, -2f, -3f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        _db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding(Arrays.asList(1f, -1f, -2f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        _db.upsertAsync(collection, testRecord).block();

        // Act
        double threshold = 0.75;
        Tuple2<MemoryRecord, Float> topNResultDefault =
                _db
                        .getNearestMatchAsync(collection, compareEmbedding, threshold, false)
                        .block();
        Tuple2<MemoryRecord, Float> topNResultWithEmbedding =
                _db
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
    void getNearestMatchAsyncReturnsExpectedAsync() {
        // Arrange
        Embedding compareEmbedding = new Embedding(Arrays.asList(1f, 1f, 1f));
        int topN = 4;
        String collection = "test_collection" + _collectionNum;
        _collectionNum++;
        _db.createCollectionAsync(collection).block();
        int i = 0;
        MemoryRecord testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding(Arrays.asList(1f, 1f, 1f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        _db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding(Arrays.asList(-1f, -1f, -1f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        _db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding(Arrays.asList(1f, 2f, 3f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        _db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding(Arrays.asList(-1f, -2f, -3f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        _db.upsertAsync(collection, testRecord).block();

        i++;
        testRecord =
                MemoryRecord.localRecord(
                        "test" + i,
                        "text" + i,
                        "description" + i,
                        new Embedding(Arrays.asList(1f, -1f, -2f)),
                        NULL_ADDITIONAL_METADATA,
                        NULL_KEY,
                        NULL_TIMESTAMP);
        _db.upsertAsync(collection, testRecord).block();

        // Act
        double threshold = 0.75;
        Tuple2<MemoryRecord, Float> topNResult =
                _db
                        .getNearestMatchAsync(collection, compareEmbedding, threshold, false)
                        .block();

        // Assert
        assertNotNull(topNResult);
        assertEquals("test0", topNResult.getT1().getMetadata().getId());
        assertTrue(topNResult.getT2() >= threshold);
    }

    @Test
    void getNearestMatcheReturnsEmptyIfCollectionEmpty() {
        // Arrange
        Embedding compareEmbedding = new Embedding(Arrays.asList(1f, 1f, 1f));
        int topN = 4;
        String collection = "test_collection" + _collectionNum;
        _collectionNum++;
        _db.createCollectionAsync(collection).block();

        // Act
        double threshold = -1;
        Tuple2<MemoryRecord, Float> topNResults =
                _db
                        .getNearestMatchAsync(collection, compareEmbedding, threshold, false)
                        .block();

        // Assert
        assertNull(topNResults);
    }

    @Test
    void getNearestMatchesDifferentiatesIdenticalVectorsByKeyAsync() {
        // Arrange
        Embedding compareEmbedding = new Embedding(Arrays.asList(1f, 1f, 1f));
        int topN = 4;
        String collection = "test_collection" + _collectionNum;
        _collectionNum++;
        _db.createCollectionAsync(collection).block();

        for (int i = 0; i < 10; i++) {
            MemoryRecord testRecord =
                    MemoryRecord.localRecord(
                            "test" + i,
                            "text" + i,
                            "description" + i,
                            new Embedding(Arrays.asList(1f, 1f, 1f)),
                            NULL_ADDITIONAL_METADATA,
                            NULL_KEY,
                            NULL_TIMESTAMP);
            _db.upsertAsync(collection, testRecord).block();
        }

        // Act
        Collection<Tuple2<MemoryRecord, Float>> topNResults =
                _db
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
        for (Iterator<Tuple2<MemoryRecord, Float>> iterator = topNResults.iterator();
                iterator.hasNext(); ) {
            Tuple2<MemoryRecord, Float> tuple = iterator.next();
            int compare = Float.compare(tuple.getT2(), 0.75f);
            assertTrue(topNKeys.contains(tuple.getT1().getKey()));
            assertTrue(compare >= 0);
        }
    }

    @Test
    void itCanBatchUpsertRecordsAsync() {
        // Arrange
        int numRecords = 10;
        String collection = "test_collection" + _collectionNum;
        _collectionNum++;
        _db.createCollectionAsync(collection).block();
        Collection<MemoryRecord> records = this.createBatchRecords(numRecords);

        // Act
        Collection<String> keys = _db.upsertBatchAsync(collection, records).block();
        Collection<MemoryRecord> resultRecords =
                _db.getBatchAsync(collection, keys, false).block();

        // Assert
        assertNotNull(keys);
        assertEquals(numRecords, keys.size());
        assertEquals(numRecords, resultRecords.size());
    }

    @Test
    void itCanBatchGetRecordsAsync() {
        // Arrange
        int numRecords = 10;
        String collection = "test_collection" + _collectionNum;
        _collectionNum++;
        _db.createCollectionAsync(collection).block();
        Collection<MemoryRecord> records = this.createBatchRecords(numRecords);
        Collection<String> keys = _db.upsertBatchAsync(collection, records).block();

        // Act
        Collection<MemoryRecord> results = _db.getBatchAsync(collection, keys, false).block();

        // Assert
        assertNotNull(keys);
        assertNotNull(results);
        assertEquals(numRecords, results.size());
    }

    @Test
    void itCanBatchRemoveRecordsAsync() {
        // Arrange
        int numRecords = 10;
        String collection = "test_collection" + _collectionNum;
        _collectionNum++;
        _db.createCollectionAsync(collection).block();
        Collection<MemoryRecord> records = this.createBatchRecords(numRecords);

        List<String> keys = new ArrayList<>();
        for (String key : _db.upsertBatchAsync(collection, records).block()) {
            keys.add(key);
        }

        // Act
        _db.removeBatchAsync(collection, keys).block();

        // Assert
        for (MemoryRecord result : _db.getBatchAsync(collection, keys, true).block()) {
            assertNull(result);
        }
    }

    @Test
    void collectionsCanBeDeletedAsync() {
        // Arrange
        int numCollections = 3;
        String[] testCollections =
                IntStream.range(_collectionNum, _collectionNum += numCollections)
                        .mapToObj(i -> "test_collection" + i)
                        .toArray(String[]::new);

        Collection<String> collections = this._db.getCollectionsAsync().block();
        assertNotNull(collections);
        int initialSize = collections.size();

        Flux.fromArray(testCollections)
                .concatMap(collection -> this._db.createCollectionAsync(collection))
                .blockLast();
        _collectionNum += numCollections;

        // Act
        collections = this._db.getCollectionsAsync().block();
        assertNotNull(collections);
        assertEquals(initialSize + numCollections, collections.size());

        // Act
        for (String collection : collections) {
            this._db.deleteCollectionAsync(collection).block();
        }

        // Assert
        collections = this._db.getCollectionsAsync().block();
        assertNotNull(collections);
        assertEquals(0, collections.size());
    }

    @Test
    void itThrowsWhenDeletingNonExistentCollectionAsync() {
        // Arrange
        String collection = "test_collection" + _collectionNum;
        _collectionNum++;

        // Act
        assertThrows(
                MemoryException.class, () -> _db.deleteCollectionAsync(collection).block());
    }

    @Test
    void doesCollectionExistAsyncReturnTrueForExistingCollection() {
        // Arrange
        String collection = "test_collection" + _collectionNum;
        _collectionNum++;
        _db.createCollectionAsync(collection).block();

        // Act
        assertTrue(_db.doesCollectionExistAsync(collection).block());
    }

    @Test
    void doesCollectionExistAsyncReturnFalseForNonExistentCollection() {
        // Arrange
        String collection = "test_collection" + _collectionNum;
        _collectionNum++;

        // Act
        assertFalse(_db.doesCollectionExistAsync(collection).block());
    }
}
