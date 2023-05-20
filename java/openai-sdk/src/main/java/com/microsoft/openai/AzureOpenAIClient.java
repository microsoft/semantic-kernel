// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.openai;

import com.azure.ai.openai.models.*;

import reactor.core.publisher.Mono;

/**
 * Create an OpenAIAsyncClient that delegates to an com.azure.ai.openai.OpenAIAsyncClient provided
 * by com.azure:azure-ai-openai
 */
public class AzureOpenAIClient implements OpenAIAsyncClient {
    private final com.azure.ai.openai.OpenAIAsyncClient delegate;

    public AzureOpenAIClient(com.azure.ai.openai.OpenAIAsyncClient delegate) {
        this.delegate = delegate;
    }

    @Override
    public Mono<Embeddings> getEmbeddings(
            String deploymentId, EmbeddingsOptions embeddingsOptions) {
        return delegate.getEmbeddings(deploymentId, embeddingsOptions);
    }

    @Override
    public Mono<Completions> getCompletions(
            String deploymentId, CompletionsOptions completionsOptions) {
        return delegate.getCompletions(deploymentId, completionsOptions);
    }

    @Override
    public Mono<ChatCompletions> getChatCompletions(
            String deploymentId, ChatCompletionsOptions chatCompletionsOptions) {
        return delegate.getChatCompletions(deploymentId, chatCompletionsOptions);
    }
}
