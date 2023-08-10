// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.skilldefinition.FunctionView;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import javax.annotation.CheckReturnValue;
import javax.annotation.Nullable;
import reactor.core.publisher.Mono;

/**
 * Semantic Kernel callable function interface
 *
 * @param <RequestConfiguration> The type of the configuration argument that will be provided when
 *     the function is invoked
 */
public interface SKFunction<RequestConfiguration> {
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
     */
    @CheckReturnValue
    Mono<SKContext> invokeAsync(String input, SKContext context, RequestConfiguration settings);

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
     * @return The type
     */
    @Nullable
    Class<RequestConfiguration> getType();

    /**
     * Invokes the function with the given context and settings
     *
     * @param context Request context
     * @return an updated context with the result of the request
     */
    @CheckReturnValue
    Mono<SKContext> invokeAsync(SKContext context);

    /**
     * Invokes the function with the given context and settings
     *
     * @param context Request context
     * @param settings Configuration of the request
     * @return an updated context with the result of the request
     */
    @CheckReturnValue
    Mono<SKContext> invokeAsync(SKContext context, @Nullable RequestConfiguration settings);

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
     * @return A manual-friendly string for a function.
     */
    String toManualString();

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
