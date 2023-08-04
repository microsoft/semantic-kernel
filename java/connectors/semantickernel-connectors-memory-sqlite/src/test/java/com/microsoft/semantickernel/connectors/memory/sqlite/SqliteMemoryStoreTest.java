// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.sqlite;

import com.microsoft.semantickernel.ai.embeddings.Embedding;
import com.microsoft.semantickernel.memory.MemoryRecord;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import reactor.util.function.Tuple2;

import java.sql.SQLException;
import java.time.ZonedDateTime;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.List;

public class SqliteMemoryStoreTest {

    private SqliteMemoryStore connect() throws SQLException {
        SqliteMemoryStore memoryStore = (SqliteMemoryStore) new SqliteMemoryStore.Builder().build();
        memoryStore.connectAsync(":memory:").block();
        return memoryStore;
    }

    private static int collectionNum = 0;

    private String getNewCollectionName() {
        collectionNum++;
        return "test_collection_" + collectionNum;
    }

    @Test
    public void testCreation() throws SQLException {
        SqliteMemoryStore memory = connect();
    }

    @Test
    public void testCreateAndGetCollections() throws SQLException {
        SqliteMemoryStore memory = connect();
        String name = getNewCollectionName();

        memory.createCollectionAsync(name).block();
        List<String> collections = memory.getCollectionsAsync().block();

        Assertions.assertNotNull(collections);
        Assertions.assertTrue(collections.contains(name));
    }

    @Test
    public void testDoesCollectionExist() throws SQLException {
        SqliteMemoryStore memory = connect();
        String name = getNewCollectionName();

        memory.createCollectionAsync(name).block();
        Boolean collectionExists = memory.doesCollectionExistAsync(name).block();

        Assertions.assertEquals(Boolean.TRUE, collectionExists);
    }

    @Test
    public void testDuplicateCreateDoesNothing() throws SQLException {
        SqliteMemoryStore memory = connect();
        String name = getNewCollectionName();

        memory.createCollectionAsync(name).block();
        List<String> collectionsBefore = memory.getCollectionsAsync().block();

        memory.createCollectionAsync(name).block();
        List<String> collectionsAfter = memory.getCollectionsAsync().block();

        Assertions.assertNotNull(collectionsBefore);
        Assertions.assertNotNull(collectionsAfter);
        Assertions.assertEquals(collectionsBefore.size(), collectionsAfter.size());
    }

    @Test
    public void testDeleteCollection() throws SQLException {
        SqliteMemoryStore memory = connect();
        String name = getNewCollectionName();

        memory.createCollectionAsync(name).block();
        List<String> collections = memory.getCollectionsAsync().block();

        Assertions.assertNotNull(collections);
        Assertions.assertFalse(collections.isEmpty());

        collections.forEach(collection -> memory.deleteCollectionAsync(collection).block());

        collections = memory.getCollectionsAsync().block();
        Assertions.assertNotNull(collections);
        Assertions.assertTrue(collections.isEmpty());
    }

    @Test
    public void testCollectionsAreAllListed() throws SQLException {
        SqliteMemoryStore memory = connect();

        int collectionsToTest = 5;
        List<String> collectionNames = new ArrayList<>(collectionsToTest);
        for (int i = 0; i < collectionsToTest; ++i) {
            collectionNames.add(getNewCollectionName());
        }

        collectionNames.forEach(name -> memory.createCollectionAsync(name).block());
        collectionNames.forEach(
                name -> {
                    Assertions.assertEquals(
                            Boolean.TRUE, memory.doesCollectionExistAsync(name).block());
                });

        List<String> collections = memory.getCollectionsAsync().block();
        Assertions.assertNotNull(collections);
        collectionNames.forEach(name -> Assertions.assertTrue(collections.contains(name)));
    }

    @Test
    public void testUpsertAndRetrieve() throws SQLException {
        SqliteMemoryStore memory = connect();
        String collectionName = getNewCollectionName();

        memory.createCollectionAsync(collectionName).block();

        MemoryRecord testRecord =
                MemoryRecord.localRecord(
                        "test",
                        "test",
                        "test",
                        new Embedding(new ArrayList<>(Arrays.asList(1.23f, 4.56f, 7.89f))),
                        null,
                        "test",
                        ZonedDateTime.now());

        String key = memory.upsertAsync(collectionName, testRecord).block();
        Assertions.assertNotNull(key);

        MemoryRecord inserted = memory.getAsync(collectionName, key, true).block();
        Assertions.assertNotNull(inserted);
        Assertions.assertEquals(testRecord.getMetadata().getId(), key);
        Assertions.assertEquals(testRecord.getMetadata().getId(), inserted.getKey());
        // Assertions.assertIterableEquals(testRecord.getEmbedding().getVector(),
        // inserted.getEmbedding().getVector());
        Assertions.assertEquals(
                testRecord.getMetadata().getText(), inserted.getMetadata().getText());
        Assertions.assertEquals(
                testRecord.getMetadata().getDescription(), inserted.getMetadata().getDescription());
        Assertions.assertEquals(
                testRecord.getMetadata().getExternalSourceName(),
                inserted.getMetadata().getExternalSourceName());
        Assertions.assertEquals(testRecord.getMetadata().getId(), inserted.getMetadata().getId());
    }

    @Test
    public void testGetNearestMatchesAsync() throws SQLException {
        SqliteMemoryStore memory = connect();
        String collectionName = getNewCollectionName();
        Embedding embedding = new Embedding(Arrays.asList(1.23f, 4.56f, 7.89f));
        memory.createCollectionAsync(collectionName).block();

        MemoryRecord testRecord =
                MemoryRecord.localRecord(
                        "test",
                        "test",
                        "test",
                        embedding,
                        null,
                        "test",
                        ZonedDateTime.now());

        Collection<Tuple2<MemoryRecord,Float>> matches =
                memory.upsertAsync(collectionName, testRecord)
                .then(memory.getNearestMatchesAsync(
                        collectionName,
                        embedding,
                        1,
                        0,
                        true)).block();

        Assertions.assertNotNull(matches);
        Assertions.assertEquals(1, matches.size());
        Assertions.assertEquals(embedding.getVector(), matches.iterator().next().getT1().getEmbedding().getVector());
    }
}
