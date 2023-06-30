// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.azurecognitivesearch;

import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.http.HttpHeaders;
import com.azure.core.http.HttpMethod;
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
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.memory.MemoryQueryResult;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.mockito.invocation.InvocationOnMock;
import org.mockito.stubbing.Answer;
import reactor.core.publisher.Mono;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.List;
import java.util.function.BiFunction;
import java.util.function.Function;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

// TODO: This class is in the core package to avoid a
//       circular dependency with the connectors module.
class AzureCognitiveSearchMemoryTests
{

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
        public void end(String errorMessage, Throwable throwable, Context context) {
        }

        @Override
        public void setAttribute(String key, String value, Context context) {
        }

        @Override
        public boolean isEnabled() {
            // we could also set a property to disable tracing, but this is simpler.
            return false;
        }
    }


    // Kernel is configured with a real AzureCognitiveSearchMemory which is backed
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

        HttpPipeline pipeline = setUpHttpPipeline();

        SearchIndexAsyncClient searchIndexAsyncClient = new SearchIndexClientBuilder()
                .endpoint("https://fake-random-test-host/fake-path")
                .credential(new AzureKeyCredential("fake-key"))
                .pipeline(pipeline)
                .httpLogOptions(new HttpLogOptions().setLogLevel(HttpLogDetailLevel.BODY_AND_HEADERS))
                .buildAsyncClient();

        kernel = SKBuilders.kernel()
                .setKernelConfig(SKBuilders.kernelConfig().build())
                .withMemory(new AzureCognitiveSearchMemory(searchIndexAsyncClient))
                .build();

    }
    
    private HttpPipeline setUpHttpPipeline() {

        HttpPipeline pipeline = Mockito.mock(HttpPipeline.class);

        Tracer tracer = new NoOpTracer();
        Mockito.when(pipeline.getTracer())
                .thenReturn(tracer);

        Mockito.when(pipeline.send(Mockito.any(HttpRequest.class), Mockito.any(Context.class)))
                .thenAnswer(this::answerHttpRequest);

        return pipeline;
    }

    private Mono<HttpResponse> answerHttpRequest(InvocationOnMock invocation) {
        HttpRequest request = invocation.getArgument(0);

        // HttpResponse is based on this api-version
        assertTrue(request.getUrl().getQuery().contains("api-version=2021-04-30-Preview"));

        System.err.println(request.getHttpMethod() + " " + request.getUrl() + "\n\t" + request.getHeaders());
        byte[] body = responseBody.apply(request).getBytes(StandardCharsets.UTF_8);
        int statusCode = responseStatusCode.apply(request);
        HttpHeaders httpHeaders = new HttpHeaders().add("Content-Type", "application/json; charset=utf-8");

        HttpResponse httpResponse= Mockito.mock(HttpResponse.class);
        Mockito.when(httpResponse.getRequest()).thenReturn(request);
        Mockito.when(httpResponse.getHeaders()).thenReturn(httpHeaders);
        Mockito.when(httpResponse.getBodyAsByteArray()).thenReturn(Mono.just(body));
        Mockito.when(httpResponse.getStatusCode()).thenReturn(statusCode);
        return Mono.just(httpResponse);
    }

    @Test
    void azureCognitiveSearchMemoryStoreShouldBeProperlyInitialized() {
        //Arrange
        responseBody = httpRequest -> "{\"value\": [{\"name\": \"fake-index\"}]}";
        responseStatusCode = httpResponse -> 200;

        //Act
        //This call triggers a subsequent call to Azure Cognitive Search Memory store.
        List<String> collections = kernel.getMemory().getCollectionsAsync().block();

        //Assert
        assertTrue(collections.contains("fake-index"));
    }

    @Test
    void azureCognitiveSearchMemoryStoreCanSaveReferenceAsync() {
        //Arrange
        responseBody = httpRequest ->
                "{\"value\": [" +
                        "    {" +
                        "      \"key\": \"fake-key\"," +
                        "      \"status\": true," +
                        "      \"errorMessage\": null," +
                        "      \"statusCode\": 200" +
                        "    }" +
                        "  ]" +
                        "}";

        responseStatusCode = httpRequest -> 200;

        //Act
        String key = kernel.getMemory()
                .saveReferenceAsync(
                        "fake-index",
                        "fake-text",
                        "fake-externalId",
                        "fake-exernalSourceName",
                        "fake-description",
                        "fake-additionalMetadata")
                .block();

        //Assert
        assertEquals("fake-key", key);
    }

    @Test
    void azureCognitiveSearchMemoryStoreCanSaveInformationAsync() {
        //Arrange
        responseBody = httpRequest ->
                "{\"value\": [" +
                        "    {" +
                        "      \"key\": \"fake-key\"," +
                        "      \"status\": true," +
                        "      \"errorMessage\": null," +
                        "      \"statusCode\": 200" +
                        "    }" +
                        "  ]" +
                        "}";

        responseStatusCode = httpRequest -> 200;

        //Act
        String key = kernel.getMemory()
                .saveInformationAsync(
                        "fake-index",
                        "fake-text",
                        "fake-externalId",
                        "fake-description",
                        "fake-additionalMetadata")
                .block();

        //Assert
        assertEquals("fake-key", key);
    }

    @Test
    void azureCognitiveSearchMemoryStoreGetAsync() {
        //Arrange
        String key = "fake-key";
        String base64EncodedKey = new String(Base64.getUrlEncoder().encode("fake-key".getBytes(StandardCharsets.UTF_8)));

        responseBody = httpRequest ->
                "{" +
                "  \"Id\": \"" + base64EncodedKey + "\"," +
                "  \"Text\": \"fake-text\"," +
                "  \"Description\": \"fake-description\"," +
                "  \"AdditionalMetadata\": \"fake-additionalmetadata\"," +
                "  \"ExternalSourceName\": \"fake-externalsourcename\"," +
                "  \"Reference\": false" +
                "}";

        responseStatusCode = httpRequest -> 200;

        //Act
        MemoryQueryResult result = kernel.getMemory()
                .getAsync(
                        "fake-index",
                        key,
                        false)
                .block();

        //Assert
        assertEquals(key, result.getMetadata().getId());
    }

    @Test
    void azureCognitiveSearchMemoryStoreRemoveAsync() {
        //Arrange
        String key = "fake-key";
        String base64EncodedKey = new String(Base64.getUrlEncoder().encode("fake-key".getBytes(StandardCharsets.UTF_8)));

        responseBody = httpRequest ->
                "{\"value\": [" +
                        "    {" +
                        "      \"key\": \"" + base64EncodedKey + "\"," +
                        "      \"status\": true," +
                        "      \"errorMessage\": null," +
                        "      \"statusCode\": 200" +
                        "    }" +
                        "  ]" +
                        "}";;

        responseStatusCode = httpRequest -> 200;

        //Act
        kernel.getMemory()
                .removeAsync(
                        "fake-index",
                        key)
                .block();

        //Assert
    }
    
    //{
    //    "@odata.count": # (if $count=true was provided in the query),
    //    "@search.coverage": # (if minimumCoverage was provided in the query),
    //    "@search.facets": { (if faceting was specified in the query)
    //      "facet_field": [
    //        {
    //          "value": facet_entry_value (for non-range facets),
    //          "from": facet_entry_value (for range facets),
    //          "to": facet_entry_value (for range facets),
    //          "count": number_of_documents
    //        }
    //      ],
    //      ...
    //    },
    //    "@search.nextPageParameters": { (request body to fetch the next page of results if not all results could be returned in this response and Search was called with POST)
    //      "count": ... (value from request body if present),
    //      "facets": ... (value from request body if present),
    //      "filter": ... (value from request body if present),
    //      "highlight": ... (value from request body if present),
    //      "highlightPreTag": ... (value from request body if present),
    //      "highlightPostTag": ... (value from request body if present),
    //      "minimumCoverage": ... (value from request body if present),
    //      "orderby": ... (value from request body if present),
    //      "scoringParameters": ... (value from request body if present),
    //      "scoringProfile": ... (value from request body if present),
    //      "scoringStatistics": ... (value from request body if present),
    //      "search": ... (value from request body if present),
    //      "searchFields": ... (value from request body if present),
    //      "searchMode": ... (value from request body if present),
    //      "select": ... (value from request body if present),
    //      "sessionId" : ... (value from request body if present),
    //      "skip": ... (page size plus value from request body if present),
    //      "top": ... (value from request body if present minus page size),
    //    },
    //    "value": [
    //      {
    //        "@search.score": document_score (if a text query was provided),
    //        "@search.highlights": {
    //          field_name: [ subset of text, ... ],
    //          ...
    //        },
    //        "@search.features": {
    //          "field_name": {
    //            "uniqueTokenMatches": feature_score,
    //            "similarityScore": feature_score,
    //            "termFrequency": feature_score,
    //          },
    //          ...
    //        },
    //        key_field_name: document_key,
    //        field_name: field_value (retrievable fields or specified projection),
    //        ...
    //      },
    //      ...
    //    ],
    //    "@odata.nextLink": (URL to fetch the next page of results if not all results could be returned in this response; Applies to both GET and POST)
    //  }
    @Test
    void azureCognitiveSearchMemoryStoreSearchAsync() {
        //Arrange
        String key = "fake-key";
        String base64EncodedKey = new String(Base64.getUrlEncoder().encode("fake-key".getBytes(StandardCharsets.UTF_8)));

        responseBody = httpRequest ->
                "{\"value\": [" +
                        "{" +
                        "  \"@search.score\": 1," +
                        "  \"@search.highlights\": {" +
                        "    \"Text\": [\"It was a dark and stormy night\"]" +
                        "  }," +
                        "  \"@search.features\": {" +
                        "    \"Text\": {" +
                        "      \"uniqueTokenMatches\": 1," +
                        "      \"similarityScore\": 0.8," +
                        "      \"termFrequency\": 0.99" +
                        "    }"+
                        "  }," +
                        "  \"Id\": \"" + base64EncodedKey + "\"," +
                        "  \"Text\": \"fake-text\"," +
                        "  \"Description\": \"fake-description\"," +
                        "  \"AdditionalMetadata\": \"fake-additionalmetadata\"," +
                        "  \"ExternalSourceName\": \"fake-externalsourcename\"," +
                        "  \"Reference\": false" +
                        "}" +
                        "]}";

        responseStatusCode = httpRequest -> 200;

        //Act
        List<MemoryQueryResult> results = kernel.getMemory()
                .searchAsync(
                        "fake-index",
                        "fake-query",
                        1,
                        0.5,
                        false)
                .block();

        //Assert
        assertEquals(1, results.size());
        assertEquals(key, results.get(0).getMetadata().getId());
    }
}
