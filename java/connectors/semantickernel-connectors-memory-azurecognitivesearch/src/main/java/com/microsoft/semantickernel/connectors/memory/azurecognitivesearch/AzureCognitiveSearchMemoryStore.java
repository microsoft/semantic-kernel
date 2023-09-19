// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.azurecognitivesearch;

import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.TokenCredential;
import com.azure.core.http.rest.Response;
import com.azure.core.util.ClientOptions;
import com.azure.core.util.MetricsOptions;
import com.azure.core.util.TracingOptions;
import com.azure.search.documents.SearchAsyncClient;
import com.azure.search.documents.SearchDocument;
import com.azure.search.documents.indexes.SearchIndexAsyncClient;
import com.azure.search.documents.indexes.SearchIndexClientBuilder;
import com.azure.search.documents.indexes.models.HnswParameters;
import com.azure.search.documents.indexes.models.HnswVectorSearchAlgorithmConfiguration;
import com.azure.search.documents.indexes.models.LexicalAnalyzerName;
import com.azure.search.documents.indexes.models.SearchField;
import com.azure.search.documents.indexes.models.SearchFieldDataType;
import com.azure.search.documents.indexes.models.SearchIndex;
import com.azure.search.documents.indexes.models.VectorSearch;
import com.azure.search.documents.indexes.models.VectorSearchAlgorithmMetric;
import com.azure.search.documents.models.IndexDocumentsOptions;
import com.azure.search.documents.models.IndexingResult;
import com.azure.search.documents.models.SearchOptions;
import com.azure.search.documents.models.SearchQueryVector;
import com.microsoft.semantickernel.ai.embeddings.Embedding;
import com.microsoft.semantickernel.connectors.memory.azurecognitivesearch.AzureCognitiveSearchMemoryException.ErrorCodes;
import com.microsoft.semantickernel.memory.MemoryRecord;
import com.microsoft.semantickernel.memory.MemoryStore;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.Iterator;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;
import javax.annotation.Nonnull;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.util.function.Tuple2;
import reactor.util.function.Tuples;

/**
 * Semantic Memory implementation using Azure Cognitive Search. For more information about Azure
 * Cognitive Search {@see https://learn.microsoft.com/azure/search/search-what-is-azure-search}
 */
public class AzureCognitiveSearchMemoryStore implements MemoryStore {

    private static final String USER_AGENT = "Semantic-Kernel";
    private static final String SEARCH_CONFIG_NAME = "searchConfig";

    private final SearchIndexAsyncClient _adminClient;

    private final Map<String, SearchAsyncClient> _clientsByIndex = new ConcurrentHashMap<>();

    /// <summary>
    /// Create a new instance of memory storage using Azure Cognitive Search.
    /// </summary>
    /// <param name="endpoint">Azure Cognitive Search URI, e.g.
    // "https://contoso.search.windows.net"</param>
    /// <param name="apiKey">API Key</param>

    /**
     * Create a new instance of memory storage using Azure Cognitive Search.
     *
     * @param endpoint Azure Cognitive Search URI, e.g. "https://contoso.search.windows.net"
     * @param apiKey Azure API Key
     */
    public AzureCognitiveSearchMemoryStore(@Nonnull String endpoint, @Nonnull String apiKey) {
        this(
                new SearchIndexClientBuilder()
                        .endpoint(endpoint)
                        .credential(new AzureKeyCredential(apiKey))
                        .clientOptions(clientOptions())
                        .buildAsyncClient());
    }

    /**
     * Create a new instance of memory storage using Azure Cognitive Search.
     *
     * @param endpoint Azure Cognitive Search URI, e.g. "https://contoso.search.windows.net"
     * @param credentials Azure service credentials
     */
    public AzureCognitiveSearchMemoryStore(
            @Nonnull String endpoint, @Nonnull TokenCredential credentials) {
        this(
                new SearchIndexClientBuilder()
                        .endpoint(endpoint)
                        .credential(credentials)
                        .clientOptions(clientOptions())
                        .buildAsyncClient());
    }

    /**
     * Create a new instance of memory storage using Azure Cognitive Search.
     *
     * @param searchIndexAsyncClient the Azure search documents index client to use
     */
    public AzureCognitiveSearchMemoryStore(@Nonnull SearchIndexAsyncClient searchIndexAsyncClient) {
        this._adminClient = searchIndexAsyncClient;
    }

    @Override
    public Mono<Void> createCollectionAsync(@Nonnull String collectionName) {
        // Indexes are created when sending a record. The creation requires the size of the
        // embeddings.
        return Mono.empty();
    }

    @Override
    public Mono<List<String>> getCollectionsAsync() {
        return this.getIndexesAsync();
    }

    @Override
    public Mono<Boolean> doesCollectionExistAsync(@Nonnull String collectionName) {
        String normalizedIndexName = normalizeIndexName(collectionName);
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
        collectionName = normalizeIndexName(collectionName);
        return _adminClient.deleteIndex(collectionName);
    }

    @Override
    public Mono<String> upsertAsync(@Nonnull String collectionName, @Nonnull MemoryRecord record) {
        collectionName = normalizeIndexName(collectionName);
        return this.upsertRecordAsync(
                collectionName, AzureCognitiveSearchMemoryRecord.fromMemoryRecord(record));
    }

    @Override
    public Mono<Collection<String>> upsertBatchAsync(
            @Nonnull String collectionName, Collection<MemoryRecord> records) {
        if (records == null || records.isEmpty()) {
            return Mono.just(Collections.emptyList());
        }

        collectionName = normalizeIndexName(collectionName);
        List<AzureCognitiveSearchMemoryRecord> searchRecords =
                records.stream()
                        .map(AzureCognitiveSearchMemoryRecord::fromMemoryRecord)
                        .collect(Collectors.toList());
        return upsertBatchAsync(collectionName, searchRecords);
    }

    @Override
    public Mono<MemoryRecord> getAsync(
            @Nonnull String collectionName, @Nonnull String key, boolean withEmbedding) {
        collectionName = normalizeIndexName(collectionName);
        key = AzureCognitiveSearchMemoryRecord.encodeId(key);
        SearchAsyncClient client = this.getSearchClient(collectionName);

        return client.getDocumentWithResponse(key, AzureCognitiveSearchMemoryRecord.class, null)
                .map(
                        response -> {
                            if (response.getStatusCode() == 404) {
                                throw new AzureCognitiveSearchMemoryException(
                                        ErrorCodes.READ_FAILURE, "Index not found");
                            }
                            return response.getValue().toMemoryRecord(withEmbedding);
                        });
    }

    @Override
    public Mono<Collection<MemoryRecord>> getBatchAsync(
            @Nonnull String collectionName,
            @Nonnull Collection<String> keys,
            boolean withEmbedding) {
        // TODO: there _must_ be a better way than one request per key!
        return Flux.fromIterable(keys)
                .flatMap(key -> getAsync(collectionName, key, withEmbedding))
                .collect(Collectors.toList());
    }

    @Override
    public Mono<Tuple2<MemoryRecord, Float>> getNearestMatchAsync(
            @Nonnull String collectionName,
            @Nonnull Embedding embedding,
            float minRelevanceScore,
            boolean withEmbedding) {
        return getNearestMatchesAsync(
                        collectionName, embedding, 1, minRelevanceScore, withEmbedding)
                .map(matches -> matches.iterator().next());
    }

    @Override
    public Mono<Collection<Tuple2<MemoryRecord, Float>>> getNearestMatchesAsync(
            @Nonnull String collectionName,
            @Nonnull Embedding embedding,
            int limit,
            float minRelevanceScore,
            boolean withEmbedding) {
        collectionName = normalizeIndexName(collectionName);
        SearchAsyncClient client = getSearchClient(collectionName);

        SearchQueryVector searchVector =
                new SearchQueryVector()
                        .setKNearestNeighborsCount(limit)
                        .setFields(AzureCognitiveSearchMemoryRecord.EMBEDDING)
                        .setValue(embedding.getVector());

        SearchOptions searchOptions = new SearchOptions().setVectors(searchVector);

        return client.search(null, searchOptions)
                .filter(result -> (double) minRelevanceScore >= result.getScore())
                .map(
                        result -> {
                            MemoryRecord memoryRecord =
                                    result.getDocument(AzureCognitiveSearchMemoryRecord.class)
                                            .toMemoryRecord(withEmbedding);
                            float score = (float) result.getScore();
                            return Tuples.of(memoryRecord, score);
                        })
                .collect(Collectors.toList());
    }

    @Override
    public Mono<Void> removeAsync(@Nonnull String collectionName, @Nonnull String key) {
        return removeBatchAsync(collectionName, Collections.singleton(key));
    }

    @Override
    public Mono<Void> removeBatchAsync(
            @Nonnull String collectionName, @Nonnull Collection<String> keys) {
        collectionName = normalizeIndexName(collectionName);
        SearchAsyncClient client = this.getSearchClient(collectionName);

        List<SearchDocument> documents =
                keys.stream()
                        .map(AzureCognitiveSearchMemoryRecord::encodeId)
                        .map(
                                key -> {
                                    SearchDocument searchDocument = new SearchDocument();
                                    searchDocument.put("Id", key); // TODO: Id should be a constant
                                    return searchDocument;
                                })
                        .collect(Collectors.toList());

        return client.deleteDocuments(documents).then();
    }

    static List<SearchField> searchFields(String configName, int embeddingSize) {
        return Arrays.asList(
                new SearchField(AzureCognitiveSearchMemoryRecord.ID, SearchFieldDataType.STRING)
                        .setKey(true)
                        .setFilterable(false),
                new SearchField(
                                AzureCognitiveSearchMemoryRecord.EMBEDDING,
                                SearchFieldDataType.collection(SearchFieldDataType.SINGLE))
                        .setSearchable(true)
                        .setVectorSearchDimensions(embeddingSize)
                        .setVectorSearchConfiguration(configName),
                new SearchField(AzureCognitiveSearchMemoryRecord.TEXT, SearchFieldDataType.STRING)
                        .setSearchable(true)
                        .setFacetable(true)
                        .setAnalyzerName(LexicalAnalyzerName.EN_LUCENE),
                new SearchField(
                                AzureCognitiveSearchMemoryRecord.DESCRIPTION,
                                SearchFieldDataType.STRING)
                        .setSearchable(true)
                        .setFacetable(true)
                        .setAnalyzerName(LexicalAnalyzerName.EN_LUCENE),
                new SearchField(
                                AzureCognitiveSearchMemoryRecord.ADDITIONAL_METADATA,
                                SearchFieldDataType.STRING)
                        .setSearchable(true)
                        .setFacetable(true)
                        .setAnalyzerName(LexicalAnalyzerName.EN_LUCENE),
                new SearchField(
                                AzureCognitiveSearchMemoryRecord.EXTERNAL_SOURCE_NAME,
                                SearchFieldDataType.STRING)
                        .setSearchable(true)
                        .setFacetable(true)
                        .setAnalyzerName(LexicalAnalyzerName.EN_LUCENE),
                new SearchField(
                                AzureCognitiveSearchMemoryRecord.IS_REFERENCE,
                                SearchFieldDataType.BOOLEAN)
                        .setFilterable(true)
                        .setFacetable(true));
    }

    /**
     * Create a new search index.
     *
     * @param indexName Index name
     * @param embeddingSize Size of the embedding vector
     * @return A Mono that completes when the index is created
     */
    private Mono<Response<SearchIndex>> createIndexAsync(
            @Nonnull String indexName, int embeddingSize) {
        if (embeddingSize < 1) {
            throw new AzureCognitiveSearchMemoryException(
                    ErrorCodes.INVALID_EMBEDDING_SIZE, "the value must be greater than zero");
        }

        String normalizedIndexName = normalizeIndexName(indexName);

        VectorSearch vectorSearch =
                new VectorSearch()
                        .setAlgorithmConfigurations(
                                Collections.singletonList(
                                        new HnswVectorSearchAlgorithmConfiguration(
                                                        SEARCH_CONFIG_NAME)
                                                .setParameters(
                                                        new HnswParameters()
                                                                .setMetric(
                                                                        VectorSearchAlgorithmMetric
                                                                                .COSINE))));

        SearchIndex newIndex =
                new SearchIndex(normalizedIndexName)
                        .setFields(searchFields(SEARCH_CONFIG_NAME, embeddingSize))
                        .setVectorSearch(vectorSearch);

        return _adminClient.createIndexWithResponse(newIndex);
    }

    private Mono<List<String>> getIndexesAsync() {
        return _adminClient.listIndexes().map(SearchIndex::getName).collect(Collectors.toList());
    }

    private Mono<String> upsertRecordAsync(
            @Nonnull String indexName, @Nonnull AzureCognitiveSearchMemoryRecord record) {
        return upsertBatchAsync(indexName, Collections.singletonList(record))
                .map(Collection::iterator)
                .map(Iterator::next);
    }

    private Mono<Collection<String>> upsertBatchAsync(
            @Nonnull String indexName, @Nonnull List<AzureCognitiveSearchMemoryRecord> records) {

        if (records.isEmpty()) {
            return Mono.just(Collections.emptyList());
        }

        List<SearchDocument> documents =
                records.stream()
                        .map(
                                record -> {
                                    SearchDocument searchDocument = new SearchDocument();
                                    searchDocument.put(
                                            AzureCognitiveSearchMemoryRecord.ID,
                                            AzureCognitiveSearchMemoryRecord.encodeId(
                                                    record.getId()));
                                    searchDocument.put(
                                            AzureCognitiveSearchMemoryRecord.TEXT,
                                            record.getText());
                                    searchDocument.put(
                                            AzureCognitiveSearchMemoryRecord.DESCRIPTION,
                                            record.getDescription());
                                    searchDocument.put(
                                            AzureCognitiveSearchMemoryRecord.EMBEDDING,
                                            record.getEmbedding());
                                    searchDocument.put(
                                            AzureCognitiveSearchMemoryRecord.ADDITIONAL_METADATA,
                                            record.getAdditionalMetadata());
                                    searchDocument.put(
                                            AzureCognitiveSearchMemoryRecord.EXTERNAL_SOURCE_NAME,
                                            record.getExternalSourceName());
                                    searchDocument.put(
                                            AzureCognitiveSearchMemoryRecord.IS_REFERENCE,
                                            record.isReference());
                                    return searchDocument;
                                })
                        .collect(Collectors.toList());

        IndexDocumentsOptions options = new IndexDocumentsOptions().setThrowOnAnyError(true);

        int embeddingSize =
                records.stream()
                        .map(AzureCognitiveSearchMemoryRecord::getEmbedding)
                        .map(List::size)
                        .max(Integer::compareTo)
                        .orElse(0);

        String normalizedIndexName = normalizeIndexName(indexName);
        SearchAsyncClient client = this.getSearchClient(normalizedIndexName);

        return client.uploadDocumentsWithResponse(documents, options)
                .map(
                        response -> {
                            if (response.getStatusCode() == 404) {
                                throw new AzureCognitiveSearchMemoryException(
                                        ErrorCodes.INVALID_INDEX_NAME);
                            }
                            return response;
                        })
                .onErrorResume(
                        e ->
                                createIndexAsync(normalizedIndexName, embeddingSize)
                                        .then(
                                                client.uploadDocumentsWithResponse(
                                                        documents, options)))
                .map(
                        response ->
                                response.getValue().getResults().stream()
                                        .map(IndexingResult::getKey)
                                        .collect(Collectors.toList()));
    }

    /**
     * Get a search client for the index specified. Note: the index might not exist, but we avoid
     * checking everytime and the extra latency.
     *
     * @param indexName Index name
     * @return Search client ready to read/write
     */
    private SearchAsyncClient getSearchClient(@Nonnull String indexName) {
        String normalizedIndexName = normalizeIndexName(indexName);
        return _clientsByIndex.computeIfAbsent(
                normalizedIndexName, _adminClient::getSearchAsyncClient);
    }

    /// <summary>
    /// Options used by the Azure Cognitive Search client, e.g. User Agent.
    /// See also
    // https://github.com/Azure/azure-sdk-for-net/blob/main/sdk/core/Azure.Core/src/DiagnosticsOptions.cs
    /// </summary>
    private static ClientOptions clientOptions() {
        return new ClientOptions()
                .setTracingOptions(new TracingOptions())
                .setMetricsOptions(new MetricsOptions())
                .setApplicationId(USER_AGENT);
    }

    // Index names cannot contain special chars. We use this rule to replace a few common ones
    // with an underscore and reduce the chance of errors. If other special chars are used, we leave
    // it
    // to the service to throw an error.
    // Note:
    // - replacing chars introduces a small chance of conflicts, e.g. "the-user" and "the_user".
    // - we should consider whether making this optional and leave it to the developer to handle.
    //
    // Java 8 does not support \s for whitespace, so we have to list them all.
    private static final String whitespace = " |\\t|\\n|\\x0B|\\f|\\r";
    private static final String s_replaceIndexNameSymbolsRegex = "[" + whitespace + "|\\|/|.|_|:]";

    // Normalize index name to match ACS rules.
    // See https://learn.microsoft.com/en-us/rest/api/searchservice/Create-Index
    // The method doesn't handle all the error scenarios, leaving it to the service
    // to throw an error for edge cases not handled locally.
    // <param name="indexName">Value to normalize</param>
    // <returns>Normalized name</returns>
    private static String normalizeIndexName(String indexName) {
        if (indexName.length() > 128) {
            throw new IllegalArgumentException("The collection name cannot exceed 128 chars");
        }

        indexName = indexName.toLowerCase(Locale.ROOT);
        return indexName.replaceAll(s_replaceIndexNameSymbolsRegex, "-");
    }
}
