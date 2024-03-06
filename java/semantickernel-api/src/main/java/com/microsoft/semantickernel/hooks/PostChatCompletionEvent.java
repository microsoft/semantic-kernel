// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.hooks;

import com.azure.ai.openai.models.ChatCompletions;

/**
 * Represents a KernelHookEvent that is raised after a chat completion is invoked.
 */
public class PostChatCompletionEvent implements KernelHookEvent {

    private final ChatCompletions chatCompletions;

    /**
     * Creates a new instance of the {@link PostChatCompletionEvent} class.
     *
     * @param chatCompletions the chat completions
     */
    public PostChatCompletionEvent(ChatCompletions chatCompletions) {
        this.chatCompletions = chatCompletions;
    }

    /**
     * Gets the chat completions.
     *
     * @return the chat completions
     */
    public ChatCompletions getChatCompletions() {
        return chatCompletions;
    }
}
