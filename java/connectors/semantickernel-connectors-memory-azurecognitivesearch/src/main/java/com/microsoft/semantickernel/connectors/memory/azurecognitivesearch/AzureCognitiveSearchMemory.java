// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.azurecognitivesearch;

import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.TokenCredential;
import com.azure.core.http.rest.Response;
import com.azure.search.documents.SearchAsyncClient;
import com.azure.search.documents.indexes.SearchIndexAsyncClient;
import com.azure.search.documents.indexes.SearchIndexClientBuilder;
import com.azure.search.documents.indexes.models.PrioritizedFields;
import com.azure.search.documents.indexes.models.SearchField;
import com.azure.search.documents.indexes.models.SearchIndex;
import com.azure.search.documents.indexes.models.SemanticConfiguration;
import com.azure.search.documents.indexes.models.SemanticField;
import com.azure.search.documents.indexes.models.SemanticSettings;
import com.azure.search.documents.models.IndexDocumentsOptions;
import com.azure.search.documents.models.IndexDocumentsResult;
import com.azure.search.documents.models.QueryLanguage;
import com.azure.search.documents.models.QueryType;
import com.azure.search.documents.models.SearchOptions;
import com.azure.search.documents.util.SearchPagedResponse;
import com.microsoft.semantickernel.connectors.memory.azurecognitivesearch.AzureCognitiveSearchMemoryException.ErrorCodes;
import com.microsoft.semantickernel.memory.MemoryQueryResult;
import com.microsoft.semantickernel.memory.MemoryRecordMetadata;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Base64;
import java.util.Collections;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;
import java.util.function.Function;
import java.util.stream.Collector;
import java.util.stream.Collectors;
import javax.annotation.Nonnull;
import javax.annotation.Nullable;
import reactor.core.publisher.Mono;

/**
 * Semantic Memory implementation using Azure Cognitive Search. For more information about Azure
 * Cognitive Search {@see https://learn.microsoft.com/azure/search/search-what-is-azure-search}
 */
public class AzureCognitiveSearchMemory implements SemanticTextMemory {

    private static final String EMPTY_STRING = "";

    private final SearchIndexAsyncClient _adminClient;

    private final ConcurrentMap<String, SearchAsyncClient> _clientsByIndex =
            new ConcurrentHashMap<>();

    /**
     * Create a new instance of semantic memory using Azure Cognitive Search.
     *
     * @param endpoint Azure Cognitive Search URI, e.g. {@code "https://contoso.search.windows.net"}
     * @param apiKey The key used to authenticate HTTP requests sent to the Azure Cognitive Search
     *     service.
     */
    public AzureCognitiveSearchMemory(String endpoint, String apiKey) {
        AzureKeyCredential credentials = new AzureKeyCredential(apiKey);
        this._adminClient =
                new SearchIndexClientBuilder()
                        .endpoint(endpoint)
                        .credential(credentials)
                        .buildAsyncClient();
    }

    /**
     * Create a new instance of semantic memory using Azure Cognitive Search.
     *
     * @param endpoint Azure Cognitive Search URI, e.g. {@code "https://contoso.search.windows.net"}
     * @param credentials TokenCredential used to authorize requests sent to the Azure Cognitive
     *     Search service.
     */
    public AzureCognitiveSearchMemory(String endpoint, TokenCredential credentials) {
        this._adminClient =
                new SearchIndexClientBuilder()
                        .endpoint(endpoint)
                        .credential(credentials)
                        .buildAsyncClient();
    }

    AzureCognitiveSearchMemory(SearchIndexAsyncClient adminClient) {
        this._adminClient = adminClient;
    }

    @Override
    public AzureCognitiveSearchMemory copy() {
        return new AzureCognitiveSearchMemory(this._adminClient);
    }

    @Override
    public Mono<String> saveInformationAsync(
            @Nonnull String collection,
            @Nonnull String text,
            @Nonnull String id,
            @Nullable String description,
            @Nullable String additionalMetadata) {
        collection = normalizeIndexName(collection);

        AzureCognitiveSearchRecord record =
                new AzureCognitiveSearchRecord(
                        encodeId(id), text, description, additionalMetadata, null, false);
        return this.upsertRecordAsync(collection, record);
    }

    @Override
    public Mono<String> saveReferenceAsync(
            @Nonnull String collection,
            @Nonnull String text,
            @Nonnull String externalId,
            @Nonnull String externalSourceName,
            @Nullable String description,
            @Nullable String additionalMetadata) {
        collection = normalizeIndexName(collection);

        AzureCognitiveSearchRecord record =
                new AzureCognitiveSearchRecord(
                        encodeId(externalId),
                        text,
                        description,
                        additionalMetadata,
                        externalSourceName,
                        true);
        return this.upsertRecordAsync(collection, record);
    }

    @Override
    public Mono<MemoryQueryResult> getAsync(
            @Nonnull String collection, @Nonnull String key, boolean withEmbedding) {

        SearchAsyncClient client = this.getSearchClient(normalizeIndexName(collection));

        return client.getDocumentWithResponse(encodeId(key), AzureCognitiveSearchRecord.class, null)
                .map(
                        (response) -> {
                            if (response.getStatusCode() == 404 || response.getValue() == null) {
                                throw new AzureCognitiveSearchMemoryException(
                                    ErrorCodes.MEMORY_NOT_FOUND,
                                        "Memory read returned null");
                            }
                            return new MemoryQueryResult(
                                    toMemoryRecordMetadata(response.getValue()), 1);
                        });
    }

    @Override
    public Mono<Void> removeAsync(@Nonnull String collection, @Nonnull String key) {

        SearchAsyncClient client = this.getSearchClient(normalizeIndexName(collection));

        List<AzureCognitiveSearchRecord> records =
                Collections.singletonList(
                        new AzureCognitiveSearchRecord(encodeId(key), "", "", "", "", false));

        return client.deleteDocumentsWithResponse(records, null).then();
    }

    private Collector<SearchPagedResponse, ?, List<MemoryQueryResult>> toMemoryQueryResultList =
            Collector.of(
                    ArrayList::new,
                    (list, response) -> {
                        if (response.getStatusCode() == 404 || response.getValue() == null) {
                            throw new AzureCognitiveSearchMemoryException(
                                ErrorCodes.MEMORY_NOT_FOUND,
                                    "Memory read returned null");
                        }
                        response.getValue().stream()
                                .map(
                                        searchResult ->
                                                new MemoryQueryResult(
                                                        toMemoryRecordMetadata(
                                                                searchResult.getDocument(
                                                                        AzureCognitiveSearchRecord
                                                                                .class)),
                                                        searchResult.getScore()))
                                .forEach(list::add);
                    },
                    (left, right) -> {
                        left.addAll(right);
                        return left;
                    });

    @Override
    public Mono<List<MemoryQueryResult>> searchAsync(
            @Nonnull String collection,
            @Nonnull String query,
            int limit,
            double minRelevanceScore,
            boolean withEmbeddings) {

        SearchAsyncClient client = this.getSearchClient(normalizeIndexName(collection));

        SearchOptions options =
                new SearchOptions()
                        .setQueryType(QueryType.SEMANTIC)
                        .setSemanticConfigurationName("default")
                        .setQueryLanguage(QueryLanguage.EN_US)
                        .setAnswersCount(limit);

        return client.search(query, options).byPage().collect(toMemoryQueryResultList);
    }

    @Override
    public Mono<List<String>> getCollectionsAsync() {
        return this._adminClient
                .listIndexes()
                .map(SearchIndex::getName)
                .collect(Collectors.toList());
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
    private static String whitespace = " |\\t|\\n|\\x0B|\\f|\\r";
    private static String s_replaceIndexNameSymbolsRegex = "[" + whitespace + "|\\|/|.|_|:]";

    // Get a search client for the index specified.
    // Note: the index might not exist, but we avoid checking everytime and the extra latency.
    // <param name="indexName">Index name</param>
    // <returns>Search client ready to read/write</returns>
    private SearchAsyncClient getSearchClient(String indexName) {
        // Search an available client from the local cache
        String normalizeIndexName = normalizeIndexName(indexName);
        return _clientsByIndex.computeIfAbsent(
                indexName, k -> _adminClient.getSearchAsyncClient(normalizeIndexName));
    }

    // Create a new search index.
    // <param name="indexName">Index name</param>
    // <param name="cancellationToken">Task cancellation token</param>
    //    private Mono<SearchIndex> createIndexAsync(String indexName) {
    private Mono<SearchIndex> createIndexAsync(String indexName) {

        indexName = normalizeIndexName(indexName);

        // TODO: Use FieldBuilder pending resolution of
        //  https://github.com/Azure/azure-sdk-for-java/issues/35584
        // List<SearchField> fields =
        //        FieldBuilder.build(AzureCognitiveSearchRecord.class, null);
        List<SearchField> fields = AzureCognitiveSearchRecord.searchFields();

        SemanticField titleField = new SemanticField().setFieldName("Description");

        List<SemanticField> prioritizedContentFields =
                Arrays.asList(
                        new SemanticField().setFieldName("Text"),
                        new SemanticField().setFieldName("AdditionalMetadata"));

        PrioritizedFields prioritizedFields =
                new PrioritizedFields()
                        .setTitleField(titleField)
                        .setPrioritizedContentFields(prioritizedContentFields);

        SemanticConfiguration semanticConfiguration =
                new SemanticConfiguration("default", prioritizedFields);

        SemanticSettings semanticSettings =
                new SemanticSettings()
                        .setConfigurations(Collections.singletonList(semanticConfiguration));

        SearchIndex newIndex =
                new SearchIndex(indexName, fields).setSemanticSettings(semanticSettings);

        return this._adminClient.createIndex(newIndex);
    }

    @SuppressWarnings("unchecked")
    private Mono<String> upsertRecordAsync(String indexName, AzureCognitiveSearchRecord record) {
        SearchAsyncClient client = this.getSearchClient(indexName);
        IndexDocumentsOptions throwOnAnyError =
                new IndexDocumentsOptions().setThrowOnAnyError(true);

        Function<Response<IndexDocumentsResult>, String> transform =
                (response) -> {
                    if (response.getStatusCode() == 404
                            || response.getValue() == null
                            || response.getValue().getResults() == null
                            || response.getValue().getResults().isEmpty()) {
                        throw new AzureCognitiveSearchMemoryException(
                            ErrorCodes.MEMORY_NOT_FOUND,
                                "Memory write returned null or an empty set");
                    }
                    return response.getValue().getResults().get(0).getKey();
                };

        return client.mergeOrUploadDocumentsWithResponse(
                        Collections.singleton(record), throwOnAnyError)
                .map(transform)
                .onErrorResume(
                        e ->
                                createIndexAsync(indexName)
                                        .then(
                                                client.mergeOrUploadDocumentsWithResponse(
                                                        Collections.singleton(record),
                                                        throwOnAnyError))
                                        .map(transform));
    }

    private static MemoryRecordMetadata toMemoryRecordMetadata(AzureCognitiveSearchRecord data) {
        return new MemoryRecordMetadata(
                data.isReference(),
                decodeId(data.getId()),
                normalizeNullToEmptyString(data.getText()),
                normalizeNullToEmptyString(data.getDescription()),
                normalizeNullToEmptyString(data.getExternalSourceName()),
                normalizeNullToEmptyString(data.getAdditionalMetadata()));
    }

    private static String normalizeNullToEmptyString(@Nullable String value) {
        return value != null ? value : EMPTY_STRING;
    }

    // Normalize index name to match ACS rules.
    // The method doesn't handle all the error scenarios, leaving it to the service
    // to throw an error for edge cases not handled locally.
    // <param name="indexName">Value to normalize</param>
    // <returns>Normalized name</returns>
    private static String normalizeIndexName(String indexName) {
        if (indexName.length() > 128) {
            throw new AzureCognitiveSearchMemoryException(
                ErrorCodes.INVALID_INDEX_NAME,
                    "The collection name cannot exceed 128 chars");
        }

        indexName = indexName.toLowerCase(Locale.ROOT);
        return indexName.replaceAll(s_replaceIndexNameSymbolsRegex, "-");
    }

    // ACS keys can contain only letters, digits, underscore, dash, equal sign, recommending
    // to encode values with a URL-safe algorithm.
    // <param name="realId">Original Id</param>
    // <returns>Encoded id</returns>
    private static String encodeId(@Nullable String realId) {
        if (realId == null) {
            return EMPTY_STRING;
        }
        byte[] bytes = Base64.getUrlEncoder().encode(realId.getBytes(StandardCharsets.UTF_8));
        return new String(bytes, StandardCharsets.UTF_8);
    }

    private static String decodeId(@Nullable String encodedId) {
        if (encodedId == null) {
            return EMPTY_STRING;
        }
        byte[] bytes = Base64.getUrlDecoder().decode(encodedId.getBytes(StandardCharsets.UTF_8));
        return new String(bytes, StandardCharsets.UTF_8);
    }
}
