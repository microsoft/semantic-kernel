// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.chatcompletion;

import java.util.List;

import com.microsoft.semantickernel.AIService;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.PromptExecutionSettings;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public interface ChatCompletionService extends AIService {

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
}
