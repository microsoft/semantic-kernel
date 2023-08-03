// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.models.EmbeddingItem;
import com.azure.ai.openai.models.Embeddings;
import com.microsoft.semantickernel.ai.embeddings.EmbeddingGeneration;
import com.microsoft.semantickernel.connectors.ai.openai.textembeddings.OpenAITextEmbeddingGeneration;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

import reactor.core.publisher.Mono;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class TextEmbeddingsTest {

    private static OpenAIAsyncClient mockEmbeddingOpenAIAsyncClient() {
        OpenAIAsyncClient openAIAsyncClient = Mockito.mock(OpenAIAsyncClient.class);
        Embeddings embeddings = Mockito.mock(Embeddings.class);
        EmbeddingItem embeddingItem = Mockito.mock(EmbeddingItem.class);

        Mockito.when(embeddingItem.getEmbedding()).thenReturn(Collections.singletonList(1.0));

        Mockito.when(embeddings.getData()).thenReturn(Collections.singletonList(embeddingItem));

        Mockito.when(
                        openAIAsyncClient.getEmbeddings(
                                Mockito.any(String.class),
                                Mockito.argThat(
                                        it ->
                                                it != null
                                                        && it.getModel()
                                                                .equals("text-embedding-ada-002"))))
                .thenReturn(Mono.just(embeddings));

        return openAIAsyncClient;
    }

    @Test
    public void testEmbedding() {
        testEmbeddingGeneration(mockEmbeddingOpenAIAsyncClient(), 1);
    }

    public void testEmbeddingGeneration(OpenAIAsyncClient client, int expectedEmbeddingSize) {
        String model = "text-embedding-ada-002";
        EmbeddingGeneration<String> embeddingGeneration =
                new OpenAITextEmbeddingGeneration(client, model);

        List<String> data = new ArrayList<>();
        data.add("This is just");
        data.add("a test");

        embeddingGeneration
                .generateEmbeddingsAsync(data)
                .block()
                .forEach(
                        embedding -> {
                            Assertions.assertEquals(
                                    expectedEmbeddingSize, embedding.getVector().size());
                        });
    }
}
