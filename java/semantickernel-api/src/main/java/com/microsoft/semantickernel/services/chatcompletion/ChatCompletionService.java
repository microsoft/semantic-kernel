// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.services.chatcompletion;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;
import com.microsoft.semantickernel.implementation.ServiceLoadUtil;
import com.microsoft.semantickernel.orchestration.InvocationContext;
import com.microsoft.semantickernel.services.TextAIService;
import com.microsoft.semantickernel.services.openai.OpenAiServiceBuilder;
import java.util.List;
import javax.annotation.Nullable;
import reactor.core.publisher.Mono;

/**
 * Chat completion service interface.
 */
public interface ChatCompletionService extends TextAIService {
    /**
     * Gets the chat message contents asynchronously using {@code ChatHistory} to support a
     * turn-based conversation. Typically, the resulting chat message contents is appended to the
     * {@code chatHistory} to continue the conversation.
     *
     * @param chatHistory       the chat history
     * @param kernel            the kernel
     * @param invocationContext the invocation context
     * @return the chat message contents
     */
    Mono<List<ChatMessageContent<?>>> getChatMessageContentsAsync(
        ChatHistory chatHistory,
        @Nullable Kernel kernel,
        @Nullable InvocationContext invocationContext);

    /**
     * Gets the chat message contents asynchronously using a prompt.
     *
     * @param prompt            the prompt
     * @param kernel            the kernel
     * @param invocationContext the invocation context
     * @return the chat message contents
     */
    Mono<List<ChatMessageContent<?>>> getChatMessageContentsAsync(
        String prompt,
        @Nullable Kernel kernel,
        @Nullable InvocationContext invocationContext);
}
