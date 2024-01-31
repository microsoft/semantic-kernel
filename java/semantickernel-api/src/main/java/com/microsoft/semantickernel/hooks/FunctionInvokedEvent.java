package com.microsoft.semantickernel.hooks;

import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import javax.annotation.Nullable;

public class FunctionInvokedEvent<T> implements KernelHookEvent {

    private final KernelFunction function;
    @Nullable
    private final KernelArguments arguments;
    private final FunctionResult<T> result;

    public FunctionInvokedEvent(
        KernelFunction function,
        @Nullable KernelArguments arguments,
        FunctionResult<T> result) {
        this.function = function;
        this.arguments = arguments;
        this.result = result;
    }

    public KernelFunction getFunction() {
        return function;
    }

    @Nullable
    public KernelArguments getArguments() {
        return arguments;
    }

    public FunctionResult<T> getResult() {
        return result;
    }
}