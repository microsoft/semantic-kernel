// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.chatcompletion;

import java.util.List;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClient;
import com.microsoft.semantickernel.AIService;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public interface ChatCompletionService extends Buildable, AIService {

    Mono<List<ChatMessageContent>> getChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings promptExecutionSettings,
        Kernel kernel
    );

    Flux<StreamingChatMessageContent> getStreamingChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings promptExecutionSettings,
        Kernel kernel
    );

    Mono<List<ChatMessageContent>> getChatMessageContentsAsync(
        String prompt,
        PromptExecutionSettings promptExecutionSettings,
        Kernel kernel
    );

    Flux<StreamingChatMessageContent> getStreamingChatMessageContentsAsync(
        String prompt,
        PromptExecutionSettings promptExecutionSettings,
        Kernel kernel
    );

    interface Builder<T extends ChatCompletionService> extends SemanticKernelBuilder<T> {

        /**
         * Sets the model ID to use with the ChatCompletion service.
         * @param modelId the model ID to use with the ChatCompletion service
         * @return this builder
         */
        Builder<T> withModelId(String modelId);

        /**
         * Sets the {@link OpenAIClient} to use for communication with the ChatCompletion service.
         * @param openAIClient the {@link OpenAIClient} to use for communication with the ChatCompletion service
         * @return this builder
         */
        Builder<T> withOpenAIAsyncClient(OpenAIAsyncClient openAIClient);

    }

}
