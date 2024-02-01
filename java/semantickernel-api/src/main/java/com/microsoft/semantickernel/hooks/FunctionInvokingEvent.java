package com.microsoft.semantickernel.hooks;

import javax.annotation.Nullable;

import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.KernelFunctionArguments;

public class FunctionInvokingEvent implements KernelHookEvent {

    private final KernelFunction function;
    private final KernelFunctionArguments arguments;

    public FunctionInvokingEvent(KernelFunction function, 
        @Nullable KernelFunctionArguments arguments) {
        this.function = function;
        this.arguments = arguments;
    }

    public KernelFunction getFunction() {
        return function;
    }

    public KernelFunctionArguments getArguments() {
        return arguments;
    }
}