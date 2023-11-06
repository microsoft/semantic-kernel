// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.azurecognitivesearch;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.azure.core.http.HttpHeaders;
import com.azure.core.http.HttpPipeline;
import com.azure.core.http.HttpRequest;
import com.azure.core.http.HttpResponse;
import com.azure.core.http.rest.Response;
import com.azure.core.util.Context;
import com.azure.core.util.tracing.Tracer;
import com.azure.search.documents.SearchAsyncClient;
import com.azure.search.documents.SearchDocument;
import com.azure.search.documents.indexes.SearchIndexAsyncClient;
import com.azure.search.documents.models.SearchResult;
import com.azure.search.documents.util.SearchPagedFlux;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.ai.embeddings.Embedding;
import com.microsoft.semantickernel.ai.embeddings.EmbeddingGeneration;
import com.microsoft.semantickernel.memory.MemoryQueryResult;
import com.microsoft.semantickernel.memory.MemoryRecord;
import com.microsoft.semantickernel.memory.MemoryRecordMetadata;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Base64;
import java.util.List;
import java.util.function.Function;
import javax.annotation.Nullable;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.mockito.invocation.InvocationOnMock;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

class AzureCognitiveSearchMemoryTests {

    // com.azure.core.implementation.http.rest.RestProxyBase.RestProxyBase
    // expects a non-null tracer. There is a TracerProvider in the Azure SDK
    // that can be used to create a tracer, but it has some ceremony around
    // it. We create a simple no-op tracer instead.
    private static class NoOpTracer implements Tracer {

        @Override
        public Context start(String methodName, Context context) {
            return context;
        }

        @Override
        public void end(String errorMessage, Throwable throwable, Context context) {}

        @Override
        public void setAttribute(String key, String value, Context context) {}

        @Override
        public boolean isEnabled() {
            // we could also set a property to disable tracing, but this is simpler.
            return false;
        }
    }

    // Kernel is configured with a real AzureCognitiveSearchMemoryStore which is backed
    // by a mocked HttpPipeline. The HttpPipeline is mocked to return a mocked
    // HttpResponse whose body and status code are configured by the test.
    Kernel kernel;

    //
    // A test may generate more than one HttpRequest. This function
    // can be set in the test to return the appropriate response body
    // for each request.
    //
    // A good place to set a breakpoint for debugging exceptions in
    // deserializing the response body is:
    // com.azure.search.documents.implementation.util.MappingUtils#exceptionMapper
    //
    Function<HttpRequest, String> responseBody;

    //
    // A test may generate more than one HttpRequest. This function
    // can be set in the test to return the appropriate HTTP status
    // code for each request.
    //
    Function<HttpRequest, Integer> responseStatusCode;

    @BeforeEach
    void setUp() {
        kernel = buildKernel(null);
    }

    private Kernel buildKernel(
            @Nullable Function<SearchDocument, MemoryRecord> memoryRecordMapper) {
        SearchAsyncClient searchAsyncClient = Mockito.mock(SearchAsyncClient.class);
        SearchIndexAsyncClient searchIndexAsyncClient = Mockito.mock(SearchIndexAsyncClient.class);
        Response response = Mockito.mock(Response.class);
        AzureCognitiveSearchMemoryRecord azureCognitiveSearchMemoryRecord =
                Mockito.mock(AzureCognitiveSearchMemoryRecord.class);
        MemoryRecord memoryRecord = Mockito.mock(MemoryRecord.class);
        SearchPagedFlux searchPagedFlux = Mockito.mock(SearchPagedFlux.class);
        SearchResult searchResult = Mockito.mock(SearchResult.class);

        Mockito.when(searchResult.getDocument(Mockito.any())).thenReturn(new SearchDocument());
        Mockito.when(searchIndexAsyncClient.getSearchAsyncClient(Mockito.any()))
                .thenReturn(searchAsyncClient);

        Mockito.when(searchPagedFlux.filter(Mockito.any())).thenReturn(Flux.just(searchResult));

        Mockito.when(
                        searchAsyncClient.getDocumentWithResponse(
                                Mockito.any(), Mockito.any(), Mockito.any()))
                .thenReturn(Mono.just(response));

        Mockito.when(searchAsyncClient.search(Mockito.any(), Mockito.any()))
                .thenReturn(searchPagedFlux);
        Mockito.when(response.getValue()).thenReturn(azureCognitiveSearchMemoryRecord);
        Mockito.when(azureCognitiveSearchMemoryRecord.toMemoryRecord(Mockito.anyBoolean()))
                .thenReturn(memoryRecord);

        EmbeddingGeneration<String> embeddingGeneration =
                new EmbeddingGeneration<String>() {
                    /*
                    new SearchIndexClientBuilder()
                        .endpoint("https://fake-random-test-host/fake-path")
                        .credential(new AzureKeyCredential(apiKey))
                        .pipeline(pipeline)
                        .httpLogOptions(
                            new HttpLogOptions()
                                .setLogLevel(HttpLogDetailLevel.BODY_AND_HEADERS))
                        .buildAsyncClient();

                     */

                    List<Embedding> embeddings = new ArrayList<>();

                    {
                        embeddings.add(new Embedding(Arrays.asList(1.0f, 2.0f, 3.0f)));
                    }

                    @Override
                    public Mono<List<Embedding>> generateEmbeddingsAsync(List<String> data) {
                        return Mono.just(embeddings);
                    }
                };

        return SKBuilders.kernel()
                .withMemoryStorage(
                        new AzureCognitiveSearchMemoryStore(
                                searchIndexAsyncClient, memoryRecordMapper))
                .withDefaultAIService(embeddingGeneration)
                .build();
    }

    private HttpPipeline setUpHttpPipeline() {

        HttpPipeline pipeline = Mockito.mock(HttpPipeline.class);

        Tracer tracer = new NoOpTracer();
        Mockito.when(pipeline.getTracer()).thenReturn(tracer);

        Mockito.when(pipeline.send(Mockito.any(HttpRequest.class), Mockito.any(Context.class)))
                .thenAnswer(this::answerHttpRequest);

        return pipeline;
    }

    private Mono<HttpResponse> answerHttpRequest(InvocationOnMock invocation) {
        HttpRequest request = invocation.getArgument(0);

        String query = request.getUrl().getQuery();
        int offset = query.indexOf("api-version");
        assertTrue(offset >= 0);
        // HttpResponse is based on this api-version
        assertEquals("api-version=2023-07-01-Preview", query.substring(offset));

        //        System.err.println(request.getHttpMethod() + " " + request.getUrl() + "\n\t" +
        // request.getHeaders());
        byte[] body = responseBody.apply(request).getBytes(StandardCharsets.UTF_8);
        int statusCode = responseStatusCode.apply(request);
        HttpHeaders httpHeaders =
                new HttpHeaders().add("Content-Type", "application/json; charset=utf-8");

        HttpResponse httpResponse = Mockito.mock(HttpResponse.class);
        Mockito.when(httpResponse.getRequest()).thenReturn(request);
        Mockito.when(httpResponse.getHeaders()).thenReturn(httpHeaders);
        Mockito.when(httpResponse.getBodyAsByteArray()).thenReturn(Mono.just(body));
        Mockito.when(httpResponse.getStatusCode()).thenReturn(statusCode);
        return Mono.just(httpResponse);
    }

    @Disabled("Pending https://github.com/microsoft/semantic-kernel/issues/1797")
    @Test
    void azureCognitiveSearchMemoryStoreShouldBeProperlyInitialized() {
        // Arrange
        responseBody = httpRequest -> "{\"value\": [{\"name\": \"fake-index\"}]}";
        responseStatusCode = httpResponse -> 200;

        // Act
        // This call triggers a subsequent call to Azure Cognitive Search Memory store.
        List<String> collections = kernel.getMemory().getCollectionsAsync().block();

        // Assert
        assertTrue(collections.contains("fake-index"));
    }

    @Disabled("Pending https://github.com/microsoft/semantic-kernel/issues/1797")
    @Test
    void azureCognitiveSearchMemoryStoreCanSaveReferenceAsync() {
        // Arrange
        responseBody =
                httpRequest ->
                        "{\"value\": ["
                                + "    {"
                                + "      \"key\": \"fake-key\","
                                + "      \"status\": true,"
                                + "      \"errorMessage\": null,"
                                + "      \"statusCode\": 200"
                                + "    }"
                                + "  ]"
                                + "}";

        responseStatusCode = httpRequest -> 200;

        // Act
        String key =
                kernel.getMemory()
                        .saveReferenceAsync(
                                "fake-index",
                                "fake-text",
                                "fake-externalId",
                                "fake-externalSourceName",
                                "fake-description",
                                "fake-additionalMetadata")
                        .block();

        // Assert
        assertEquals("fake-key", key);
    }

    @Disabled("Pending https://github.com/microsoft/semantic-kernel/issues/1797")
    @Test
    void azureCognitiveSearchMemoryStoreCanSaveInformationAsync() {
        // Arrange
        responseBody =
                httpRequest ->
                        "{\"value\": ["
                                + "    {"
                                + "      \"key\": \"fake-key\","
                                + "      \"status\": true,"
                                + "      \"errorMessage\": null,"
                                + "      \"statusCode\": 200"
                                + "    }"
                                + "  ]"
                                + "}";

        responseStatusCode = httpRequest -> 200;

        // Act
        String key =
                kernel.getMemory()
                        .saveInformationAsync(
                                "fake-index",
                                "fake-text",
                                "fake-externalId",
                                "fake-description",
                                "fake-additionalMetadata")
                        .block();

        // Assert
        assertEquals("fake-key", key);
    }

    @Disabled("Pending https://github.com/microsoft/semantic-kernel/issues/1797")
    @Test
    void azureCognitiveSearchMemoryStoreGetAsync() {
        // Arrange
        String key = "fake-key";
        String base64EncodedKey =
                new String(
                        Base64.getUrlEncoder().encode("fake-key".getBytes(StandardCharsets.UTF_8)));

        responseBody =
                httpRequest ->
                        "{"
                                + "  \"Id\": \""
                                + base64EncodedKey
                                + "\","
                                + "  \"Text\": \"fake-text\","
                                + "  \"Description\": \"fake-description\","
                                + "  \"AdditionalMetadata\": \"fake-additionalmetadata\","
                                + "  \"ExternalSourceName\": \"fake-externalsourcename\","
                                + "  \"Reference\": false"
                                + "}";

        responseStatusCode = httpRequest -> 200;

        // Act
        MemoryQueryResult result = kernel.getMemory().getAsync("fake-index", key, false).block();

        // Assert
        assertEquals(key, result.getMetadata().getId());
    }

    @Disabled("Pending https://github.com/microsoft/semantic-kernel/issues/1797")
    @Test
    void azureCognitiveSearchMemoryStoreRemoveAsync() {
        // Arrange
        String key = "fake-key";
        String base64EncodedKey =
                new String(
                        Base64.getUrlEncoder().encode("fake-key".getBytes(StandardCharsets.UTF_8)));

        responseBody =
                httpRequest ->
                        "{\"value\": ["
                                + "    {"
                                + "      \"key\": \""
                                + base64EncodedKey
                                + "\","
                                + "      \"status\": true,"
                                + "      \"errorMessage\": null,"
                                + "      \"statusCode\": 200"
                                + "    }"
                                + "  ]"
                                + "}";
        ;

        responseStatusCode = httpRequest -> 200;

        // Act
        kernel.getMemory().removeAsync("fake-index", key).block();

        // Assert
    }

    @Disabled("Pending https://github.com/microsoft/semantic-kernel/issues/1797")
    @Test
    void azureCognitiveSearchMemoryStoreSearchAsync() {
        // Arrange
        String key = "fake-key";
        String base64EncodedKey =
                new String(
                        Base64.getUrlEncoder().encode("fake-key".getBytes(StandardCharsets.UTF_8)));

        responseBody =
                httpRequest ->
                        "{\"value\": ["
                                + "{"
                                + "  \"@search.score\": 1,"
                                + "  \"@search.highlights\": {"
                                + "    \"Text\": [\"It was a dark and stormy night\"]"
                                + "  },"
                                + "  \"@search.features\": {"
                                + "    \"Text\": {"
                                + "      \"uniqueTokenMatches\": 1,"
                                + "      \"similarityScore\": 0.8,"
                                + "      \"termFrequency\": 0.99"
                                + "    }"
                                + "  },"
                                + "  \"Id\": \""
                                + base64EncodedKey
                                + "\","
                                + "  \"Text\": \"fake-text\","
                                + "  \"Description\": \"fake-description\","
                                + "  \"AdditionalMetadata\": \"fake-additionalmetadata\","
                                + "  \"ExternalSourceName\": \"fake-externalsourcename\","
                                + "  \"Reference\": false"
                                + "}"
                                + "]}";

        responseStatusCode = httpRequest -> 200;

        // Act
        List<MemoryQueryResult> results =
                kernel.getMemory().searchAsync("fake-index", "fake-query", 1, 0.5f, false).block();

        // Assert
        assertEquals(1, results.size());
        assertEquals(key, results.get(0).getMetadata().getId());
    }

    @Test
    void azureCognitiveSearchMemoryStoreGetAsyncWithCustomMapping() {
        // Do not convert to lambda, it will break mockito
        Function<SearchDocument, MemoryRecord> transform =
                Mockito.spy(
                        new Function<SearchDocument, MemoryRecord>() {
                            @Override
                            public MemoryRecord apply(SearchDocument searchDocument) {
                                return new MemoryRecord(
                                        new MemoryRecordMetadata(
                                                false,
                                                "an-id",
                                                "fake-text",
                                                "fake-description",
                                                "fake-additionalmetadata",
                                                "fake-externalsourcename"),
                                        new Embedding(Arrays.asList(1.0f, 2.0f, 3.0f)),
                                        "an-id",
                                        null);
                            }
                        });

        kernel = buildKernel(transform);
        // Arrange
        String key = "fake-key";
        String base64EncodedKey =
                new String(
                        Base64.getUrlEncoder().encode("fake-key".getBytes(StandardCharsets.UTF_8)));

        responseBody =
                httpRequest ->
                        "{"
                                + "  \"Id\": \""
                                + base64EncodedKey
                                + "\","
                                + "  \"Text\": \"fake-text\","
                                + "  \"Description\": \"fake-description\","
                                + "  \"AdditionalMetadata\": \"fake-additionalmetadata\","
                                + "  \"ExternalSourceName\": \"fake-externalsourcename\","
                                + "  \"Reference\": false"
                                + "}";

        responseStatusCode = httpRequest -> 200;

        // Act
        kernel.getMemory().searchAsync("fake-index", "a-query", 1, 0.0f, false).block();

        Mockito.verify(transform, Mockito.atLeastOnce()).apply(Mockito.any());
    }
}
