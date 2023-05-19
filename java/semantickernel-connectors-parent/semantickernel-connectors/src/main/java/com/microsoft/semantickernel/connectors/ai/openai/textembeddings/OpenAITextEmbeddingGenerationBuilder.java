// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.ai.openai.textembeddings;

import com.microsoft.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.ai.embeddings.EmbeddingGeneration;

public class OpenAITextEmbeddingGenerationBuilder
        implements EmbeddingGeneration.Builder<String, Double> {

    @Override
    public EmbeddingGeneration<String, Double> build(OpenAIAsyncClient client, String modelId) {
        return new OpenAITextEmbeddingGeneration(client, modelId);
    }
}
