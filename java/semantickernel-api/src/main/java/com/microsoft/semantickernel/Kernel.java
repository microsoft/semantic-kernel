// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.ai.embeddings.TextEmbeddingGeneration;
import com.microsoft.semantickernel.builders.BuildersSingleton;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.memory.MemoryStore;
import com.microsoft.semantickernel.memory.NullMemory;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.orchestration.ContextVariables;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.orchestration.SKFunction;
import com.microsoft.semantickernel.services.AIService;
import com.microsoft.semantickernel.services.AIServiceCollection;
import com.microsoft.semantickernel.services.AIServiceProvider;
import com.microsoft.semantickernel.templateengine.PromptTemplateEngine;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;

import reactor.core.publisher.Mono;

import java.util.function.Function;
import java.util.function.Supplier;

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
    <T extends AIService> T getService(@Nullable String name, Class<T> clazz)
            throws KernelException;

    /** Registers a semantic function on this kernel */
    <RequestConfiguration, FunctionType extends SKFunction<RequestConfiguration>>
            FunctionType registerSemanticFunction(FunctionType semanticFunctionDefinition);

    /** Obtains a semantic function with the given name */
    SKFunction getFunction(String skill, String function);

    class Builder {
        @Nullable private KernelConfig config = null;
        @Nullable private PromptTemplateEngine promptTemplateEngine = null;
        @Nullable private AIServiceCollection aiServices = new AIServiceCollection();
        private Supplier<SemanticTextMemory> memoryFactory = () -> new NullMemory();
        private Supplier<MemoryStore> memoryStorageFactory = null;
        ;

        /**
         * Set the kernel configuration
         *
         * @param kernelConfig Kernel configuration
         * @return Builder
         */
        public Builder withConfiguration(KernelConfig kernelConfig) {
            this.config = kernelConfig;
            return this;
        }

        /**
         * Add prompt template engine to the kernel to be built.
         *
         * @param promptTemplateEngine Prompt template engine to add.
         * @return Updated kernel builder including the prompt template engine.
         */
        public Builder withPromptTemplateEngine(PromptTemplateEngine promptTemplateEngine) {
            Verify.notNull(promptTemplateEngine);
            this.promptTemplateEngine = promptTemplateEngine;
            return this;
        }

        /**
         * Add memory storage to the kernel to be built.
         *
         * @param storage Storage to add.
         * @return Updated kernel builder including the memory storage.
         */
        public Builder withMemoryStorage(MemoryStore storage) {
            Verify.notNull(storage);
            this.memoryStorageFactory = () -> storage;
            return this;
        }

        /**
         * Add memory storage factory to the kernel.
         *
         * @param factory The storage factory.
         * @return Updated kernel builder including the memory storage.
         */
        public Builder withMemoryStorage(Supplier<MemoryStore> factory) {
            Verify.notNull(factory);
            this.memoryStorageFactory = factory::get;
            return this;
        }

        /**
         * Adds an instance to the services collection
         *
         * @param instance The instance.
         * @return The builder.
         */
        public <T extends AIService> Builder withDefaultAIService(T instance) {
            Class<T> clazz = (Class<T>) instance.getClass();
            this.aiServices.setService(instance, clazz);
            return this;
        }

        /**
         * Adds an instance to the services collection
         *
         * @param instance The instance.
         * @param clazz The class of the instance.
         * @return The builder.
         */
        public <T extends AIService> Builder withDefaultAIService(T instance, Class<T> clazz) {
            this.aiServices.setService(instance, clazz);
            return this;
        }

        /**
         * Adds a factory method to the services collection
         *
         * @param factory The factory method that creates the AI service instances of type T.
         * @param clazz The class of the instance.
         */
        public <T extends AIService> Builder withDefaultAIService(
                Supplier<T> factory, Class<T> clazz) {
            this.aiServices.setService(factory, clazz);
            return this;
        }

        /**
         * Adds an instance to the services collection
         *
         * @param serviceId The service ID
         * @param instance The instance.
         * @param setAsDefault Optional: set as the default AI service for type T
         * @param clazz The class of the instance.
         */
        public <T extends AIService> Builder withAIService(
                @Nullable String serviceId, T instance, boolean setAsDefault, Class<T> clazz) {
            this.aiServices.setService(serviceId, instance, setAsDefault, clazz);
            return this;
        }

        /**
         * Adds a factory method to the services collection
         *
         * @param serviceId The service ID
         * @param factory The factory method that creates the AI service instances of type T.
         * @param setAsDefault Optional: set as the default AI service for type T
         * @param clazz The class of the instance.
         */
        public <T extends AIService> Builder withAIServiceFactory(
                @Nullable String serviceId,
                Function<KernelConfig, T> factory,
                boolean setAsDefault,
                Class<T> clazz) {
            this.aiServices.setService(
                    serviceId, (Supplier<T>) () -> factory.apply(this.config), setAsDefault, clazz);
            return this;
        }

        /**
         * Add a semantic text memory entity to the kernel to be built.
         *
         * @param memory Semantic text memory entity to add.
         * @return Updated kernel builder including the semantic text memory entity.
         */
        public Builder withMemory(SemanticTextMemory memory) {
            Verify.notNull(memory);
            this.memoryFactory = () -> memory;
            return this;
        }

        /**
         * Add memory storage and an embedding generator to the kernel to be built.
         *
         * @param storage Storage to add.
         * @param embeddingGenerator Embedding generator to add.
         * @return Updated kernel builder including the memory storage and embedding generator.
         */
        public Builder withMemoryStorageAndTextEmbeddingGeneration(
                MemoryStore storage, TextEmbeddingGeneration embeddingGenerator) {
            Verify.notNull(storage);
            Verify.notNull(embeddingGenerator);
            this.memoryFactory =
                    () ->
                            SKBuilders.semanticTextMemory()
                                    .setEmbeddingGenerator(embeddingGenerator)
                                    .setStorage(storage)
                                    .build();
            return this;
        }

        /**
         * Build the kernel
         *
         * @return Kernel
         */
        public Kernel build() {
            if (config == null) {
                config = SKBuilders.kernelConfig().build();
            }

            return BuildersSingleton.INST
                    .getKernelBuilder()
                    .build(
                            config,
                            promptTemplateEngine,
                            memoryFactory.get(),
                            memoryStorageFactory == null ? null : memoryStorageFactory.get(),
                            aiServices.build());
        }
    }

    interface InternalBuilder {
        Kernel build(
                KernelConfig kernelConfig,
                @Nullable PromptTemplateEngine promptTemplateEngine,
                @Nullable SemanticTextMemory memory,
                @Nullable MemoryStore memoryStore,
                @Nullable AIServiceProvider aiServiceProvider);
    }
}
