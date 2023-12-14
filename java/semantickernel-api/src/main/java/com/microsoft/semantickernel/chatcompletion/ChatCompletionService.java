// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.chatcompletion;

import java.util.List;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.AIService;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.builders.BuildersSingleton;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public interface ChatCompletionService extends Buildable, AIService {

    /**
     * Creates a new, empty chat instance. This is the same as calling
     * {@link #createNewChat(String)} with a {@code null} argument.
     * @return a new {@link ChatHistory} instance
     */
    default ChatHistory createNewChat() {
        return createNewChat(null);
    }

    /**
     * Creates a new, empty chat instance
     * @param instructions Chat instructions for the AI service, may be {@code null}
     * @return a new {@link ChatHistory} instance
     */
    ChatHistory createNewChat(String instructions);

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
