// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.jdbc;

import java.time.ZonedDateTime;
import java.util.List;
import reactor.core.publisher.Mono;

public interface SQLConnector {

    /**
     * Asynchronously creates a table in the database.
     *
     * @return A Mono representing the completion of the table creation operation.
     */
    Mono<Void> createTableAsync();

    /**
     * Asynchronously creates a collection within the database.
     *
     * @param collectionName The name of the collection to be created.
     * @return A Mono representing the completion of the collection creation operation.
     */
    Mono<Void> createCollectionAsync(String collectionName);

    /**
     * Asynchronously updates an entry.
     *
     * @param collection The name of the collection containing the entry.
     * @param key The key identifying the entry to update.
     * @param metadata The metadata associated with the entry.
     * @param embedding The embedding data associated with the entry.
     * @param timestamp The timestamp of the update.
     * @return A Mono representing the completion of the update operation.
     */
    Mono<Void> updateAsync(
            String collection,
            String key,
            String metadata,
            String embedding,
            ZonedDateTime timestamp);

    /**
     * Asynchronously inserts or ignores an entry.
     *
     * @param collection The name of the collection to insert the entry into.
     * @param key The key identifying the entry.
     * @param metadata The metadata associated with the entry.
     * @param embedding The embedding data associated with the entry.
     * @param timestamp The timestamp of the insertion.
     * @return A Mono representing the completion of the insertion operation.
     */
    Mono<Void> insertOrIgnoreAsync(
            String collection,
            String key,
            String metadata,
            String embedding,
            ZonedDateTime timestamp);

    /**
     * Asynchronously checks if a collection exists.
     *
     * @param collectionName The name of the collection to check.
     * @return A Mono emitting a boolean value indicating whether the collection exists.
     */
    Mono<Boolean> doesCollectionExistsAsync(String collectionName);

    /**
     * Asynchronously retrieves a list of collection names.
     *
     * @return A Mono emitting a list of collection names.
     */
    Mono<List<String>> getCollectionsAsync();

    /**
     * Asynchronously reads all entries within a collection.
     *
     * @param collectionName The name of the collection to read from.
     * @return A Mono emitting a list of DatabaseEntry objects representing the entries.
     */
    Mono<List<DatabaseEntry>> readAllAsync(String collectionName);

    /**
     * Asynchronously reads a specific entry within a collection.
     *
     * @param collectionName The name of the collection to read from.
     * @param key The key identifying the entry to read.
     * @return A Mono emitting a DatabaseEntry object representing the entry.
     */
    Mono<DatabaseEntry> readAsync(String collectionName, String key);

    /**
     * Asynchronously deletes a collection.
     *
     * @param collectionName The name of the collection to delete.
     * @return A Mono representing the completion of the collection deletion operation.
     */
    Mono<Void> deleteCollectionAsync(String collectionName);

    /**
     * Asynchronously deletes an entry within a collection.
     *
     * @param collectionName The name of the collection to delete the entry from.
     * @param key The key identifying the entry to delete.
     * @return A Mono representing the completion of the entry deletion operation.
     */
    Mono<Void> deleteAsync(String collectionName, String key);

    /**
     * Asynchronously deletes all empty entries within a collection.
     *
     * @param collectionName The name of the collection to delete empty entries from.
     * @return A Mono representing the completion of the empty entry deletion operation.
     */
    Mono<Void> deleteEmptyAsync(String collectionName);
}
