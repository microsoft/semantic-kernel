package com.microsoft.semantickernel.connectors.memory.azurecognitivesearch;

import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.TokenCredential;
import com.azure.core.http.rest.Response;
import com.azure.core.util.Context;
import com.azure.search.documents.SearchClient;
import com.azure.search.documents.implementation.util.FieldBuilder;
import com.azure.search.documents.indexes.SearchIndexClient;
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
import com.azure.search.documents.util.SearchPagedIterable;
import com.microsoft.semantickernel.exceptions.NotSupportedException;
import com.microsoft.semantickernel.memory.MemoryQueryResult;
import com.microsoft.semantickernel.memory.MemoryRecordMetadata;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import reactor.core.publisher.Mono;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Base64;
import java.util.Collections;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.Callable;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;
import java.util.function.Function;
import java.util.stream.Collectors;

/**
 * Semantic Memory implementation using Azure Cognitive Search.
 * For more information about Azure Cognitive Search {@see https://learn.microsoft.com/azure/search/search-what-is-azure-search}
 */
public class AzureCognitiveSearchMemory implements SemanticTextMemory {

    private static final String EMPTY_STRING = "";

    private final SearchIndexClient _adminClient;

    private final ConcurrentMap<String, SearchClient> _clientsByIndex = new ConcurrentHashMap<>();

    // Create a new instance of semantic memory using Azure Cognitive Search.
    // <param name="endpoint">Azure Cognitive Search URI, e.g. "https://contoso.search.windows.net"</param>
    // <param name="apiKey">API Key</param>
    public AzureCognitiveSearchMemory(String endpoint, String apiKey) {
        AzureKeyCredential credentials = new AzureKeyCredential(apiKey);
        this._adminClient = new SearchIndexClientBuilder().endpoint(endpoint).credential(credentials).buildClient();
    }

    // Create a new instance of semantic memory using Azure Cognitive Search.
    // <param name="endpoint">Azure Cognitive Search URI, e.g. "https://contoso.search.windows.net"</param>
    // <param name="credentials">Azure service</param>
    public AzureCognitiveSearchMemory(String endpoint, TokenCredential credentials) {
        this._adminClient = new SearchIndexClientBuilder().endpoint(endpoint).credential(credentials).buildClient();
    }

    @Override
    public AzureCognitiveSearchMemory copy() {
        return new AzureCognitiveSearchMemory(this._adminClient);
    }

    private AzureCognitiveSearchMemory(SearchIndexClient adminClient) {
        this._adminClient = adminClient;
    }

    @Override
    public Mono<String> saveInformationAsync(@Nonnull String collection, @Nonnull String text, @Nonnull String id, @Nullable String description, @Nullable String additionalMetadata) {
        collection = normalizeIndexName(collection);

        AzureCognitiveSearchRecord record = new AzureCognitiveSearchRecord(
                encodeId(id),
                text,
                description,
                additionalMetadata,
                null,
                false
            );
        return this.upsertRecordAsync(collection, record);
    }

    @Override
    public Mono<String> saveReferenceAsync(@Nonnull String collection, @Nonnull String text, @Nonnull String externalId, @Nonnull String externalSourceName, @Nullable String description, @Nullable String additionalMetadata) {
        collection = normalizeIndexName(collection);

        AzureCognitiveSearchRecord record = new AzureCognitiveSearchRecord(
                encodeId(externalId),
                text,
                description,
                additionalMetadata,
                externalSourceName,
                false
        );
        return this.upsertRecordAsync(collection, record);
    }

    @Override
    public Mono<MemoryQueryResult> getAsync(@Nonnull String collection, @Nonnull String key, boolean withEmbedding) {

        SearchClient client = this.getSearchClient(normalizeIndexName(collection));

        // what to do...
        Callable<Response<AzureCognitiveSearchRecord>> callable =
                () -> client.getDocumentWithResponse(encodeId(key), AzureCognitiveSearchRecord.class, null, null);

        // how to handle the response...
        Function<Response<AzureCognitiveSearchRecord>, MemoryQueryResult> transform =
                (response) -> {
                    if (response.getStatusCode() == 404 || response.getValue() == null) {
                        throw new AzureCognitiveSearchMemoryException("Memory read returned null");
                    }
                    return new MemoryQueryResult(toMemoryRecordMetadata(response.getValue()), 1);
                };

        return Mono.fromCallable(callable).map(transform);
    }

    @Override
    public SemanticTextMemory merge(MemoryQueryResult b) {
        throw new NotSupportedException("Deprecated");
    }

    @Override
    public Mono<Void> removeAsync(@Nonnull String collection, @Nonnull String key) {
        SearchClient client = this.getSearchClient(normalizeIndexName(collection));

        List<AzureCognitiveSearchRecord> records = Collections.singletonList(
                new AzureCognitiveSearchRecord(encodeId(key), "", "", "", "", false)
        );

        return Mono.fromCallable(() -> client.deleteDocumentsWithResponse(records, null, null))
                // TODO: should we check the response?
                .then();
    }

    @Override
    public Mono<List<MemoryQueryResult>> searchAsync(@Nonnull String collection, @Nonnull String query, int limit, double minRelevanceScore, boolean withEmbeddings) {

        SearchClient client = this.getSearchClient(normalizeIndexName(collection));

        SearchOptions options = new SearchOptions()
                .setQueryType(QueryType.SEMANTIC)
                .setSemanticConfigurationName("default")
                .setQueryLanguage(QueryLanguage.EN_US)
                .setAnswersCount(limit);

        // what to do...
        Callable<SearchPagedIterable> callable =
                () -> client.search(query, options, Context.NONE);

        // how to handle the response...
        // return a list of results that have a score greater than the minimum relevance score.
        Function<SearchPagedIterable, List<MemoryQueryResult>> transform =
                (searchPagedIterable) -> {
                    // return a list of results that have a score greater than the minimum relevance score.
                    return
                            searchPagedIterable.getAnswers().stream()
                                    .filter(answerResult -> answerResult.getScore() >= minRelevanceScore)
                                    .map(answerResult -> {
                                        MemoryRecordMetadata metadata = new MemoryRecordMetadata(
                                                false,
                                                answerResult.getKey(),
                                                answerResult.getText(),
                                                EMPTY_STRING,
                                                EMPTY_STRING,
                                                EMPTY_STRING
                                        );
                                        return new MemoryQueryResult(metadata, answerResult.getScore());
                                    })
                                    .collect(Collectors.toList());
                };

        return Mono.fromCallable(callable).map(transform);
    }

    @Override
    public Mono<List<String>> getCollectionsAsync() {
        return Mono.fromCallable(() -> this._adminClient.listIndexes().stream().map(SearchIndex::getName).collect(Collectors.toList()));
    }


    // Index names cannot contain special chars. We use this rule to replace a few common ones
    // with an underscore and reduce the chance of errors. If other special chars are used, we leave it
    // to the service to throw an error.
    // Note:
    // - replacing chars introduces a small chance of conflicts, e.g. "the-user" and "the_user".
    // - we should consider whether making this optional and leave it to the developer to handle.
    //
    // Java 8 does not support \s for whitespace, so we have to list them all.
    private static String whitespace = " |\\t|\\n|\\x0B|\\f|\\r";
    private static String s_replaceIndexNameSymbolsRegex = "["+whitespace+"|\\|/|.|_|:]";

    // Get a search client for the index specified.
    // Note: the index might not exist, but we avoid checking everytime and the extra latency.
    // <param name="indexName">Index name</param>
    // <returns>Search client ready to read/write</returns>
    private SearchClient getSearchClient(String indexName) {
        // Search an available client from the local cache
        SearchClient client = _clientsByIndex.computeIfAbsent(indexName, k -> _adminClient.getSearchClient(indexName));
        return client;
    }

    // Create a new search index.
    // <param name="indexName">Index name</param>
    // <param name="cancellationToken">Task cancellation token</param>
    private Mono<SearchIndex> createIndexAsync(String indexName) {
        List<SearchField> fields =
                FieldBuilder.build(AzureCognitiveSearchRecord.class, null);
        SearchIndex newIndex = new SearchIndex(indexName, fields)
                .setSemanticSettings(new SemanticSettings()
                        .setConfigurations(
                                Collections.singletonList(
                                        new SemanticConfiguration("default", new PrioritizedFields()
                                                .setTitleField(new SemanticField().setFieldName("Description"))
                                                .setPrioritizedContentFields(
                                                        Arrays.asList(
                                                                new SemanticField().setFieldName("Text"),
                                                                new SemanticField().setFieldName("AdditionalMetadata")
                                                        )
                                                )
                                        )
                                )
                        )
                );

        return Mono.fromCallable(() -> this._adminClient.createIndex(newIndex));
    }

    @SuppressWarnings("unchecked")
    private Mono<String> upsertRecordAsync(String indexName, AzureCognitiveSearchRecord record) {
        SearchClient client = this.getSearchClient(indexName);
        IndexDocumentsOptions throwOnAnyError = new IndexDocumentsOptions().setThrowOnAnyError(true);

        Callable<Response<IndexDocumentsResult>> upsertCode =
                () -> client.mergeOrUploadDocumentsWithResponse(Collections.singleton(record), throwOnAnyError, Context.NONE);

        Function<Response<IndexDocumentsResult>, String> transform =
                (response) -> {
                    if (response.getStatusCode() == 404 || response.getValue().getResults().isEmpty()) {
                        throw new AzureCognitiveSearchMemoryException("Memory write returned null or an empty set");
                    }
                    return response.getValue().getResults().get(0).getKey();
                };


        return Mono.fromCallable(upsertCode)
                .map(response -> {
                    if (response.getStatusCode() == 404) {
                        return createIndexAsync(indexName).thenReturn(Mono.fromCallable(upsertCode));
                    }
                    return response;
                })
                .map(response -> transform.apply((Response<IndexDocumentsResult>) response));
    }

    private static MemoryRecordMetadata toMemoryRecordMetadata(AzureCognitiveSearchRecord data) {
        return new MemoryRecordMetadata(
                data.isReference(),
                decodeId(data.getId()),
                normalizeNullToEmptyString(data.getText()),
                normalizeNullToEmptyString(data.getDescription()),
                normalizeNullToEmptyString(data.getExternalSourceName()),
                normalizeNullToEmptyString(data.getAdditionalMetadata())
        );
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
            throw new AzureCognitiveSearchMemoryException("The collection name is too long, it cannot exceed 128 chars");
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
