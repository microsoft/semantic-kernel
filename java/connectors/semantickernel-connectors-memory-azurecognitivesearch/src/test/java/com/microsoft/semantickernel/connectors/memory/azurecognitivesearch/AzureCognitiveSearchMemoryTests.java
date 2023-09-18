// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.azurecognitivesearch;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.http.HttpHeaders;
import com.azure.core.http.HttpPipeline;
import com.azure.core.http.HttpRequest;
import com.azure.core.http.HttpResponse;
import com.azure.core.http.policy.HttpLogDetailLevel;
import com.azure.core.http.policy.HttpLogOptions;
import com.azure.core.util.Context;
import com.azure.core.util.tracing.Tracer;
import com.azure.search.documents.indexes.SearchIndexAsyncClient;
import com.azure.search.documents.indexes.SearchIndexClientBuilder;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.memory.MemoryQueryResult;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.List;
import java.util.function.Function;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.mockito.invocation.InvocationOnMock;
import reactor.core.publisher.Mono;

// TODO: This class is in the core package to avoid a
//       circular dependency with the connectors module.
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

        String apiKey = "fake-key";
        HttpPipeline pipeline = setUpHttpPipeline();

        SearchIndexAsyncClient searchIndexAsyncClient =
                new SearchIndexClientBuilder()
                        .endpoint("https://fake-random-test-host/fake-path")
                        .credential(new AzureKeyCredential(apiKey))
                        .pipeline(pipeline)
                        .httpLogOptions(
                                new HttpLogOptions()
                                        .setLogLevel(HttpLogDetailLevel.BODY_AND_HEADERS))
                        .buildAsyncClient();

        OpenAIAsyncClient openAIAsyncClient = Mockito.mock(OpenAIAsyncClient.class);

        kernel =
                SKBuilders.kernel()
                        .withMemoryStorage(
                                new AzureCognitiveSearchMemoryStore(
                                        searchIndexAsyncClient.getEndpoint(), apiKey))
                        .withDefaultAIService(
                                SKBuilders.textEmbeddingGeneration()
                                        .withOpenAIClient(openAIAsyncClient)
                                        .withModelId("fake-model-id")
                                        .build())
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

        // HttpResponse is based on this api-version
        assertTrue(request.getUrl().getQuery().contains("api-version=2021-04-30-Preview"));

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
                                "fake-exernalSourceName",
                                "fake-description",
                                "fake-additionalMetadata")
                        .block();

        // Assert
        assertEquals("fake-key", key);
    }

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
}
