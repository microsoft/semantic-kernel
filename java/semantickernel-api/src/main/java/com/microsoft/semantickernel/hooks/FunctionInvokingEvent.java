package com.microsoft.semantickernel.hooks;

import javax.annotation.Nullable;

import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.KernelFunctionArguments;

import edu.umd.cs.findbugs.annotations.SuppressFBWarnings;

public class FunctionInvokingEvent implements KernelHookEvent {

    private final KernelFunction function;
    private final KernelFunctionArguments arguments;

    public FunctionInvokingEvent(KernelFunction function, 
        @Nullable KernelFunctionArguments arguments) {
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