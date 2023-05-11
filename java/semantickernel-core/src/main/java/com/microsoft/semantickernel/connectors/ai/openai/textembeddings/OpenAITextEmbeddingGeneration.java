// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.ai.openai.textembeddings;

import com.azure.ai.openai.models.EmbeddingItem;
import com.azure.ai.openai.models.Embeddings;
import com.azure.ai.openai.models.EmbeddingsOptions;
import com.microsoft.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.ai.embeddings.Embedding;
import com.microsoft.semantickernel.ai.embeddings.EmbeddingGeneration;
import com.microsoft.semantickernel.connectors.ai.openai.azuresdk.ClientBase;

import reactor.core.publisher.Flux;
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
        return Flux.fromIterable(data)
                .flatMap(
                        text -> {
                            EmbeddingsOptions options = null;

                            return getClient()
                                    .getEmbeddings(getModelId(), options)
                                    .flatMapIterable(Embeddings::getData)
                                    .elementAt(0)
                                    .mapNotNull(EmbeddingItem::getEmbedding)
                                    .mapNotNull(Embedding::new);
                        })
                .collectList();
    }
}
