// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.ai.embeddings;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.services.AIService;

import reactor.core.publisher.Mono;

import java.util.List;

/** Interface for text embedding generation services */
public interface EmbeddingGeneration<TValue, TEmbedding extends Number> extends AIService {
    /**
     * Generates a list of embeddings associated to the data
     *
     * @param data List of texts to generate embeddings for
     * @return List of embeddings of each data point
     */
    Mono<List<Embedding<TEmbedding>>> generateEmbeddingsAsync(List<TValue> data);

    interface Builder<TValue, TEmbedding extends Number> {
        EmbeddingGeneration<TValue, TEmbedding> build(OpenAIAsyncClient client, String modelId);
    }
}
