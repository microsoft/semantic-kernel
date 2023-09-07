// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.chatcompletion;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.models.ChatCompletions;
import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.builders.BuildersSingleton;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;
import com.microsoft.semantickernel.services.AIService;
import com.microsoft.semantickernel.textcompletion.TextCompletion;
import javax.annotation.Nullable;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public interface ChatCompletion<ChatHistoryType extends ChatHistory>
        extends AIService, TextCompletion, Buildable {
    /**
     * Generate a new chat message
     *
     * @param chat Chat history
     * @param requestSettings AI request settings
     * @return Generated chat message in string format
     */
    Mono<String> generateMessageAsync(
            ChatHistoryType chat, @Nullable ChatRequestSettings requestSettings);

    /**
     * Create a new empty chat instance
     *
     * @param instructions Optional chat instructions for the AI service
     * @return Chat object
     */
    ChatHistoryType createNewChat(@Nullable String instructions);

    Flux<String> generateMessageStream(
            ChatHistoryType chatHistory, @Nullable ChatRequestSettings requestSettings);

    Flux<ChatCompletions> getStreamingChatCompletionsAsync(
            ChatHistoryType chat, ChatRequestSettings requestSettings);

    @SuppressWarnings("unchecked")
    static <ChatHistoryType extends ChatHistory, E extends ChatCompletion<ChatHistoryType>>
            Builder<ChatHistoryType> builder() {
        return (Builder<ChatHistoryType>) BuildersSingleton.INST.getInstance(Builder.class);
    }

    interface Builder<ChatHistoryType extends ChatHistory>
            extends SemanticKernelBuilder<ChatCompletion<ChatHistoryType>> {

        Builder<ChatHistoryType> withOpenAIClient(OpenAIAsyncClient client);

        Builder<ChatHistoryType> withModelId(String modelId);
    }
}
