// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableType;
import com.microsoft.semantickernel.skilldefinition.FunctionView;
import javax.annotation.Nullable;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * Semantic Kernel callable function interface
 *
 * @apiNote Breaking change: s/SKFunction<RequestConfiguration>/SKFunction/
 */
public interface KernelFunction {

    /**
     * Returns a description of the function, including parameters.
     *
     * @return An instance of {@link FunctionView} describing the function
     */
    @Nullable
    FunctionView describe();


    /**
     * @return The name of the skill that this function is within
     */
    String getSkillName();

    /**
     * @return The name of this function
     */
    String getName();

    /**
     * The function to create a fully qualified name for
     *
     * @return A fully qualified name for a function
     */
    String toFullyQualifiedName();

    /**
     * @return A description of the function
     */
    String getDescription();

    /**
     * Create a string for generating an embedding for a function.
     *
     * @return A string for generating an embedding for a function.
     */
    String toEmbeddingString();

    /**
     * Create a manual-friendly string for a function.
     *
     * @param includeOutputs Whether to include function outputs in the string.
     * @return A manual-friendly string for a function.
     */
    String toManualString(boolean includeOutputs);

    @Deprecated
    default Class<?> getType() {
        throw new UnsupportedOperationException("Deprecated");
    }

    /**
     * Invokes the <see cref="KernelFunction"/> and streams its results.
     *
     * @param kernel    The <see cref="Kernel"/> containing services, plugins, and other state for
     *                  use throughout the operation.
     * @param arguments The arguments to pass to the function's invocation, including any
     *                  {@link PromptExecutionSettings}.
     * @param <T>       The type of the context variable
     * @return An {@link Flux} for streaming the results of the function's invocation.
     */
    <T> Flux<ContextVariable<T>> invokeStreamingAsync(
        Kernel kernel,
        @Nullable KernelArguments arguments,
        ContextVariableType<T> variableType);

    /**
     * Invokes the <see cref="KernelFunction"/>.
     *
     * @param kernel    The <see cref="Kernel"/> containing services, plugins, and other state for
     *                  use throughout the operation.
     * @param arguments The arguments to pass to the function's invocation, including any
     *                  {@link PromptExecutionSettings}.
     * @param <T>       The type of the context variable
     * @return The result of the function's execution.
     */
    <T> Mono<ContextVariable<T>> invokeAsync(
        Kernel kernel,
        @Nullable KernelArguments arguments,
        ContextVariableType<T> variableType);
}
