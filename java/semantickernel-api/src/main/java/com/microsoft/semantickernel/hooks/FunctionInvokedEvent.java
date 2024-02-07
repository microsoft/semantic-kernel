package com.microsoft.semantickernel.hooks;

import javax.annotation.Nullable;

import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.KernelFunctionArguments;

import edu.umd.cs.findbugs.annotations.SuppressFBWarnings;

public class FunctionInvokedEvent<T> implements KernelHookEvent {

    private final KernelFunction function;
    @Nullable
    private final KernelFunctionArguments arguments;
    private final FunctionResult<T> result;

    public FunctionInvokedEvent(
        KernelFunction function,
        @Nullable KernelFunctionArguments arguments,
        FunctionResult<T> result) {
        this.function = function;
        this.arguments = arguments != null ? new KernelFunctionArguments(arguments) : new KernelFunctionArguments();
        this.result = result;
    }

    public KernelFunction getFunction() {
        return function;
    }

    @SuppressFBWarnings("EI_EXPOSE_REP")
    @Nullable
    public KernelFunctionArguments getArguments() {
        return arguments;
    }

    @SuppressFBWarnings("EI_EXPOSE_REP")
    public FunctionResult<T> getResult() {
        return result;
    }
}