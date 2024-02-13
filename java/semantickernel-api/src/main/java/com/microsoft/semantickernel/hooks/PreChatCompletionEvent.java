package com.microsoft.semantickernel.hooks;

import com.azure.ai.openai.models.ChatCompletionsOptions;

/**
 * Represents a KernelHookEvent that is raised before a chat completion is invoked.
 */
public class PreChatCompletionEvent implements KernelHookEvent {

    private final ChatCompletionsOptions options;

    /**
     * Creates a new instance of the {@link PreChatCompletionEvent} class.
     * @param options the chat completion options
     */
    public PreChatCompletionEvent(ChatCompletionsOptions options) {
        this.options = options;
    }

    /**
     * Gets the chat completion options.
     * @return the options
     */
    public ChatCompletionsOptions getOptions() {
        return options;
    }
}
