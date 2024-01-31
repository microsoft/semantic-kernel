package com.microsoft.semantickernel.hooks;

import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import javax.annotation.Nullable;

public class FunctionInvokingEvent implements KernelHookEvent {

    private final KernelFunction function;
    @Nullable
    private final KernelArguments arguments;

    public FunctionInvokingEvent(KernelFunction function, @Nullable KernelArguments arguments) {
        this.function = function;
        this.arguments = arguments;
    }

    public KernelFunction getFunction() {
        return function;
    }

    @Nullable
    public KernelArguments getArguments() {
        return arguments;
    }
}