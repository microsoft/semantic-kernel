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
     * Get a builder for creating a {@code ChatCompletionService}. The builder loads a service that
     * implements the {@link ChatCompletionService.Builder} interface.
     *
     * @return a builder for creating a {@code ChatCompletionService}
     */
    static Builder builder() {
        return ServiceLoadUtil.findServiceLoader(Builder.class,
            "com.microsoft.semantickernel.aiservices.openai.chatcompletion.OpenAIChatCompletion$Builder")
            .get();
    }

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

    /**
     * Builder API for creating a {@link ChatCompletionService}. Concrete implementations of
     * {@link ChatCompletionService} must implement the {@link SemanticKernelBuilder#build()}
     * method.
     */
    abstract class Builder extends OpenAiServiceBuilder<ChatCompletionService, Builder> {

    }

}
