// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.ai.openai.textembeddings;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.models.EmbeddingItem;
import com.azure.ai.openai.models.Embeddings;
import com.azure.ai.openai.models.EmbeddingsOptions;
import com.microsoft.semantickernel.ai.embeddings.Embedding;
import com.microsoft.semantickernel.ai.embeddings.EmbeddingGeneration;
import com.microsoft.semantickernel.connectors.ai.openai.azuresdk.ClientBase;
import java.util.List;
import java.util.stream.Collectors;
import reactor.core.publisher.Mono;

public class OpenAITextEmbeddingGeneration extends ClientBase
        implements EmbeddingGeneration<String> {

    public OpenAITextEmbeddingGeneration(OpenAIAsyncClient client, String modelId) {
        super(client, modelId);
    }

    @Override
    public Mono<List<Embedding>> generateEmbeddingsAsync(List<String> data) {
        return this.internalGenerateTextEmbeddingsAsync(data);
    }

    protected Mono<List<Embedding>> internalGenerateTextEmbeddingsAsync(List<String> data) {
        EmbeddingsOptions options =
                new EmbeddingsOptions(data).setModel(getModelId()).setUser("default");

        return getClient()
                .getEmbeddings(getModelId(), options)
                .flatMapIterable(Embeddings::getData)
                .mapNotNull(EmbeddingItem::getEmbedding)
                .map(
                        embedding ->
                                embedding.stream()
                                        .map(Double::floatValue)
                                        .collect(Collectors.toList()))
                .mapNotNull(Embedding::new)
                .collectList();
    }

    public static class Builder implements EmbeddingGeneration.Builder<String> {
        @Override
        public EmbeddingGeneration<String> build(OpenAIAsyncClient client, String modelId) {
            return new OpenAITextEmbeddingGeneration(client, modelId);
        }
    }
}
