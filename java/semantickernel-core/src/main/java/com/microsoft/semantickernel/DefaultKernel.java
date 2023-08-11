// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.ai.AIException;
import com.microsoft.semantickernel.ai.embeddings.TextEmbeddingGeneration;
import com.microsoft.semantickernel.coreskills.SkillImporter;
import com.microsoft.semantickernel.exceptions.SkillsNotFoundException;
import com.microsoft.semantickernel.exceptions.SkillsNotFoundException.ErrorCodes;
import com.microsoft.semantickernel.extensions.KernelExtensions;
import com.microsoft.semantickernel.memory.MemoryConfiguration;
import com.microsoft.semantickernel.memory.MemoryStore;
import com.microsoft.semantickernel.memory.NullMemory;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.orchestration.ContextVariables;
import com.microsoft.semantickernel.orchestration.RegistrableSkFunction;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.orchestration.SKFunction;
import com.microsoft.semantickernel.semanticfunctions.SemanticFunctionConfig;
import com.microsoft.semantickernel.services.AIService;
import com.microsoft.semantickernel.services.AIServiceCollection;
import com.microsoft.semantickernel.services.AIServiceProvider;
import com.microsoft.semantickernel.skilldefinition.DefaultSkillCollection;
import com.microsoft.semantickernel.skilldefinition.FunctionNotFound;
import com.microsoft.semantickernel.skilldefinition.ReadOnlyFunctionCollection;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import com.microsoft.semantickernel.templateengine.DefaultPromptTemplateEngine;
import com.microsoft.semantickernel.templateengine.PromptTemplateEngine;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;
import jakarta.inject.Inject;
import java.util.Arrays;
import java.util.Map;
import java.util.function.Function;
import java.util.function.Supplier;
import javax.annotation.Nonnull;
import javax.annotation.Nullable;
import reactor.core.publisher.Mono;

public class DefaultKernel implements Kernel {

    private final KernelConfig kernelConfig;
    private final DefaultSkillCollection defaultSkillCollection;
    private final PromptTemplateEngine promptTemplateEngine;
    private final AIServiceProvider aiServiceProvider;
    private SemanticTextMemory memory;

    @Inject
    public DefaultKernel(
            KernelConfig kernelConfig,
            PromptTemplateEngine promptTemplateEngine,
            @Nullable SemanticTextMemory memoryStore,
            AIServiceProvider aiServiceProvider) {
        if (kernelConfig == null) {
            throw new IllegalArgumentException();
        }

        this.kernelConfig = kernelConfig;
        this.aiServiceProvider = aiServiceProvider;
        this.promptTemplateEngine = promptTemplateEngine;
        this.defaultSkillCollection = new DefaultSkillCollection();

        if (memoryStore != null) {
            this.memory = memoryStore.copy();
        } else {
            this.memory = new NullMemory();
        }
    }

    @Override
    public <T extends AIService> T getService(String serviceId, Class<T> clazz) {

        T service = aiServiceProvider.getService(serviceId, clazz);

        if (service == null) {
            throw new KernelException(
                    KernelException.ErrorCodes.ServiceNotFound,
                    "Service of type "
                            + clazz.getName()
                            + " and name "
                            + serviceId
                            + " not registered");
        } else {
            return service;
        }
    }

    @Override
    public KernelConfig getConfig() {
        return kernelConfig;
    }

    @Override
    public <RequestConfiguration, FunctionType extends SKFunction<RequestConfiguration>>
            FunctionType registerSemanticFunction(FunctionType func) {
        if (!(func instanceof RegistrableSkFunction)) {
            throw new RuntimeException("This function does not implement RegistrableSkFunction");
        }
        ((RegistrableSkFunction) func).registerOnKernel(this);
        defaultSkillCollection.addSemanticFunction(func);
        return func;
    }

    @Override
    public SKFunction<?> getFunction(String skill, String function) {
        return defaultSkillCollection.getFunction(skill, function, null);
    }

    /*
    /// <inheritdoc/>
    public SKFunction registerSemanticFunction(
        String skillName, String functionName, SemanticFunctionConfig functionConfig) {
      // Future-proofing the name not to contain special chars
      // Verify.ValidSkillName(skillName);
      // Verify.ValidFunctionName(functionName);

      skillCollection = skillCollection.addSemanticFunction(func);

      return this.createSemanticFunction(skillName, functionName, functionConfig);
    }*/

    /// <summary>
    /// Import a set of functions from the given skill. The functions must have the `SKFunction`
    // attribute.
    /// Once these functions are imported, the prompt templates can use functions to import content
    // at runtime.
    /// </summary>
    /// <param name="skillInstance">Instance of a class containing functions</param>
    /// <param name="skillName">Name of the skill for skill collection and prompt templates. If the
    // value is empty functions are registered in the global namespace.</param>
    /// <returns>A list of all the semantic functions found in the directory, indexed by function
    // name.</returns>
    @Override
    public ReadOnlyFunctionCollection importSkill(
            String skillName, Map<String, SemanticFunctionConfig> skills)
            throws SkillsNotFoundException {
        skills.entrySet().stream()
                .map(
                        (entry) -> {
                            return SKBuilders.completionFunctions()
                                    .withKernel(this)
                                    .setSkillName(skillName)
                                    .setFunctionName(entry.getKey())
                                    .setSemanticFunctionConfig(entry.getValue())
                                    .build();
                        })
                .forEach(this::registerSemanticFunction);

        ReadOnlyFunctionCollection collection = getSkill(skillName);
        if (collection == null) {
            throw new SkillsNotFoundException(ErrorCodes.SKILLS_NOT_FOUND);
        }
        return collection;
    }

    @Override
    public ReadOnlyFunctionCollection importSkill(
            Object skillInstance, @Nullable String skillName) {
        if (skillInstance instanceof String) {
            throw new KernelException(
                    KernelException.ErrorCodes.FunctionNotAvailable,
                    "Called importSkill with a string argument, it is likely the intention was to"
                            + " call importSkillFromDirectory");
        }

        if (skillName == null || skillName.isEmpty()) {
            skillName = ReadOnlySkillCollection.GlobalSkill;
        }

        // skill = new Dictionary<string, ISKFunction>(StringComparer.OrdinalIgnoreCase);
        ReadOnlyFunctionCollection functions =
                SkillImporter.importSkill(skillInstance, skillName, () -> defaultSkillCollection);

        DefaultSkillCollection newSkills =
                functions.getAll().stream()
                        .reduce(
                                new DefaultSkillCollection(),
                                DefaultSkillCollection::addNativeFunction,
                                DefaultSkillCollection::merge);

        this.defaultSkillCollection.merge(newSkills);

        return functions;
    }

    @Override
    public ReadOnlySkillCollection getSkills() {
        return defaultSkillCollection;
    }

    @Override
    public CompletionSKFunction.Builder getSemanticFunctionBuilder() {
        return SKBuilders.completionFunctions().withKernel(this);
    }

    @Override
    public ReadOnlyFunctionCollection getSkill(String skillName) throws FunctionNotFound {
        ReadOnlyFunctionCollection functions = this.defaultSkillCollection.getFunctions(skillName);
        if (functions == null) {
            throw new FunctionNotFound(FunctionNotFound.ErrorCodes.FUNCTION_NOT_FOUND, skillName);
        }

        return functions;
    }

    @Override
    public ReadOnlyFunctionCollection importSkillFromDirectory(
            String skillName, String parentDirectory, String skillDirectoryName) {
        Map<String, SemanticFunctionConfig> skills =
                KernelExtensions.importSemanticSkillFromDirectory(
                        parentDirectory, skillDirectoryName, promptTemplateEngine);
        return importSkill(skillName, skills);
    }

    @Override
    public void importSkillsFromDirectory(String parentDirectory, String... skillNames) {
        Arrays.stream(skillNames)
                .forEach(
                        skill -> {
                            importSkillFromDirectory(skill, parentDirectory, skill);
                        });
    }

    @Override
    public ReadOnlyFunctionCollection importSkillFromDirectory(
            String skillName, String parentDirectory) {
        return importSkillFromDirectory(skillName, parentDirectory, skillName);
    }

    @Override
    public ReadOnlyFunctionCollection importSkillFromResources(
            String pluginDirectory, String skillName, String functionName) {
        return importSkillFromResources(pluginDirectory, skillName, functionName, null);
    }

    @Override
    public ReadOnlyFunctionCollection importSkillFromResources(
            String pluginDirectory, String skillName, String functionName, @Nullable Class clazz) {
        Map<String, SemanticFunctionConfig> skills =
                KernelExtensions.importSemanticSkillFromResourcesDirectory(
                        pluginDirectory, skillName, functionName, clazz, promptTemplateEngine);
        return importSkill(skillName, skills);
    }

    @Override
    public PromptTemplateEngine getPromptTemplateEngine() {
        return promptTemplateEngine;
    }

    @Override
    public SemanticTextMemory getMemory() {
        return memory;
    }

    public void registerMemory(@Nonnull SemanticTextMemory memory) {
        this.memory = memory;
    }

    @Override
    public Mono<SKContext> runAsync(SKFunction<?>... pipeline) {
        return runAsync(SKBuilders.variables().build(), pipeline);
    }

    @Override
    public Mono<SKContext> runAsync(String input, SKFunction<?>... pipeline) {
        return runAsync(SKBuilders.variables().withInput(input).build(), pipeline);
    }

    @Override
    public Mono<SKContext> runAsync(ContextVariables variables, SKFunction<?>... pipeline) {
        if (pipeline == null || pipeline.length == 0) {
            throw new SKException("No parameters provided to pipeline");
        }
        // TODO: The SemanticTextMemory can be null, but there should be a way to provide it.
        //       Not sure registerMemory is the right way.
        Mono<SKContext> pipelineBuilder =
                Mono.just(
                        SKBuilders.context()
                                .setVariables(variables)
                                .setSkills(getSkills())
                                .build());

        for (SKFunction f : Arrays.asList(pipeline)) {
            pipelineBuilder =
                    pipelineBuilder
                            .switchIfEmpty(
                                    Mono.fromCallable(
                                            () -> {
                                                // Previous pipeline did not produce a result
                                                return SKBuilders.context()
                                                        .setVariables(variables)
                                                        .setSkills(getSkills())
                                                        .build();
                                            }))
                            .flatMap(
                                    newContext -> {
                                        SKContext context =
                                                SKBuilders.context()
                                                        .setVariables(newContext.getVariables())
                                                        .setMemory(newContext.getSemanticMemory())
                                                        .setSkills(newContext.getSkills())
                                                        .build();
                                        return f.invokeAsync(context, null);
                                    });
        }

        return pipelineBuilder;
    }

    public static class Builder implements Kernel.Builder {
        @Nullable private KernelConfig config = null;
        @Nullable private PromptTemplateEngine promptTemplateEngine = null;
        @Nullable private final AIServiceCollection aiServices = new AIServiceCollection();
        private Supplier<SemanticTextMemory> memoryFactory = NullMemory::new;
        private Supplier<MemoryStore> memoryStorageFactory = null;

        /**
         * Set the kernel configuration
         *
         * @param kernelConfig Kernel configuration
         * @return Builder
         */
        public Kernel.Builder withConfiguration(KernelConfig kernelConfig) {
            this.config = kernelConfig;
            return this;
        }

        /**
         * Add prompt template engine to the kernel to be built.
         *
         * @param promptTemplateEngine Prompt template engine to add.
         * @return Updated kernel builder including the prompt template engine.
         */
        public Kernel.Builder withPromptTemplateEngine(PromptTemplateEngine promptTemplateEngine) {
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
        public Kernel.Builder withMemoryStorage(MemoryStore storage) {
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
        public Kernel.Builder withMemoryStorage(Supplier<MemoryStore> factory) {
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
        public <T extends AIService> Kernel.Builder withDefaultAIService(T instance) {
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
        public <T extends AIService> Kernel.Builder withDefaultAIService(
                T instance, Class<T> clazz) {
            this.aiServices.setService(instance, clazz);
            return this;
        }

        /**
         * Adds a factory method to the services collection
         *
         * @param factory The factory method that creates the AI service instances of type T.
         * @param clazz The class of the instance.
         */
        public <T extends AIService> Kernel.Builder withDefaultAIService(
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
        public <T extends AIService> Kernel.Builder withAIService(
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
        public <T extends AIService> Kernel.Builder withAIServiceFactory(
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
        public Kernel.Builder withMemory(SemanticTextMemory memory) {
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
        public Kernel.Builder withMemoryStorageAndTextEmbeddingGeneration(
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

            return build(
                    config,
                    promptTemplateEngine,
                    memoryFactory.get(),
                    memoryStorageFactory == null ? null : memoryStorageFactory.get(),
                    aiServices.build());
        }

        private Kernel build(
                KernelConfig kernelConfig,
                @Nullable PromptTemplateEngine promptTemplateEngine,
                @Nullable SemanticTextMemory memory,
                @Nullable MemoryStore memoryStore,
                @Nullable AIServiceProvider aiServiceProvider) {
            if (promptTemplateEngine == null) {
                promptTemplateEngine = new DefaultPromptTemplateEngine();
            }

            if (kernelConfig == null) {
                throw new AIException(
                        AIException.ErrorCodes.InvalidConfiguration,
                        "It is required to set a kernelConfig to build a kernel");
            }

            DefaultKernel kernel =
                    new DefaultKernel(
                            kernelConfig, promptTemplateEngine, memory, aiServiceProvider);

            if (memoryStore != null) {
                MemoryConfiguration.useMemory(kernel, memoryStore, null);
            }

            return kernel;
        }
    }
}
