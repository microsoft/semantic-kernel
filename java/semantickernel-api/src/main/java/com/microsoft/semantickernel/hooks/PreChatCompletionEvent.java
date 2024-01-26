package com.microsoft.semantickernel.hooks;

import com.azure.ai.openai.models.ChatCompletionsOptions;

public class PreChatCompletionEvent implements KernelHookEvent {

    private final ChatCompletionsOptions options;

    public PreChatCompletionEvent(ChatCompletionsOptions options) {
        this.options = options;
    }

    public ChatCompletionsOptions getOptions() {
        return options;
    }
}
