// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.ai.embeddings;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;
import com.microsoft.semantickernel.services.AIService;
import java.util.List;
import reactor.core.publisher.Mono;

/** Interface for text embedding generation services */
public interface EmbeddingGeneration<TValue> extends AIService, Buildable {
    /**
     * Generates a list of embeddings associated to the data
     *
     * @param data List of texts to generate embeddings for
     * @return List of embeddings of each data point
     */
    Mono<List<Embedding>> generateEmbeddingsAsync(List<TValue> data);

    interface Builder<T, E extends EmbeddingGeneration<T>> extends SemanticKernelBuilder<E> {

        Builder<T, E> withOpenAIClient(OpenAIAsyncClient client);

        Builder<T, E> withModelId(String modelId);
    }
}
