package com.microsoft.semantickernel.hooks;

import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.KernelFunctionArguments;

import edu.umd.cs.findbugs.annotations.SuppressFBWarnings;

public class PromptRenderedEvent implements KernelHookEvent {

    private final KernelFunction function;
    private final KernelFunctionArguments arguments;
    private final String prompt;

    public PromptRenderedEvent(KernelFunction function, KernelFunctionArguments arguments,
        String prompt) {
        this.function = function;
        this.arguments = arguments != null ? new KernelFunctionArguments(arguments) : new KernelFunctionArguments();
        this.prompt = prompt;
    }

    public KernelFunction getFunction() {
        return function;
    }

    @SuppressFBWarnings("EI_EXPOSE_REP")
    public KernelFunctionArguments getArguments() {
        return arguments;
    }

    @SuppressFBWarnings("EI_EXPOSE_REP")
    public String getPrompt() {
        return prompt;
    }
}