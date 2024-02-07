package com.microsoft.semantickernel.hooks;

import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.KernelFunctionArguments;

import edu.umd.cs.findbugs.annotations.SuppressFBWarnings;
import javax.annotation.Nullable;

public class PromptRenderingEvent implements KernelHookEvent {

    private final KernelFunction function;
    private final KernelFunctionArguments arguments;

    public PromptRenderingEvent(KernelFunction function, @Nullable KernelFunctionArguments arguments) {
        this.function = function;
        this.arguments = arguments != null ? new KernelFunctionArguments(arguments) : new KernelFunctionArguments();
    }

    public KernelFunction getFunction() {
        return function;
    }

    @SuppressFBWarnings("EI_EXPOSE_REP")
    public KernelFunctionArguments getArguments() {
        return arguments;
    }
}
