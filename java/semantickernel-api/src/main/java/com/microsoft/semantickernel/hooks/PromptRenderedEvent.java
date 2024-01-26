package com.microsoft.semantickernel.hooks;

import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;

public class PromptRenderedEvent implements KernelHookEvent {

    private final KernelFunction function;
    private final KernelArguments arguments;
    private final String prompt;

    public PromptRenderedEvent(KernelFunction function, KernelArguments arguments,
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