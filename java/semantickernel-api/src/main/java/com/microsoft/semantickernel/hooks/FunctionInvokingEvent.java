package com.microsoft.semantickernel.hooks;

import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.KernelFunctionArguments;

import javax.annotation.Nullable;

import edu.umd.cs.findbugs.annotations.SuppressFBWarnings;

/**
 * Represents a KernelHookEvent that is raised before a function is invoked.
 * This event is raised before the function is invoked, and can be used to 
 * by a {@code KernelHook} to modify the arguments before the function is invoked.
 * @param <T> The type of the KernelFunction being invoked
 */
public class FunctionInvokingEvent<T> implements KernelHookEvent {

    private final KernelFunction<T> function;
    private final KernelFunctionArguments arguments;

    public FunctionInvokingEvent(KernelFunction<T> function, 
        @Nullable KernelFunctionArguments arguments) {
        this.function = function;
        this.arguments = arguments != null ? new KernelFunctionArguments(arguments) : new KernelFunctionArguments();
    }

    /**
     * Gets the function that is being invoked.
     * @return the function
     */
    public KernelFunction<T> getFunction() {
        return function;
    }

    /**
     * Gets the arguments that are being passed to the function.
     * @return the arguments
     */
    @SuppressFBWarnings("EI_EXPOSE_REP")
    public KernelFunctionArguments getArguments() {
        return arguments;
    }
}