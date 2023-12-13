// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.chatcompletion;

import java.util.List;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.AIService;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.PromptExecutionSettings;
import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.builders.BuildersSingleton;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;

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

    @SuppressWarnings("unchecked")
    static Builder builder() {
        return BuildersSingleton.INST.getInstance(ChatCompletionService.Builder.class);
    }

    interface Builder extends SemanticKernelBuilder<ChatCompletionService> {

        Builder withOpenAIClient(OpenAIAsyncClient client);

        Builder withModelId(String modelId);
    }
}
