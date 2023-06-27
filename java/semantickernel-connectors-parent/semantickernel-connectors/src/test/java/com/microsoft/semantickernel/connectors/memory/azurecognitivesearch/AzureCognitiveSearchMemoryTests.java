// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.memory.azurecognitivesearch;

import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.http.HttpClient;
import com.azure.core.http.HttpRequest;
import com.azure.core.http.HttpResponse;
import com.azure.search.documents.indexes.SearchIndexAsyncClient;
import com.azure.search.documents.indexes.SearchIndexClientBuilder;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.SKBuilders;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertTrue;

public class AzureCognitiveSearchMemoryTests
{

    SearchIndexAsyncClient searchIndexAsyncClient;
    HttpResponse httpResponse;

    @BeforeEach
    void setUp() {
        httpResponse = Mockito.mock(HttpResponse.class);

        HttpClient httpClient = Mockito.mock(HttpClient.class);
        Mockito.when(httpClient.send(Mockito.any(HttpRequest.class))
                .thenReturn(Mono.just(httpResponse)));

        searchIndexAsyncClient = new SearchIndexClientBuilder()
                .endpoint("https://fake-random-test-host/fake-path")
                .credential(new AzureKeyCredential("fake-key"))
                .httpClient(httpClient)
                .buildAsyncClient();
    }

    @Test @Disabled
    void AzureCognitiveSearchMemoryStoreShouldBeProperlyInitialized() {
        //Arrange
        Mockito.when(httpResponse.getBody())
                .thenReturn(Flux.just(
                        ByteBuffer.wrap(
                                "{\"value\": [{\"name\": \"fake-index1\"}]}"
                                        .getBytes(StandardCharsets.UTF_8))));
        Mockito.when(httpResponse.getStatusCode()).thenReturn(200);

        Kernel kernel = SKBuilders.kernel()
            .withMemory(new AzureCognitiveSearchMemory(searchIndexAsyncClient))
            .build();
    //Act
    //This call triggers a subsequent call to Azure Cognitive Search Memory store.
    List<String> collections = kernel.getMemory().getCollectionsAsync().block();

    //Assert
//    assertEquals("https://fake-random-test-host/fake-path/indexes?$select=%2A&api-version=2021-04-30-Preview"), this.messageHandlerStub?.RequestUri?.AbsoluteUri);

//    var headerValues = Enumerable.Empty<string>();
//    var headerExists = this.messageHandlerStub?.RequestHeaders?.TryGetValues("Api-Key", out headerValues);
//    Assert.True(headerExists);
    assertTrue(collections.contains("fake-index1"));
}

}
