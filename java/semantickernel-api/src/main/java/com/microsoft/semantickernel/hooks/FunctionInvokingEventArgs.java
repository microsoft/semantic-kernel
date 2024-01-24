package com.microsoft.semantickernel.hooks;

import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;

public class FunctionInvokingEventArgs implements HookEvent {

    private final KernelFunction function;
    private final KernelArguments arguments;

    public FunctionInvokingEventArgs(KernelFunction function, KernelArguments arguments) {
        this.function = function;
        this.arguments = arguments;
    }

    public KernelFunction getFunction() {
        return function;
    }

    public KernelArguments getArguments() {
        return arguments;
    }
}