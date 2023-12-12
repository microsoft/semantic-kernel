// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import javax.annotation.CheckReturnValue;
import javax.annotation.Nullable;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.skilldefinition.FunctionView;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;

import reactor.core.publisher.Mono;

/**
 * Semantic Kernel callable function interface
 *
 * @apiNote Breaking change: s/SKFunction<RequestConfiguration>/SKFunction/
 */
public interface SKFunction {
    /**
     * Returns a description of the function, including parameters.
     *
     * @return An instance of {@link FunctionView} describing the function
     */
    @Nullable
    FunctionView describe();

    /**
     * Invokes the function with the given input, context and settings
     *
     * @param input input provided to the function
     * @param context Request context
     * @param settings Configuration of the request
     * @return an updated context with the result of the request
     * @apiNote Breaking change: s/RequestConfiguration settings/Object settings/
     */
    @CheckReturnValue
    @Deprecated
    default Mono<SKContext> invokeAsync(String input, SKContext context, Object settings) {
        throw new UnsupportedOperationException("Deprecated");
    }

    /**
     * Invokes the function
     *
     * @return an updated context with the result of the request
     */
    Mono<SKContext> invokeAsync();

    /**
     * Invokes the function with the given input
     *
     * @param input input provided to the function
     * @return an updated context with the result of the request
     */
    @CheckReturnValue
    Mono<SKContext> invokeAsync(String input);

    /**
     * The type of the configuration argument that will be provided when the function is invoked
     *
     * @return The type @Nullable Class<RequestConfiguration> getType();
     */

    /**
     * Invokes the function with the given context and settings
     *
     * @param context Request context
     * @return an updated context with the result of the request
     */
    @CheckReturnValue
    @Deprecated
    default Mono<SKContext> invokeAsync(SKContext context) {
        throw new UnsupportedOperationException("Deprecated");
    }

    /**
     * The type of the configuration argument that will be provided when the function is invoked
     *
     * @return The type @Nullable Class<RequestConfiguration> getType();
     */

    /**
     * Invokes the function with the given context and settings
     *
     * @param kernel Associated Kernel
     * @param variables Request variables
     * @param streaming Whether streaming is on or not
     * @return an updated context with the result of the request
     */
    @CheckReturnValue
    default Mono<FunctionResult> invokeAsync(Kernel kernel, ContextVariables variables, boolean streaming) {
        throw new UnsupportedOperationException("Deprecated");
    }


    /**
     * Invokes the function with the given context and settings
     *
     * @param context Request context
     * @param settings Configuration of the request
     * @return an updated context with the result of the request
     * @apiNote Breaking change: s/RequestConfiguration settings/Object settings/
     */
    @CheckReturnValue
    @Deprecated
    default Mono<SKContext> invokeAsync(SKContext context, @Nullable Object settings) {
        throw new UnsupportedOperationException("Deprecated");
    }

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
     * Invokes the function with the given input, context and settings
     *
     * @param variables variables to be used in the function
     * @param semanticMemory semantic memory to be used in the function
     * @param skills skills to be used in the function
     * @return an updated context with the result of the request
     */
    Mono<SKContext> invokeWithCustomInputAsync(
            ContextVariables variables,
            @Nullable SemanticTextMemory semanticMemory,
            @Nullable ReadOnlySkillCollection skills);
}
