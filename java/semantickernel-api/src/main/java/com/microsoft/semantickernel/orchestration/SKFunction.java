// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;

import reactor.core.publisher.Mono;

import javax.annotation.CheckReturnValue;
import javax.annotation.Nullable;

/**
 * Semantic Kernel callable function interface
 *
 * @param <RequestConfiguration> The type of the configuration argument that will be provided when
 *     the function is invoked
 */
public interface SKFunction<RequestConfiguration, ContextType extends SKContext<ContextType>> {
    /*
        /// <summary>
        /// Name of the function. The name is used by the skill collection and in prompt templates e.g. {{skillName.functionName}}
        /// </summary>
        string Name { get; }

        /// <summary>
        /// Name of the skill containing the function. The name is used by the skill collection and in prompt templates e.g. {{skillName.functionName}}
        /// </summary>
        string SkillName { get; }

        /// <summary>
        /// Function description. The description is used in combination with embeddings when searching relevant functions.
        /// </summary>
        string Description { get; }

        /// <summary>
        /// Whether the function is defined using a prompt template.
        /// IMPORTANT: native functions might use semantic functions internally,
        /// so when this property is False, executing the function might still involve AI calls.
        /// </summary>
        public bool IsSemantic { get; }

        /// <summary>
        /// AI service settings
        /// </summary>
        public CompleteRequestSettings RequestSettings { get; }

        /// <summary>
        /// Returns a description of the function, including parameters.
        /// </summary>
        /// <returns>An instance of <see cref="FunctionView"/> describing the function</returns>
        FunctionView Describe();
    */
    // TODO: CancellationToken
    /// <summary>
    /// Invoke the internal delegate with an explicit string input
    /// </summary>
    /// <param name="input">String input</param>
    /// <param name="context">SK context</param>
    /// <param name="settings">LLM completion settings</param>
    /// <param name="log">Application logger</param>
    /// <param name="cancel">Cancellation token</param>
    /// <returns>The updated context, potentially a new one if context switching is
    // implemented.</returns>

    /**
     * Invokes the function with the given input, context and settings
     *
     * @param input input provided to the function
     * @param context Request context
     * @param settings Configuration of the request
     * @return an updated context with the result of the request
     */
    @CheckReturnValue
    Mono<ContextType> invokeAsync(String input, ContextType context, RequestConfiguration settings);

    /**
     * Invokes the function with the given input
     *
     * @param input input provided to the function
     * @return an updated context with the result of the request
     */
    @CheckReturnValue
    Mono<ContextType> invokeAsync(String input);

    Class<RequestConfiguration> getType();

    /**
     * Invokes the function with the given context and settings
     *
     * @param context Request context
     * @param settings Configuration of the request
     * @return an updated context with the result of the request
     */
    @CheckReturnValue
    Mono<ContextType> invokeAsync(ContextType context, @Nullable RequestConfiguration settings);

    /// <summary>
    /// Set the default skill collection to use when the function is invoked
    /// without a context or with a context that doesn't have a collection.
    /// </summary>
    /// <param name="skills">Kernel's skill collection</param>
    /// <returns>Self instance</returns>
    /*
    SKFunction<RequestConfiguration> setDefaultSkillCollection(SkillCollection skills);
      /// <summary>
      /// Set the AI service used by the semantic function, passing a factory method.
      /// The factory allows to lazily instantiate the client and to properly handle its disposal.
      /// </summary>
      /// <param name="serviceFactory">AI service factory</param>
      /// <returns>Self instance</returns>
      SKFunction setAIService(Supplier<TextCompletion> serviceFactory);

      /// <summary>
      /// Set the AI completion settings used with LLM requests
      /// </summary>
      /// <param name="settings">LLM completion settings</param>
      /// <returns>Self instance</returns>
      SKFunction setAIConfiguration(CompleteRequestSettings settings);
    */

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

    String getDescription();

    String toEmbeddingString();

    String toManualString();

    ContextType buildContext(
            ContextVariables variables,
            @Nullable SemanticTextMemory memory,
            @Nullable ReadOnlySkillCollection skills);

    ContextType buildContext();

    Mono<ContextType> invokeWithCustomInputAsync(
            ContextVariables variablesClone,
            SemanticTextMemory semanticMemory,
            ReadOnlySkillCollection skills);
}
