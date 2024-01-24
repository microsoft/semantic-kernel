package com.microsoft.semantickernel.hooks;

import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;

public class FunctionInvokedEventArgs<T> implements HookEvent {


    private final KernelFunction function;
    private final KernelArguments arguments;
    private final FunctionResult<T> result;

    public FunctionInvokedEventArgs(KernelFunction function, KernelArguments arguments,
        FunctionResult<T> result) {
        this.function = function;
        this.arguments = arguments;
        this.result = result;
    }

    public KernelFunction getFunction() {
        return function;
    }

    public KernelArguments getArguments() {
        return arguments;
    }

    public FunctionResult<T> getResult() {
        return result;
    }
}