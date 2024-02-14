// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.chatcompletion;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClient;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.TextAIService;
import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;
import com.microsoft.semantickernel.builders.ServiceLoadUtil;
import com.microsoft.semantickernel.orchestration.InvocationContext;

import java.util.List;

import javax.annotation.Nullable;

import reactor.core.publisher.Mono;

/**
 * Chat completion service interface.
 */
public interface ChatCompletionService extends Buildable, TextAIService {

    /**
     * Gets the chat message contents asynchronously using 
     * {@code ChatHistory} to support a turn-based conversation. 
     * Typically, the resulting chat message contents is appended
     * to the {@code chatHistory} to continue the conversation.
     *
     * @param chatHistory the chat history
     * @param kernel the kernel
     * @param invocationContext the invocation context
     * @return the chat message contents
     */
    Mono<List<ChatMessageContent>> getChatMessageContentsAsync(
        ChatHistory chatHistory,
        @Nullable Kernel kernel,
        @Nullable InvocationContext invocationContext);

    /**
     * Gets the chat message contents asynchronously using a prompt.
     *
     * @param prompt the prompt
     * @param kernel the kernel
     * @param invocationContext the invocation context
     * @return the chat message contents
     */
    Mono<List<ChatMessageContent>> getChatMessageContentsAsync(
        String prompt,
        @Nullable Kernel kernel,
        @Nullable InvocationContext invocationContext);

    /**
     * Get a builder for creating a {@code ChatCompletionService}. The builder loads a service
     * that implements the {@link ChatCompletionService.Builder} interface.
     * @return a builder for creating a {@code ChatCompletionService}
     */
    static Builder builder() {
        return ServiceLoadUtil.findServiceLoader(Builder.class,
            "com.microsoft.semantickernel.aiservices.openai.chatcompletion.OpenAIChatCompletion$Builder")
            .get();
    }

    /**
     * Builder API for creating a {@link ChatCompletionService}. Concrete implementations of
     * {@link ChatCompletionService} must implement the {@link SemanticKernelBuilder#build()} 
     * method.
     */
    abstract class Builder implements SemanticKernelBuilder<ChatCompletionService> {

        @Nullable
        protected OpenAIAsyncClient client;

        @Nullable
        protected String modelId;

        @Nullable
        protected String serviceId;

        /**
         * Sets the model ID to use with the ChatCompletion service.
         *
         * @param modelId the model ID to use with the ChatCompletion service
         * @return this builder
         */
        public Builder withModelId(String modelId) {
            this.modelId = modelId;
            return this;
        }

        /**
         * Sets the {@link OpenAIClient} to use for communication with the ChatCompletion service.
         *
         * @param openAIClient the {@link OpenAIClient} to use for communication with the
         *                     ChatCompletion service
         * @return this builder
         */
        public Builder withOpenAIAsyncClient(OpenAIAsyncClient openAIClient) {
            this.client = openAIClient;
            return this;
        }

        /**
         * Sets the service ID to use with the ChatCompletion service.
         *
         * @param serviceId the service ID to use with the ChatCompletion service
         * @return this builder
         */
        public Builder withServiceId(String serviceId) {
            this.serviceId = serviceId;
            return this;
        }
    }

}
