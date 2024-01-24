package com.microsoft.semantickernel.hooks;

import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;

public class PromptRenderedEventArgs implements HookEvent {

    private final KernelFunction function;
    private final KernelArguments arguments;
    private final String prompt;

    public PromptRenderedEventArgs(KernelFunction function, KernelArguments arguments,
        String prompt) {
        this.function = function;
        this.arguments = arguments;
        this.prompt = prompt;
    }

    public KernelFunction getFunction() {
        return function;
    }

    public KernelArguments getArguments() {
        return arguments;
    }

    public String getPrompt() {
        return prompt;
    }
}