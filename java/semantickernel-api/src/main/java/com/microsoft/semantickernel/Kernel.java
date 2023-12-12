// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import java.util.function.Function;
import java.util.function.Supplier;

import javax.annotation.Nullable;

import com.microsoft.semantickernel.ai.embeddings.TextEmbeddingGeneration;
import com.microsoft.semantickernel.aiservices.AIService;
import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.builders.BuildersSingleton;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;
import com.microsoft.semantickernel.memory.MemoryStore;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.orchestration.ContextVariables;
import com.microsoft.semantickernel.orchestration.SKFunction;
import com.microsoft.semantickernel.plugin.Plugin;
import com.microsoft.semantickernel.semanticfunctions.SemanticFunctionConfig;
import com.microsoft.semantickernel.skilldefinition.ReadOnlyFunctionCollection;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import com.microsoft.semantickernel.templateengine.PromptTemplateEngine;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;

import reactor.core.publisher.Mono;

/** Interface for the semantic kernel. */
public interface Kernel extends SkillExecutor, Buildable {

    /**
     * Settings required to execute functions, including details about AI dependencies, e.g.
     * endpoints and API keys.
     */
    @Deprecated
    default KernelConfig getConfig() { throw new UnsupportedOperationException(); }

    /**
     * Reference to the engine rendering prompt templates
     *
     * @return Reference to the engine rendering prompt templates
     */
    @Deprecated
    default PromptTemplateEngine getPromptTemplateEngine() { throw new UnsupportedOperationException(); }

    /**
     * Get the SemanticTextMemory in use.
     *
     * @return the SemanticTextMemory in use
     */
    @Deprecated
    default SemanticTextMemory getMemory() { throw new UnsupportedOperationException(); }

    /**
     * Run a pipeline composed of synchronous and asynchronous functions.
     *
     * @param pipeline List of functions
     * @return Result of the function composition
     * @apiNote Breaking change: s/SKFunction/SKFunction/, s/Mono<SKContext>/Mono<KernelResult>/
     */
    @Deprecated
    default Mono<KernelResult> runAsync(SKFunction... pipeline) { throw new UnsupportedOperationException(); }

    /**
     * Run a pipeline composed of synchronous and asynchronous functions.
     *
     * @param input Input to process
     * @param pipeline List of functions
     * @return Result of the function composition
     * @apiNote Breaking change: s/SKFunction/SKFunction/, s/Mono<SKContext>/Mono<KernelResult>/
     */
    @Deprecated
    default Mono<KernelResult> runAsync(String input, SKFunction... pipeline) { throw new UnsupportedOperationException(); }

    /**
     * Run a pipeline composed of synchronous and asynchronous functions.
     *
     * @param variables variables to initialise the context with
     * @param pipeline List of functions
     * @return Result of the function composition
     * @apiNote Breaking change: s/SKFunction/SKFunction/, s/Mono<SKContext>/Mono<KernelResult>/
     */
    Mono<KernelResult> runAsync(ContextVariables variables, SKFunction... pipeline);

    /**
     * Run a pipeline composed of synchronous and asynchronous functions.
     *
     * @param streaming Whether to stream the results of the pipeline
     * @param variables variables to initialise the context with
     * @param pipeline List of functions
     * @return Result of the function composition
     * @since 1.0.0
     */
    Mono<KernelResult> runAsync(
            boolean streaming, ContextVariables variables, SKFunction... pipeline);

    /**
     * Register a semantic function on this kernel
     *
     * @param skillName The skill name
     * @param functionName The function name
     * @param functionConfig The function configuration
     * @return The registered function
     */
    @Deprecated
    default CompletionSKFunction registerSemanticFunction(
            String skillName, String functionName, SemanticFunctionConfig functionConfig)
        { throw new UnsupportedOperationException(); }

    /**
     * Get a completion function builder, functions created with this builder will be registered on
     * the kernel
     */
    @Deprecated
    default CompletionSKFunction.Builder getSemanticFunctionBuilder() { throw new UnsupportedOperationException(); }

    /** Obtains the service with the given name and type */
    @Deprecated
    default <T extends AIService> T getService(@Nullable String name, Class<T> clazz)
            throws KernelException { throw new UnsupportedOperationException(); }

    /**
     * Registers a semantic function on this kernel
     *
     * @apiNote Breaking change: s/<RequestConfiguration, FunctionType extends
     *     SKFunction<RequestConfiguration>>/<FunctionType extends SKFunction>/
     */
    @Deprecated
    default <FunctionType extends SKFunction> FunctionType registerSemanticFunction(
            FunctionType semanticFunctionDefinition) { throw new UnsupportedOperationException(); }

    /**
     * Obtains a semantic function with the given name
     *
     * @apiNote Breaking change: s/SKFunction<?>/SKFunction/
     */
    @Deprecated
    default SKFunction getFunction(String skill, String function) { throw new UnsupportedOperationException(); }

    static Builder builder() {
        return BuildersSingleton.INST.getInstance(Kernel.Builder.class);
    }

    @Deprecated
    default ReadOnlySkillCollection getSkills() { throw new UnsupportedOperationException(); }

    @Deprecated
    default ReadOnlyFunctionCollection getSkill() { throw new UnsupportedOperationException(); }

    interface Builder extends SemanticKernelBuilder<Kernel> {
        /**
         * Set the kernel configuration
         *
         * @param kernelConfig Kernel configuration
         * @return Builder
         */
        @Deprecated
        Builder withConfiguration(KernelConfig kernelConfig);

        /**
         * Add prompt template engine to the kernel to be built.
         *
         * @param promptTemplateEngine Prompt template engine to add.
         * @return Updated kernel builder including the prompt template engine.
         */
        @Deprecated
        Builder withPromptTemplateEngine(PromptTemplateEngine promptTemplateEngine);

        /**
         * Add memory storage to the kernel to be built.
         *
         * @param storage Storage to add.
         * @return Updated kernel builder including the memory storage.
         */
        @Deprecated
        Builder withMemoryStorage(MemoryStore storage);

        /**
         * Add memory storage factory to the kernel.
         *
         * @param factory The storage factory.
         * @return Updated kernel builder including the memory storage.
         */
        @Deprecated
        Builder withMemoryStorage(Supplier<MemoryStore> factory);

        /**
         * Adds an instance to the services collection
         *
         * @param instance The instance.
         * @return The builder.
         */
        @Deprecated
        <T extends AIService> Builder withDefaultAIService(T instance);

        /**
         * Adds an instance to the services collection
         *
         * @param instance The instance.
         * @param clazz The class of the instance.
         * @return The builder.
         */
        @Deprecated
        <T extends AIService> Builder withDefaultAIService(T instance, Class<T> clazz);

        /**
         * Adds a factory method to the services collection
         *
         * @param factory The factory method that creates the AI service instances of type T.
         * @param clazz The class of the instance.
         */
        @Deprecated
        <T extends AIService> Builder withDefaultAIService(Supplier<T> factory, Class<T> clazz);

        /**
         * Adds an instance to the services collection
         *
         * @param serviceId The service ID
         * @param instance The instance.
         * @param setAsDefault Optional: set as the default AI service for type T
         * @param clazz The class of the instance.
         */
        @Deprecated
        <T extends AIService> Builder withAIService(
                @Nullable String serviceId, T instance, boolean setAsDefault, Class<T> clazz);

        /**
         * Adds a factory method to the services collection
         *
         * @param serviceId The service ID
         * @param factory The factory method that creates the AI service instances of type T.
         * @param setAsDefault Optional: set as the default AI service for type T
         * @param clazz The class of the instance.
         */
        @Deprecated
        <T extends AIService> Builder withAIServiceFactory(
                @Nullable String serviceId,
                Function<KernelConfig, T> factory,
                boolean setAsDefault,
                Class<T> clazz);

        /**
         * Add a semantic text memory entity to the kernel to be built.
         *
         * @param memory Semantic text memory entity to add.
         * @return Updated kernel builder including the semantic text memory entity.
         */
        @Deprecated
        Builder withMemory(SemanticTextMemory memory);

        /**
         * Add memory storage and an embedding generator to the kernel to be built.
         *
         * @param storage Storage to add.
         * @param embeddingGenerator Embedding generator to add.
         * @return Updated kernel builder including the memory storage and embedding generator.
         */
        @Deprecated
        Builder withMemoryStorageAndTextEmbeddingGeneration(
                MemoryStore storage, TextEmbeddingGeneration embeddingGenerator);

        /**
         * Add plugins to the kernel to be built.
         *
         * @param plugins Plugins to add.
         * @return Updated kernel builder including the plugins.
         * @since 1.0.0
         */
        Builder withPlugins(Plugin... plugins);
    }
}
