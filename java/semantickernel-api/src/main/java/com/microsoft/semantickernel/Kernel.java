// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.builders.BuildersSingleton;
import com.microsoft.semantickernel.memory.MemoryStore;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.orchestration.ContextVariables;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.orchestration.SKFunction;
import com.microsoft.semantickernel.templateengine.PromptTemplateEngine;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;

import reactor.core.publisher.Mono;

import javax.annotation.Nullable;

/** Interface for the semantic kernel. */
public interface Kernel extends SkillExecutor {

    /**
     * Settings required to execute functions, including details about AI dependencies, e.g.
     * endpoints and API keys.
     */
    KernelConfig getConfig();

    /**
     * Reference to the engine rendering prompt templates
     *
     * @return Reference to the engine rendering prompt templates
     */
    PromptTemplateEngine getPromptTemplateEngine();

    /**
     * Get the SemanticTextMemory in use.
     *
     * @return the SemanticTextMemory in use
     */
    SemanticTextMemory getMemory();

    /**
     * Run a pipeline composed of synchronous and asynchronous functions.
     *
     * @param pipeline List of functions
     * @return Result of the function composition
     */
    Mono<SKContext> runAsync(SKFunction<?>... pipeline);

    /**
     * Run a pipeline composed of synchronous and asynchronous functions.
     *
     * @param input Input to process
     * @param pipeline List of functions
     * @return Result of the function composition
     */
    Mono<SKContext> runAsync(String input, SKFunction<?>... pipeline);

    /**
     * Run a pipeline composed of synchronous and asynchronous functions.
     *
     * @param variables variables to initialise the context with
     * @param pipeline List of functions
     * @return Result of the function composition
     */
    Mono<SKContext> runAsync(ContextVariables variables, SKFunction<?>... pipeline);

    /**
     * Get a completion function builder, functions created with this builder will be registered on
     * the kernel
     */
    CompletionSKFunction.Builder getSemanticFunctionBuilder();

    /** Obtains the service with the given name and type */
    <T> T getService(@Nullable String name, Class<T> clazz) throws KernelException;

    /** Registers a semantic function on this kernel */
    <RequestConfiguration, FunctionType extends SKFunction<RequestConfiguration>>
            FunctionType registerSemanticFunction(FunctionType semanticFunctionDefinition);

    /** Obtains a semantic function with the given name */
    SKFunction getFunction(String skill, String function);

    class Builder {
        @Nullable private KernelConfig kernelConfig = null;
        @Nullable private PromptTemplateEngine promptTemplateEngine = null;
        @Nullable private MemoryStore memoryStore = null;
        @Nullable private SemanticTextMemory memory = null;

        /**
         * Set the kernel configuration
         *
         * @param kernelConfig Kernel configuration
         * @return Builder
         */
        public Builder setKernelConfig(KernelConfig kernelConfig) {
            this.kernelConfig = kernelConfig;
            return this;
        }

        /**
         * Set the prompt template engine
         *
         * @param promptTemplateEngine Prompt template engine
         * @return Builder
         */
        public Builder setPromptTemplateEngine(PromptTemplateEngine promptTemplateEngine) {
            this.promptTemplateEngine = promptTemplateEngine;
            return this;
        }

        /**
         * Set the memory store
         *
         * @param memoryStore Memory store
         * @return Builder
         */
        public Builder withMemoryStore(MemoryStore memoryStore) {
            this.memoryStore = memoryStore;
            return this;
        }

        /**
         * Set the memory
         *
         * @param memory Memory
         * @return Builder
         */
        public Builder withMemory(SemanticTextMemory memory) {
            this.memory = memory;
            return this;
        }

        /**
         * Build the kernel
         *
         * @return Kernel
         */
        public Kernel build() {
            if (kernelConfig == null) {
                throw new IllegalStateException("Must provide a kernel configuration");
            }

            return BuildersSingleton.INST
                    .getKernelBuilder()
                    .build(kernelConfig, promptTemplateEngine, memory, memoryStore);
        }
    }

    interface InternalBuilder {
        Kernel build(
                KernelConfig kernelConfig,
                @Nullable PromptTemplateEngine promptTemplateEngine,
                @Nullable SemanticTextMemory memory,
                @Nullable MemoryStore memoryStore);
    }
}
