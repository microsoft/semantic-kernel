// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.ai.openai.textembeddings;

import com.azure.ai.openai.models.EmbeddingItem;
import com.azure.ai.openai.models.Embeddings;
import com.azure.ai.openai.models.EmbeddingsOptions;
import com.microsoft.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.ai.embeddings.Embedding;
import com.microsoft.semantickernel.ai.embeddings.EmbeddingGeneration;
import com.microsoft.semantickernel.connectors.ai.openai.azuresdk.ClientBase;

import reactor.core.publisher.Mono;

import java.util.List;

public class OpenAITextEmbeddingGeneration extends ClientBase
        implements EmbeddingGeneration<String, Double> {

    public OpenAITextEmbeddingGeneration(OpenAIAsyncClient client, String modelId) {
        super(client, modelId);
    }

    @Override
    public Mono<List<Embedding<Double>>> generateEmbeddingsAsync(List<String> data) {
        return this.internalGenerateTextEmbeddingsAsync(data);
    }

    protected Mono<List<Embedding<Double>>> internalGenerateTextEmbeddingsAsync(List<String> data) {
        EmbeddingsOptions options = new EmbeddingsOptions(data).setModel(getModelId());

        return getClient()
                .getEmbeddings(getModelId(), options)
                .flatMapIterable(Embeddings::getData)
                .mapNotNull(EmbeddingItem::getEmbedding)
                .mapNotNull(Embedding::new)
                .collectList();
    }
}
