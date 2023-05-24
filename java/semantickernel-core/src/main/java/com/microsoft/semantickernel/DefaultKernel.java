// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.ai.AIException;
import com.microsoft.semantickernel.builders.FunctionBuilders;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.coreskills.SkillImporter;
import com.microsoft.semantickernel.exceptions.NotSupportedException;
import com.microsoft.semantickernel.exceptions.SkillsNotFoundException;
import com.microsoft.semantickernel.memory.MemoryStore;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.orchestration.*;
import com.microsoft.semantickernel.semanticfunctions.SemanticFunctionConfig;
import com.microsoft.semantickernel.skilldefinition.DefaultSkillCollection;
import com.microsoft.semantickernel.skilldefinition.FunctionNotFound;
import com.microsoft.semantickernel.skilldefinition.ReadOnlyFunctionCollection;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import com.microsoft.semantickernel.templateengine.DefaultPromptTemplateEngine;
import com.microsoft.semantickernel.templateengine.PromptTemplateEngine;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;
import com.microsoft.semantickernel.textcompletion.TextCompletion;

import jakarta.inject.Inject;

import reactor.core.publisher.Mono;

import java.util.Arrays;
import java.util.Map;
import java.util.function.Function;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

public class DefaultKernel implements Kernel {

    private final KernelConfig kernelConfig;
    private final DefaultSkillCollection defaultSkillCollection;
    private final PromptTemplateEngine promptTemplateEngine;
    private MemoryStore memoryStore;

    @Inject
    public DefaultKernel(
            KernelConfig kernelConfig,
            PromptTemplateEngine promptTemplateEngine,
            MemoryStore memoryStore) {
        if (kernelConfig == null) {
            throw new IllegalArgumentException();
        }

        this.kernelConfig = kernelConfig;
        this.promptTemplateEngine = promptTemplateEngine;
        this.defaultSkillCollection = new DefaultSkillCollection();
        this.memoryStore = memoryStore;

        kernelConfig.getSkills().forEach(this::registerSemanticFunction);
    }

    @Override
    public <T> T getService(String serviceId, Class<T> clazz) {
        if (TextCompletion.class.isAssignableFrom(clazz)) {
            Function<Kernel, TextCompletion> factory =
                    kernelConfig.getTextCompletionServiceOrDefault(serviceId);
            if (factory == null) {
                throw new KernelException(
                        KernelException.ErrorCodes.ServiceNotFound,
                        "No text completion service available");
            }

            return (T) factory.apply(this);
        } else {
            // TODO correct exception
            throw new NotSupportedException(
                    "The kernel service collection doesn't support the type " + clazz.getName());
        }
    }

    @Override
    public KernelConfig getConfig() {
        return kernelConfig;
    }

    @Override
    public <
                    RequestConfiguration,
                    ContextType extends SKContext<ContextType>,
                    FunctionType extends SKFunction<RequestConfiguration, ContextType>>
            FunctionType registerSemanticFunction(FunctionType func) {
        if (!(func instanceof RegistrableSkFunction)) {
            throw new RuntimeException("This function does not implement RegistrableSkFunction");
        }
        ((RegistrableSkFunction) func).registerOnKernel(this);
        defaultSkillCollection.addSemanticFunction(func);
        return func;
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
                            return DefaultCompletionSKFunction.createFunction(
                                    skillName, entry.getKey(), entry.getValue());
                        })
                .forEach(this::registerSemanticFunction);

        ReadOnlyFunctionCollection collection = getSkill(skillName);
        if (collection == null) {
            throw new SkillsNotFoundException();
        }
        return collection;
    }

    @Override
    public ReadOnlyFunctionCollection importSkill(
            Object skillInstance, @Nullable String skillName) {
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
        return FunctionBuilders.getCompletionBuilder(this);
    }

    @Override
    public ReadOnlyFunctionCollection getSkill(String skillName) throws FunctionNotFound {
        ReadOnlyFunctionCollection functions = this.defaultSkillCollection.getFunctions(skillName);
        if (functions == null) {
            throw new FunctionNotFound(skillName);
        }

        return functions;
    }

    @Override
    public PromptTemplateEngine getPromptTemplateEngine() {
        return promptTemplateEngine;
    }

    @Override
    public MemoryStore getMemoryStore() {
        return memoryStore;
    }

    @Override
    public void registerMemory(@Nonnull SemanticTextMemory memory) {
        throw new NotSupportedException("Not implemented");
    }

    @Override
    public Mono<SKContext<?>> runAsync(SKFunction<?, ?>... pipeline) {
        return runAsync(SKBuilders.variables().build(), pipeline);
    }

    @Override
    public Mono<SKContext<?>> runAsync(String input, SKFunction<?, ?>... pipeline) {
        return runAsync(SKBuilders.variables().build(input), pipeline);
    }

    @Override
    public Mono<SKContext<?>> runAsync(ContextVariables variables, SKFunction<?, ?>... pipeline) {
        if (pipeline == null || pipeline.length == 0) {
            throw new SKException("No parameters provided to pipeline");
        }
        // TODO: The SemanticTextMemory can be null, but there should be a way to provide it.
        //       Not sure registerMemory is the right way.
        Mono<SKContext<?>> pipelineBuilder =
                Mono.just(pipeline[0].buildContext(variables, null, getSkills()));

        for (SKFunction f : Arrays.asList(pipeline)) {
            pipelineBuilder =
                    pipelineBuilder.flatMap(
                            newContext -> {
                                SKContext context =
                                        f.buildContext(
                                                newContext.getVariables(),
                                                newContext.getSemanticMemory(),
                                                newContext.getSkills());
                                return f.invokeAsync(context, null);
                            });
        }

        return pipelineBuilder;
    }

    public static class Builder implements Kernel.InternalBuilder {

        @Override
        public Kernel build(
                KernelConfig kernelConfig,
                @Nullable PromptTemplateEngine promptTemplateEngine,
                @Nullable MemoryStore memoryStore) {
            if (promptTemplateEngine == null) {
                promptTemplateEngine = new DefaultPromptTemplateEngine();
            }

            if (kernelConfig == null) {
                throw new AIException(
                        AIException.ErrorCodes.InvalidConfiguration,
                        "It is required to set a kernelConfig to build a kernel");
            }

            return new DefaultKernel(kernelConfig, promptTemplateEngine, memoryStore);
        }
    }
}
