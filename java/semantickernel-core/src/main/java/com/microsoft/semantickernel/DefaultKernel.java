// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.builders.FunctionBuilders;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.coreskills.SkillImporter;
import com.microsoft.semantickernel.exceptions.NotSupportedException;
import com.microsoft.semantickernel.exceptions.SkillsNotFoundException;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.orchestration.ContextVariables;
import com.microsoft.semantickernel.orchestration.DefaultCompletionSKFunction;
import com.microsoft.semantickernel.orchestration.RegistrableSkFunction;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.orchestration.SKFunction;
import com.microsoft.semantickernel.semanticfunctions.SemanticFunctionConfig;
import com.microsoft.semantickernel.skilldefinition.DefaultSkillCollection;
import com.microsoft.semantickernel.skilldefinition.FunctionNotFound;
import com.microsoft.semantickernel.skilldefinition.ReadOnlyFunctionCollection;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
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
    @Nullable private SemanticTextMemory memory; // TODO: make this final

    @Inject
    public DefaultKernel(
            KernelConfig kernelConfig,
            PromptTemplateEngine promptTemplateEngine,
            @Nullable SemanticTextMemory memory) {
        if (kernelConfig == null) {
            throw new IllegalArgumentException();
        }

        this.kernelConfig = kernelConfig;
        this.promptTemplateEngine = promptTemplateEngine;
        this.defaultSkillCollection = new DefaultSkillCollection();

        if (memory != null) {
            this.memory = memory.copy();
        } else {
            this.memory = null;
        }

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
    /*
      private static FunctionCollection importSkill(Object skillInstance, String skillName) {


        skillInstance.getClass().getMethods()
                .
        MethodInfo[] methods = skillInstance.GetType()
                .GetMethods(BindingFlags.Static | BindingFlags.Instance | BindingFlags.Public | BindingFlags.InvokeMethod);
        log.LogTrace("Methods found {0}", methods.Length);

        // Filter out null functions
        IEnumerable<ISKFunction> functions = from method in methods select SKFunction.FromNativeMethod(method, skillInstance, skillName, log);
        List<SKFunction> result = (from function in functions where function != null select function).ToList();
        log.LogTrace("Methods imported {0}", result.Count);

        // Fail if two functions have the same name
        var uniquenessCheck = new HashSet<string>(from x in result select x.Name, StringComparer.OrdinalIgnoreCase);
        if (result.Count > uniquenessCheck.Count)
        {
          throw new KernelException(
                  KernelException.ErrorCodes.FunctionOverloadNotSupported,
                  "Function overloads are not supported, please differentiate function names");
        }

        return result;
      }
    */

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
    /*
    private SKFunction createSemanticFunction(
        String skillName, String functionName, SemanticFunctionConfig functionConfig) {


      CompletionSKFunction func =
          CompletionSKFunction.fromSemanticConfig(
              skillName, functionName, functionConfig, promptTemplateEngine);

      // Connect the function to the current kernel skill collection, in case the function
      // is invoked manually without a context and without a way to find other functions.
      func.setDefaultSkillCollection(this.skillCollection);

      func.setAIConfiguration(
          CompleteRequestSettings.fromCompletionConfig(
              functionConfig.getConfig().getCompletionConfig()));

      // Note: the service is instantiated using the kernel configuration state when the function
      // is invoked
      func.setAIService(() -> this.getService(null, TextCompletion.class));

      this.skillCollection = this.skillCollection.addSemanticFunction(func);

      return func;
    }*/

    @Override
    public void registerMemory(@Nonnull SemanticTextMemory memory) {
        this.memory = memory != null ? memory.copy() : null;
    }

    /// <inheritdoc/>
    /*
    public ReadOnlySKContext createNewContext() {
        return ReadOnlySKContext.build(
                ReadOnlyContextVariables.build(),
                null,
                () -> skillCollection);
    }

     */

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

        Mono<SKContext<?>> pipelineBuilder =
                Mono.just(pipeline[0].buildContext(variables, memory, getSkills()));

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
}
