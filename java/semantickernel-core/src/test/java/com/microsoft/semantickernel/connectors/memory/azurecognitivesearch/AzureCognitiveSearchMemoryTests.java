// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.azurecognitivesearch;

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
import com.microsoft.semantickernel.builders.SKBuilders;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import reactor.core.publisher.Mono;

import java.nio.charset.StandardCharsets;
import java.util.List;

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

    // Kernel is real and configured with a real AzureCognitiveSearchMemory.
    // The HttpPipeline is mocked to return a mocked HttpResponse.
    // This mocked HttpPipeline is used when building the SearchIndexClient
    // for the AzureCognitiveSearchMemory.
    // A test sets the response body to a known value for verification.
    Kernel kernel;

    HttpResponse httpResponse= Mockito.mock(HttpResponse.class);

    @BeforeEach
    void setUp() {

        HttpHeaders httpHeaders = new HttpHeaders();
        httpHeaders.add("Content-Type", "application/json");
        Mockito.when(httpResponse.getHeaders())
                .thenReturn(httpHeaders);

        HttpPipeline pipeline = Mockito.mock(HttpPipeline.class);

        Tracer tracer = new NoOpTracer();
        Mockito.when(pipeline.getTracer())
                        .thenReturn(tracer);

        Mockito.when(pipeline.send(Mockito.any(HttpRequest.class), Mockito.any(Context.class)))
                .thenAnswer(invocation -> {
                    HttpRequest request = invocation.getArgument(0);
                    Mockito.when(httpResponse.getRequest())
                            .thenReturn(request);
                    return Mono.just(httpResponse);
                });

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

    @Test
    void AzureCognitiveSearchMemoryStoreShouldBeProperlyInitialized() {
        //Arrange
        Mockito.when(httpResponse.getBodyAsByteArray())
                .thenReturn(Mono.just(
                                "{\"value\": [{\"name\": \"fake-index1\"}]}"
                                        .getBytes(StandardCharsets.UTF_8)));
        Mockito.when(httpResponse.getStatusCode()).thenReturn(200);

        //Act
        //This call triggers a subsequent call to Azure Cognitive Search Memory store.
        List<String> collections = kernel.getMemory().getCollectionsAsync().block();

        //Assert
        assertTrue(collections.contains("fake-index1"));
    }

}
