// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.ai.openai.textembeddings;

import com.microsoft.semantickernel.ai.embeddings.EmbeddingGeneration;
import com.microsoft.semantickernel.openai.clients.OpenAIAsyncClient;

public class OpenAITextEmbeddingGenerationBuilder
        implements EmbeddingGeneration.Builder<String, Double> {

    @Override
    public EmbeddingGeneration<String, Double> build(OpenAIAsyncClient client, String modelId) {
        return new OpenAITextEmbeddingGeneration(client, modelId);
    }
}
