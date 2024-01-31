package com.microsoft.semantickernel.connectors.memory.redis;

import com.microsoft.semantickernel.ai.embeddings.Embedding;
import com.microsoft.semantickernel.memory.MemoryException;
import com.microsoft.semantickernel.memory.MemoryException.ErrorCodes;
import com.microsoft.semantickernel.memory.MemoryRecord;
import com.microsoft.semantickernel.memory.MemoryStore;
import reactor.core.publisher.Mono;
import reactor.util.function.Tuple2;
import reactor.util.function.Tuples;
import redis.clients.jedis.JedisPooled;
import redis.clients.jedis.exceptions.JedisDataException;
import redis.clients.jedis.resps.ScanResult;
import redis.clients.jedis.search.*;
import redis.clients.jedis.search.schemafields.VectorField.VectorAlgorithm;
import javax.annotation.Nonnull;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.security.InvalidParameterException;
import java.text.MessageFormat;
import java.time.Instant;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.util.*;

import java.util.function.Function;
import java.util.stream.Collectors;

/**
 * Semantic Memory implementation using Redis Vector Search. For more information about Redis
 * Vector Search {@see https://redis.com/solutions/use-cases/vector-database/}
 */
public class RedisMemoryStore implements MemoryStore {

    private static final VectorAlgorithm DefaultIndexAlgorithm = VectorAlgorithm.HNSW; // FLAT or HNSW
    private static final String DefaultVectorType = RedisVectorType.FLOAT32; // prefer better accuracy
    private static final String DefaultDistanceMetric = RedisVectorDistanceMetric.L2;
    private static final int DefaultQueryDialect = 2; // this has to be >= 2 for vector functionality
    private static final Integer DefaultVectorSize = 1536; // framework model dependent - ada-002
    private static final String SUFFIX = "sk";
    private static final String INDEX = "idx";
    private static final String OK = "OK";

    private final JedisPooled client;
    private int vectorSize = DefaultVectorSize;
    private VectorAlgorithm vectorIndexAlgorithm = DefaultIndexAlgorithm;
    private String vectorDistanceMetric = DefaultDistanceMetric;
    private String vectorType = DefaultVectorType;
    private int queryDialect;

    /**
     * Create a new instance of semantic memory using Redis.
     *
     * @param client A Redis Database client connection.
     * @param vectorSize Embedding vector size, defaults to 1536.
     * @param vectorIndexAlgorithm Indexing algorithm for vectors, defaults to "HNSW"
     * @param vectorDistanceMetric Metric for measuring vector distances, defaults to "COSINE"
     * @param queryDialect Query dialect, must be 2 or greater for vector similarity searching, defaults to 2
     */
    public RedisMemoryStore(
        JedisPooled client,
        Integer vectorSize,
        VectorAlgorithm vectorIndexAlgorithm,
        String vectorDistanceMetric,
        int queryDialect
        ) {

        if (vectorSize <= 0) {
            throw new InvalidParameterException(
                    MessageFormat.format(
                    "Invalid vector size: {vectorSize}. Vector size must be a positive integer.",
                    vectorSize.toString()));
        }

        this.client = client;

        this.vectorSize = vectorSize;
        this.vectorIndexAlgorithm = vectorIndexAlgorithm;
        this.vectorDistanceMetric = vectorDistanceMetric;
        this.queryDialect = queryDialect;
    }

  /**
   * Create a new instance of semantic memory using Redis.
   *
   * @param connectionString Provide connection URL to a Redis instance.
   * @param vectorSize Embedding vector size, defaults to 1536.
   * @param vectorIndexAlgorithm Indexing algorithm for vectors, defaults to "HNSW"
   * @param vectorDistanceMetric Metric for measuring vector distances, defaults to "COSINE"
   * @param queryDialect Query dialect, must be 2 or greater for vector similarity searching, defaults to 2
   */
    public RedisMemoryStore(
        String connectionString,
        int vectorSize,
        VectorAlgorithm vectorIndexAlgorithm,
        String vectorDistanceMetric,
        int queryDialect) {

        if (vectorSize <= 0) {
            throw new InvalidParameterException(
                MessageFormat.format(
                        "Invalid vector size: {vectorSize}. Vector size must be a positive integer.",
                        vectorSize));
        }
        this.client = new JedisPooled(connectionString);

        this.vectorSize = vectorSize;
        this.vectorIndexAlgorithm = vectorIndexAlgorithm;
        this.vectorDistanceMetric = vectorDistanceMetric;
        this.queryDialect = queryDialect;
    }

    /**
     * Returns a Redis key
     *
     * @param collectionName The name associated with a collection of embeddings.
     * @param key The unique id associated with the memory record to get.
     * @return A Redis key that identifies a particular Hash of Json object.
     */
    private static String getRedisKey(String collectionName, String key) {

        String name = collectionName.toLowerCase(Locale.ROOT);
        String id = JsonMemoryRecord.encodeId(key);
        return String.format("%s:%s", name, id);
    }

    /**
     * Returns a long timestamp given a OffsetDateTime
     *
     * @param timestamp An OffsetDateTime.
     * @return A long timestamp or -1 in the case of an error.
     */
    private static long toTimestampLong(OffsetDateTime timestamp) {
        if (timestamp != null)  {
            return timestamp.toInstant().toEpochMilli();
        }
        return -1;
    }

    /**
     * Returns an OffsetDateTime given a valid timestamp
     *
     * @param timestamp A long timestamp value.
     * @return An OffsetDateTime if the timestamp is valid, else null.
     */
    private static OffsetDateTime toDateTime(long timestamp) {
        if (timestamp > 0) {
            Instant instant = Instant.ofEpochMilli(timestamp);
            return OffsetDateTime.ofInstant(instant, ZoneId.systemDefault());
        }
        return null;
    }

    @Override
    public Mono<List<String>> getCollectionsAsync() {
        return Mono.just(getIndexesAsync().block().stream()
                .map(name -> name.substring(0, name.length() - "-sk-idx".length()))
                .collect(Collectors.toList()));
    }

    /**
     * Returns a List of Index(Collection) Names
     *
     * @return A list of names of the embedding indexes, including suffix, in the database
     */
    private Mono<List<String>> getIndexesAsync() {
        return Mono.just(this.client.ftList().stream()
                .filter(name -> name.endsWith("-sk-idx"))
                .collect(Collectors.toList()));
    }

    @Override
    public Mono<Void> createCollectionAsync(@Nonnull String collectionName) {
        // Indexes are created when sending a record. The creation requires the size of the
        return Mono.empty();
    }

    public Mono<Boolean> doesIndexExistAsync(@Nonnull String collectionName) {

        try {
            Map<String, Object> info = this.client.ftInfo(collectionName);
            return Mono.just(info != null && ! info.isEmpty());
        } catch(Exception e) {
            if (!(e instanceof JedisDataException)) {
                throw e;
            }
            return Mono.just(false);
        }
        // return Mono.just(this.client.ftInfo(createIndexName(collectionName)) != null);
    }

    @Override
    public Mono<Boolean> doesCollectionExistAsync(@Nonnull String collectionName) {

        Objects.requireNonNull(collectionName);
        String normalizedIndexName = createIndexName(collectionName);
        return getIndexesAsync()
                .map(
                        list ->
                                list.stream()
                                        .anyMatch(
                                                name ->
                                                        name.equalsIgnoreCase(collectionName)
                                                                || name.equalsIgnoreCase(
                                                                normalizedIndexName)));
    }

    @Override
    public Mono<Void> deleteCollectionAsync(@Nonnull String collectionName) {
        Objects.requireNonNull(collectionName);
        try {
            this.client.ftDropIndex(createIndexName(collectionName));
            return Mono.empty();
        } catch (Exception e) {
            return Mono.error(e);
        }
    }

    @Override
    public Mono<MemoryRecord> getAsync(@Nonnull String collectionName, @Nonnull String key,
        boolean withEmbedding) {

        Map<String, String> map = this.client.hgetAll(String.format("%s:%s",
                collectionName, key).toLowerCase(Locale.ROOT));
        if (map == null) {
            return Mono.empty();
        }
        MemoryRecord record = RedisMemoryRecord.mapToRecord(map, withEmbedding);
        return Mono.just(record);
    }

    public Mono<MemoryRecord> getInternalAsync(@Nonnull String collectionName, @Nonnull String key,
        boolean withEmbedding) {

        Objects.requireNonNull(collectionName);
        Objects.requireNonNull(key);

        Map<String, String> entry = this.client.hgetAll(String.format("%s:%s", collectionName, key));

        if (entry == null)
            return Mono.empty();

        return Mono.just(RedisMemoryRecord.mapToRecord(entry, withEmbedding));
    }

    /**
     * Converts a RedisSearch Document to a HashMap.
     *
     * @param document A Redis Search Document
     *
     * @return A HashMap containing the iterator's entries
     */
    protected Map<String, String> documentToMap(Document document) {

        return iterableToMap(document.getProperties());
    }

    /**
     * Converts an Iterable<Map.Entry<String, Object>> to a HashMap.
     *
     * @param entryIterator An Iterable<Map.Entry<String, Object>>
     *
     * @return A HashMap containing the iterator's entries
     */
    protected Map<String, String> iterableToMap(Iterable<Map.Entry<String, Object>> entryIterator) {

        Map<String, String> entryMap = new HashMap<>();
        entryIterator.forEach((e) -> entryMap.put(e.getKey(), e.getValue().toString()));

        return entryMap;
    }

    protected MemoryRecord documentToMemoryRecord(Document document, boolean withEmbedding) {

        Map<String, String> map = documentToMap(document);
        return RedisMemoryRecord.mapToRecord(map, withEmbedding);
    }

    @Override
    public Mono<Collection<MemoryRecord>> getBatchAsync(@Nonnull String collectionName,
        @Nonnull Collection<String> keys, boolean withEmbeddings) {
        Objects.requireNonNull(collectionName);
        // ACS issues one query per key; redis has several possible calls, fastest will be hkeys followed by hvals
        Collection<MemoryRecord> records = keys.stream().map(key -> getAsync(collectionName, key, withEmbeddings).block())
                .collect(Collectors.toList());

        return Mono.just(records);
    }

    @Override
    public Mono<String> upsertAsync(@Nonnull String collectionName, @Nonnull MemoryRecord record) {
        return upsertRecordAsync(collectionName, record);
    }

    /**
     * Returns the key of the upserted object (wraps the record in a list and calls the batch function).
     *
     * @param collectionName The name associated with a collection of embeddings.
     * @param record The memory record to upsert.
     * @return The key of the newly created record.
     */
    public Mono<String> upsertRecordAsync(@Nonnull String collectionName, @Nonnull MemoryRecord record) {
        return upsertBatchAsync(collectionName, Collections.singletonList(record))
                .map(Collection::iterator)
                .map(Iterator::next);
    }

    @Override
    public Mono<Collection<String>> upsertBatchAsync(@Nonnull String collectionName,
        @Nonnull Collection<MemoryRecord> records) {

        Objects.requireNonNull(collectionName);
        Objects.requireNonNull(records);

        if (records.isEmpty()) {
            return Mono.just(Collections.emptyList());
        }

        doesCollectionExistAsync(collectionName)
                .map(
                        exists -> {
                            if (! exists) {
                                int embeddingSize = records.stream()
                                        .map(record -> record.getEmbedding().getVector())
                                        .map(List::size)
                                        .max(Integer::compareTo)
                                        .orElse(0);
                                createIndexAsync(collectionName, embeddingSize);
                            }
                            return true;
                        }
                );

        return Mono.just(records.stream().map(record -> {
            Map<String, Object> map = RedisMemoryRecord.recordToMap(record);
            // we have to change the embeddings to bytes - it's easiest to modify the map
            List<Float> embedding = record.getEmbedding().getVector();
            map.replace(RedisMemoryRecord.EMBEDDING, embedding, embeddingToBytes(embedding));
            String key = getRedisKey(collectionName, record.getMetadata().getId());
            this.client.hsetObject(key, map);
            return key;
        }).collect(Collectors.toList()));
    }

    @Override
    public Mono<Void> removeAsync(@Nonnull String collectionName, @Nonnull String key) {
        return Mono.fromRunnable(
            () -> this.client.hdel(String.format("%s:%s", collectionName, key)));
      }

    @Override
    public Mono<Void> removeBatchAsync(@Nonnull String collectionName,
        @Nonnull Collection<String> keys) {
        return Mono.fromRunnable(
            () -> {
                // ScanResult<String> results = this.client.scan(collectionName);
                // results.getResult().forEach(key -> this.client.hdel(key));
                keys.forEach(key -> this.client.hdel(String.format("%s:%s", collectionName, key)));
            });
    }

    /**
     * Create a new search index.
     *
     * @param collectionName Index name
     * @param embeddingSize  Size of the embedding vector
     * @return A Mono that completes when the index is created
     */
    private Mono<Boolean> createIndexAsync(
        @Nonnull String collectionName, int embeddingSize) {
        if (embeddingSize < 1) {
            throw new RedisException(
                RedisException.ErrorCodes.INVALID_EMBEDDING_SIZE, "the value must be greater than zero");
        }

        Map<String, Object> attributes = new HashMap<String, Object>() {
            {
                put(RedisIndexSchemaParams.TYPE, vectorType);
                put(RedisIndexSchemaParams.DIM, embeddingSize);
                put(RedisIndexSchemaParams.DIST, vectorDistanceMetric); }
        };
        Schema schema = new Schema()
                .addVectorField("Embedding", Schema.VectorField.VectorAlgo.FLAT, attributes).as("Embedding")
                .addTextField("Id", 1.0).as("Id")
                .addTextField("Text", 1.0).as("Text")
                .addTextField("Description", 1.0).as("Description")
                .addTextField("AdditionalMetadata", 1.0).as("AdditionalMetadata")
                .addTextField("ExternalSourceName", 1.0).as("ExternalSourceName");

        IndexDefinition rule = new IndexDefinition(IndexDefinition.Type.HASH)
                .setPrefixes(collectionName.toLowerCase() + ":");
        // customarily redis indexes are named <collection>-idx; we're going to suffix them (-sk-idx) so we can find them
        String normalizedIndexName = createIndexName(collectionName);
        String result = this.client.ftCreate(normalizedIndexName,
                IndexOptions.defaultOptions().setDefinition(rule), schema);

        if (result.equals(OK)) {
            return Mono.just(true);
        }
        return null;
    }

    @Override
    public Mono<Collection<Tuple2<MemoryRecord, Float>>> getNearestMatchesAsync(
            @Nonnull String collectionName,
            @Nonnull Embedding embedding,
            int limit,
            float minRelevanceScore,
            boolean withEmbedding) {

        Objects.requireNonNull(collectionName);
        Objects.requireNonNull(embedding);

        if (limit <= 0) {
            return Mono.just(Collections.emptyList());
        }
        Query query = new Query("*=>[KNN $k @Embedding $vec AS vector_score]")
                .returnFields("Id", "Text", "Description", "vector_score")
                .setSortBy("vector_score", true)
                .addParam("k", limit)
                .addParam("vec", embeddingToBytes(embedding.getVector()))
                .limit(0, limit)
                .dialect(queryDialect);
        String indexName = createIndexName(collectionName);
        SearchResult results = this.client.ftSearch(indexName, query);

        // TODO convert to Collection<Tuple2<MemoryRecord, Float>>
        Collection<Tuple2<MemoryRecord, Float>> searchTuples =
            results.getDocuments().stream()
                .map(document -> {
                    MemoryRecord memoryRecord = documentToMemoryRecord(document, withEmbedding);
                    return Tuples.of(memoryRecord, document.getScore().floatValue());
                    })
                    .collect(Collectors.toList());
        return Mono.just(searchTuples);
    }

    @Override
    public Mono<Tuple2<MemoryRecord, Float>> getNearestMatchAsync(@Nonnull String collectionName,
        @Nonnull Embedding embedding, float minRelevanceScore, boolean withEmbedding) {
        return getNearestMatchesAsync(collectionName, embedding, 1, minRelevanceScore, withEmbedding)
            .flatMap(
                nearestMatches -> {
                    if (nearestMatches.isEmpty()) {
                        return Mono.empty();
                    }
                    return Mono.just(nearestMatches.iterator().next());
                });
    }

    /**
     * Convert the Azure List<Float> embedding structure to byte[] for storage in Redis
     *
     * @param embeddings the list of vectors returned by the model
     * @return byte[]
     */
    private byte[] embeddingToBytes(List<Float> embeddings) {
        ByteBuffer bytes = ByteBuffer.allocate(Float.BYTES * embeddings.size());
        bytes.order(ByteOrder.LITTLE_ENDIAN);
        embeddings.iterator().forEachRemaining(bytes::putFloat);
        return bytes.array();
    }

    private static OffsetDateTime ParseTimestamp(Long timestamp) {
        if (timestamp != null && timestamp > 0) {
            return OffsetDateTime.parse(timestamp.toString());
        }
        return null;
    }

    /**
     * Normalize an index name
     *
     * @param indexName Index name
     * @return A string to be used as the root of the index name; minus '-idx'
     */
    private static String normalizeCollectionName(String indexName) {
        if (indexName.length() > 128) {
            throw new IllegalArgumentException("The collection name cannot exceed 128 chars");
        }
        return indexName.toLowerCase(Locale.ROOT);
    }

    private static String createIndexName(String collectionName) {

        if (collectionName.length() > 128) {
            throw new IllegalArgumentException("The indexName name cannot exceed 128 chars");
        }
        return String.format("%s-%s-%s", normalizeCollectionName(collectionName), RedisMemoryStore.SUFFIX, INDEX);
    }

    protected Map<String, MemoryRecord> getCollection(@Nonnull String collectionName) {
        Objects.requireNonNull(collectionName);
        ScanResult<String> results = this.client.scan(collectionName);

        if (results == null) throw new MemoryException(
                ErrorCodes.ATTEMPTED_TO_ACCESS_NONEXISTENT_COLLECTION,
                collectionName);

        return Collections.unmodifiableMap((Map<String, MemoryRecord>) results.getResult().stream()
                .map(
                        key -> RedisMemoryRecord.mapToRecord(
                                this.client.hgetAll(String.format("%s:%s", collectionName, key)), false)
                ));
    }

    public static class Builder implements MemoryStore.Builder<RedisMemoryStore> {
        private String connectionString;
        private int vectorSize; // in theory determined by the model but can be overridden
        private VectorAlgorithm vectorIndexAlgorithm;
        private String vectorDistanceMetric;
        private int queryDialect = 0; // must best at least two for vector index

        public Builder connectionString(String connectionString) {
            this.connectionString = connectionString;
            return this;
        }
        public Builder vectorSize(int vectorSize) {
            this.vectorSize = vectorSize;
            return this;
        }
        public Builder vectorIndexAlgorithm(VectorAlgorithm vectorIndexAlgorithm) {
            this.vectorIndexAlgorithm = vectorIndexAlgorithm;
            return this;
        }
        public Builder vectorDistanceMetric(String vectorDistanceMetric) {
            this.vectorDistanceMetric = vectorDistanceMetric;
            return this;
        }

        public Builder queryDialect(int queryDialect) {
            this.queryDialect = queryDialect;
            return this;
        }

        @Override
        /*
         * Create a RedisMemoryStore using assigned values.
         *
         * @return A RedisMemoryStore object configured with the specified values
         */
        public RedisMemoryStore build() {

            // make sure everything we need has been set
            return new RedisMemoryStore(
                connectionString,
                vectorSize,
                vectorIndexAlgorithm,
                vectorDistanceMetric,
                (queryDialect >= 2 ? queryDialect : 2)
            );
        }

        /**
         * Create a RedisMemoryStore object using default settings; requires a valid connection string.
         *
         * @return A RedisMemoryStore object configured with default values
         */
        public RedisMemoryStore buildDefault() {
            return new RedisMemoryStore(
                connectionString,
                DefaultVectorSize,
                RedisMemoryStore.DefaultIndexAlgorithm,
                RedisMemoryStore.DefaultDistanceMetric,
                RedisMemoryStore.DefaultQueryDialect
            );
        }
    }
}

