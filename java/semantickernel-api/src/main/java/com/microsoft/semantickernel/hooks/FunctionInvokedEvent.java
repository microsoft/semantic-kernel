package com.microsoft.semantickernel.hooks;

import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.KernelFunctionArguments;

import javax.annotation.Nullable;

import edu.umd.cs.findbugs.annotations.SuppressFBWarnings;

/**
 * Represents a KernelHookEvent that is raised after a function is invoked.
 * @param <T> The type of the function result
 */
public class FunctionInvokedEvent<T> implements KernelHookEvent {

    private final KernelFunction<T> function;
    @Nullable
    private final KernelFunctionArguments arguments;
    private final FunctionResult<T> result;

    /**
     * Creates a new instance of the {@link FunctionInvokedEvent} class.
     * @param function the function
     * @param arguments the arguments
     * @param result the result
     */
    public FunctionInvokedEvent(
        KernelFunction<T> function,
        @Nullable KernelFunctionArguments arguments,
        FunctionResult<T> result) {
        this.function = function;
        this.arguments = arguments != null ? new KernelFunctionArguments(arguments) : new KernelFunctionArguments();
        this.result = result;
    }

    /**
     * Gets the function that was invoked.
     * @return the function
     */
    public KernelFunction<T> getFunction() {
        return function;
    }

    /**
     * Gets the arguments that were passed to the function.
     * @return the arguments
     */
    @SuppressFBWarnings("EI_EXPOSE_REP")
    @Nullable
    public KernelFunctionArguments getArguments() {
        return arguments;
    }

    /**
     * Gets the result of the function invocation.
     * @return the result
     */
    @SuppressFBWarnings("EI_EXPOSE_REP")
    public FunctionResult<T> getResult() {
        return result;
    }
}