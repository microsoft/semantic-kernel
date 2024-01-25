package com.microsoft.semantickernel.hooks;

import com.azure.ai.openai.models.ChatCompletionsOptions;

public class PreChatCompletionHookEvent implements HookEvent {

    private final ChatCompletionsOptions options;

    public PreChatCompletionHookEvent(ChatCompletionsOptions options) {
        this.options = options;
    }

    public ChatCompletionsOptions getOptions() {
        return options;
    }
}
