// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.mysql;

import static org.junit.jupiter.api.Assertions.*;

import com.microsoft.semantickernel.ai.embeddings.Embedding;
import com.microsoft.semantickernel.memory.MemoryException;
import com.microsoft.semantickernel.memory.MemoryRecord;
import com.microsoft.semantickernel.memory.MemoryStore;
import java.io.IOException;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.*;
import java.util.stream.Collectors;
import java.util.stream.IntStream;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.testcontainers.containers.MySQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import reactor.core.publisher.Flux;
import reactor.util.function.Tuple2;

@Testcontainers
public class MySQLMemoryStoreTest {
    @Container private static final MySQLContainer CONTAINER = new MySQLContainer();
    private static final String MYSQL_USER = "test";
    private static final String MYSQL_PASSWORD = "test";

    private static MySQLMemoryStore.Builder builder;
    private static MemoryStore db;
    private static int collectionNum = 0;
    private static final String NULL_ADDITIONAL_METADATA = null;
    private static final String NULL_KEY = null;
    private static final ZonedDateTime NULL_TIMESTAMP = null;

    @BeforeAll
    static void setUp() throws SQLException {
        builder = new MySQLMemoryStore.Builder()
                .withConnection(
                        DriverManager.getConnection(
                                CONTAINER.getJdbcUrl(), MYSQL_USER, MYSQL_PASSWORD));
        db = builder.buildAsync().block();
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
        assertNotNull(db);
    }

    @Test
    void itDoesNotFailWithExistingTables() {
        // Act
        db = builder.buildAsync().block();

        // Assert
        assertNotNull(db);
    }

    @Test
    void itCanCreateAndGetCollectionAsync() throws IOException {
        // Arrange
        String collection = "test_collection" + collectionNum;
        collectionNum++;

        // Act
        db.createCollectionAsync(collection).block();
        Collection<String> collections = db.getCollectionsAsync().block();

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
                () -> db.createCollectionAsync(collection).block(),
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
        String collection = "test_collection" + collectionNum;
        collectionNum++;

        // Assert
        assertThrows(
                MemoryException.class,
                () -> db.upsertAsync(collection, testRecord).block(),
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
        String collection = "test_collection" + collectionNum;
        collectionNum++;

        // Act
        db.createCollectionAsync(collection).block();
        String key = db.upsertAsync(collection, testRecord).block();
        MemoryRecord actualDefault = db.getAsync(collection, key, false).block();
        MemoryRecord actualWithEmbedding = db.getAsync(collection, key, true).block();

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
        String collection = "test_collection" + collectionNum;
        collectionNum++;

        // Act
        db.createCollectionAsync(collection).block();
        String key = db.upsertAsync(collection, testRecord).block();
        MemoryRecord actual = db.getAsync(collection, key, true).block();

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
        String collection = "test_collection" + collectionNum;
        collectionNum++;

        // Act
        db.createCollectionAsync(collection).block();
        String key = db.upsertAsync(collection, testRecord).block();
        MemoryRecord actual = db.getAsync(collection, key, true).block();

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
        String collection = "test_collection" + collectionNum;
        collectionNum++;

        // Act
        db.createCollectionAsync(collection).block();
        String key = db.upsertAsync(collection, testRecord).block();
        String key2 = db.upsertAsync(collection, testRecord2).block();
        MemoryRecord actual = db.getAsync(collection, key, true).block();

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
        String collection = "test_collection" + collectionNum;
        collectionNum++;

        // Act
        db.createCollectionAsync(collection).block();
        String key = db.upsertAsync(collection, testRecord).block();
        assertNotNull(key);
        db.removeAsync(collection, key).block();
        MemoryRecord actual = db.getAsync(collection, key, false).block();

        // Assert
        assertNull(actual);
    }

    @Test
    void removingNonExistingRecordDoesNothingAsync() {
        // Arrange
        String collection = "test_collection" + collectionNum;
        collectionNum++;

        // Act
        db.removeAsync(collection, "key").block();
        MemoryRecord actual = db.getAsync(collection, "key", false).block();

        // Assert
        assertNull(actual);
    }

    @Test
    void itCanListAllDatabaseCollectionsAsync() {
        // Arrange
        int numCollections = 3;
        String[] testCollections =
                IntStream.range(collectionNum, collectionNum += numCollections)
                        .mapToObj(i -> "test_collection" + i)
                        .toArray(String[]::new);

        Collection<String> collections = db.getCollectionsAsync().block();
        assertNotNull(collections);
        int initialSize = collections.size();

        Flux.fromArray(testCollections)
                .concatMap(collection -> db.createCollectionAsync(collection))
                .blockLast();

        // Act
        collections = db.getCollectionsAsync().block();

        // Assert
        assertNotNull(collections);
        assertEquals(initialSize + numCollections, collections.size());
        for (String collection : testCollections) {
            assertTrue(
                    collections.contains(collection),
                    "Collections does not contain the newly-created collection " + collection);
        }
    }

    private String setUpNearestMatches() {
        String collection = "test_collection" + collectionNum;
        collectionNum++;
        db.createCollectionAsync(collection).block();
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
        db.upsertAsync(collection, testRecord).block();

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
        db.upsertAsync(collection, testRecord).block();

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
        db.upsertAsync(collection, testRecord).block();

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
        db.upsertAsync(collection, testRecord).block();

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
        db.upsertAsync(collection, testRecord).block();

        return collection;
    }

    @Test
    void getNearestMatchesReturnsAllResultsWithNoMinScoreAsync() {
        // Arrange
        Embedding compareEmbedding = new Embedding(Arrays.asList(1f, 1f, 1f));
        int topN = 4;
        String collection = setUpNearestMatches();

        // Act
        float threshold = -1f;
        Collection<Tuple2<MemoryRecord, Float>> topNResults =
                db.getNearestMatchesAsync(collection, compareEmbedding, topN, threshold, false)
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
        String collection = setUpNearestMatches();

        // Act
        float threshold = -1f;
        Collection<Tuple2<MemoryRecord, Float>> topNResults =
                db.getNearestMatchesAsync(collection, compareEmbedding, 0, threshold, false)
                        .block();

        // Assert
        assertNotNull(topNResults);
        assertTrue(topNResults.isEmpty());
    }

    @Test
    void getNearestMatchesReturnsEmptyIfLimitZero() {
        // Arrange
        Embedding compareEmbedding = new Embedding(Arrays.asList(1f, 1f, 1f));
        String collection = setUpNearestMatches();

        // Act
        float threshold = -1f;
        Collection<Tuple2<MemoryRecord, Float>> topNResults =
                db.getNearestMatchesAsync(collection, compareEmbedding, 0, threshold, false)
                        .block();

        // Assert
        assertNotNull(topNResults);
        assertTrue(topNResults.isEmpty());
    }

    @Test
    void getNearestMatchesReturnsEmptyIfCollectionEmpty() {
        // Arrange
        Embedding compareEmbedding = new Embedding(Arrays.asList(1f, 1f, 1f));
        String collection = "test_collection" + collectionNum;
        collectionNum++;
        db.createCollectionAsync(collection).block();

        // Act
        float threshold = -1f;
        Collection<Tuple2<MemoryRecord, Float>> topNResults =
                db.getNearestMatchesAsync(
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

        String collection = setUpNearestMatches();

        // Act
        float threshold = 0.75f;
        Tuple2<MemoryRecord, Float> topNResultDefault =
                db.getNearestMatchAsync(collection, compareEmbedding, threshold, false).block();
        Tuple2<MemoryRecord, Float> topNResultWithEmbedding =
                db.getNearestMatchAsync(collection, compareEmbedding, threshold, true).block();

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
        String collection = setUpNearestMatches();

        // Act
        float threshold = 0.75f;
        Tuple2<MemoryRecord, Float> topNResult =
                db.getNearestMatchAsync(collection, compareEmbedding, threshold, false).block();

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
        String collection = "test_collection" + collectionNum;
        collectionNum++;
        db.createCollectionAsync(collection).block();

        // Act
        float threshold = -1f;
        Tuple2<MemoryRecord, Float> topNResults =
                db.getNearestMatchAsync(collection, compareEmbedding, threshold, false).block();

        // Assert
        assertNull(topNResults);
    }

    @Test
    void getNearestMatchesDifferentiatesIdenticalVectorsByKeyAsync() {
        // Arrange
        Embedding compareEmbedding = new Embedding(Arrays.asList(1f, 1f, 1f));
        int topN = 4;
        String collection = "test_collection" + collectionNum;
        collectionNum++;
        db.createCollectionAsync(collection).block();

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
            db.upsertAsync(collection, testRecord).block();
        }

        // Act
        Collection<Tuple2<MemoryRecord, Float>> topNResults =
                db.getNearestMatchesAsync(collection, compareEmbedding, topN, 0.75f, true).block();
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
        String collection = "test_collection" + collectionNum;
        collectionNum++;
        db.createCollectionAsync(collection).block();
        Collection<MemoryRecord> records = this.createBatchRecords(numRecords);

        // Act
        Collection<String> keys = db.upsertBatchAsync(collection, records).block();
        Collection<MemoryRecord> resultRecords = db.getBatchAsync(collection, keys, false).block();

        // Assert
        assertNotNull(keys);
        assertEquals(numRecords, keys.size());
        assertEquals(numRecords, resultRecords.size());
    }

    @Test
    void itCanBatchGetRecordsAsync() {
        // Arrange
        int numRecords = 10;
        String collection = "test_collection" + collectionNum;
        collectionNum++;
        db.createCollectionAsync(collection).block();
        Collection<MemoryRecord> records = this.createBatchRecords(numRecords);
        Collection<String> keys = db.upsertBatchAsync(collection, records).block();

        // Act
        Collection<MemoryRecord> results = db.getBatchAsync(collection, keys, false).block();

        // Assert
        assertNotNull(keys);
        assertNotNull(results);
        assertEquals(numRecords, results.size());
    }

    @Test
    void itCanBatchRemoveRecordsAsync() {
        // Arrange
        int numRecords = 10;
        String collection = "test_collection" + collectionNum;
        collectionNum++;
        db.createCollectionAsync(collection).block();
        Collection<MemoryRecord> records = this.createBatchRecords(numRecords);

        List<String> keys = new ArrayList<>();
        for (String key : db.upsertBatchAsync(collection, records).block()) {
            keys.add(key);
        }

        // Act
        db.removeBatchAsync(collection, keys).block();

        // Assert
        for (MemoryRecord result : db.getBatchAsync(collection, keys, true).block()) {
            assertNull(result);
        }
    }

    @Test
    void collectionsCanBeDeletedAsync() {
        // Arrange
        int numCollections = 3;
        String[] testCollections =
                IntStream.range(collectionNum, collectionNum += numCollections)
                        .mapToObj(i -> "test_collection" + i)
                        .toArray(String[]::new);

        Collection<String> collections = db.getCollectionsAsync().block();
        assertNotNull(collections);
        int initialSize = collections.size();

        Flux.fromArray(testCollections)
                .concatMap(collection -> db.createCollectionAsync(collection))
                .blockLast();
        collectionNum += numCollections;

        // Act
        collections = db.getCollectionsAsync().block();
        assertNotNull(collections);
        assertEquals(initialSize + numCollections, collections.size());

        // Act
        for (String collection : collections) {
            db.deleteCollectionAsync(collection).block();
        }

        // Assert
        collections = db.getCollectionsAsync().block();
        assertNotNull(collections);
        assertEquals(0, collections.size());
    }

    @Test
    void itThrowsWhenDeletingNonExistentCollectionAsync() {
        // Arrange
        String collection = "test_collection" + collectionNum;
        collectionNum++;

        // Act
        assertThrows(MemoryException.class, () -> db.deleteCollectionAsync(collection).block());
    }

    @Test
    void doesCollectionExistAsyncReturnTrueForExistingCollection() {
        // Arrange
        String collection = "test_collection" + collectionNum;
        collectionNum++;
        db.createCollectionAsync(collection).block();

        // Act
        assertTrue(db.doesCollectionExistAsync(collection).block());
    }

    @Test
    void doesCollectionExistAsyncReturnFalseForNonExistentCollection() {
        // Arrange
        String collection = "test_collection" + collectionNum;
        collectionNum++;

        // Act
        assertFalse(db.doesCollectionExistAsync(collection).block());
    }
}
