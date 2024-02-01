package com.microsoft.semantickernel.hooks;

import javax.annotation.Nullable;

import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.KernelFunctionArguments;

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
        this.arguments = arguments;
        this.result = result;
    }

    public KernelFunction getFunction() {
        return function;
    }

    public KernelFunctionArguments getArguments() {
        return arguments;
    }

    public FunctionResult<T> getResult() {
        return result;
    }
}