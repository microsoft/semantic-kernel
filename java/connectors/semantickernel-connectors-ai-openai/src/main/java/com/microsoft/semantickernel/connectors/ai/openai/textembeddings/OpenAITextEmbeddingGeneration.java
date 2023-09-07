// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.ai.openai.textembeddings;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.models.EmbeddingItem;
import com.azure.ai.openai.models.Embeddings;
import com.azure.ai.openai.models.EmbeddingsOptions;
import com.microsoft.semantickernel.ai.embeddings.Embedding;
import com.microsoft.semantickernel.ai.embeddings.TextEmbeddingGeneration;
import com.microsoft.semantickernel.connectors.ai.openai.azuresdk.ClientBase;
import com.microsoft.semantickernel.exceptions.NotSupportedException;
import com.microsoft.semantickernel.exceptions.NotSupportedException.ErrorCodes;
import java.util.List;
import java.util.stream.Collectors;
import reactor.core.publisher.Mono;

public class OpenAITextEmbeddingGeneration extends ClientBase
        implements TextEmbeddingGeneration {

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

    public static class Builder implements TextEmbeddingGeneration.Builder {
        private OpenAIAsyncClient client;
        private String modelId;

        public Builder withOpenAIClient(OpenAIAsyncClient client) {
            this.client = client;
            return this;
        }

        public Builder withModelId(String modelId) {
            this.modelId = modelId;
            return this;
        }

        @Override
        public OpenAITextEmbeddingGeneration build() {
            if (client == null) {
                throw new NotSupportedException(ErrorCodes.NOT_SUPPORTED, "OpenAI client not set");
            }
            if (modelId == null) {
                throw new NotSupportedException(ErrorCodes.NOT_SUPPORTED, "Model ID not set");
            }
            return new OpenAITextEmbeddingGeneration(client, modelId);
        }
    }
}
