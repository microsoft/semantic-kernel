package com.microsoft.semantickernel.hooks;

import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.KernelFunctionArguments;

public class PromptRenderedEvent implements KernelHookEvent {

    private final KernelFunction function;
    private final KernelFunctionArguments arguments;
    private final String prompt;

    public PromptRenderedEvent(KernelFunction function, KernelFunctionArguments arguments,
        String prompt) {
        this.function = function;
        this.arguments = arguments;
        this.prompt = prompt;
    }

    public KernelFunction getFunction() {
        return function;
    }

    public KernelFunctionArguments getArguments() {
        return arguments;
    }

    public String getPrompt() {
        return prompt;
    }
}