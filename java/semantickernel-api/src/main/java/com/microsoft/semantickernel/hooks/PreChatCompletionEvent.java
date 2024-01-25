package com.microsoft.semantickernel.hooks;

import com.azure.ai.openai.models.ChatCompletionsOptions;

public class PreChatCompletionEvent implements HookEvent {

    private final ChatCompletionsOptions options;

    public PreChatCompletionEvent(ChatCompletionsOptions options) {
        this.options = options;
    }

    public ChatCompletionsOptions getOptions() {
        return options;
    }
}
