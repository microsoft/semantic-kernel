// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.coreskills.SkillImporter;
import com.microsoft.semantickernel.exceptions.NotSupportedException;
import com.microsoft.semantickernel.exceptions.SkillsNotFoundException;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.orchestration.*;
import com.microsoft.semantickernel.semanticfunctions.SemanticFunctionConfig;
import com.microsoft.semantickernel.skilldefinition.DefaultReadOnlySkillCollection;
import com.microsoft.semantickernel.skilldefinition.FunctionNotFound;
import com.microsoft.semantickernel.skilldefinition.ReadOnlyFunctionCollection;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import com.microsoft.semantickernel.templateengine.PromptTemplateEngine;
import com.microsoft.semantickernel.textcompletion.TextCompletion;

import reactor.core.publisher.Mono;

import java.util.Arrays;
import java.util.Map;
import java.util.function.Function;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

public class KernelDefault implements Kernel {

    private final KernelConfig kernelConfig;
    private ReadOnlySkillCollection skillCollection;
    private final PromptTemplateEngine promptTemplateEngine;
    @Nullable private SemanticTextMemory memory; // TODO: make this final

    public KernelDefault(
            KernelConfig kernelConfig,
            PromptTemplateEngine promptTemplateEngine,
            ReadOnlySkillCollection skillCollection) {
        if (kernelConfig == null) {
            throw new IllegalArgumentException();
        }

        this.kernelConfig = kernelConfig;
        this.promptTemplateEngine = promptTemplateEngine;
        this.skillCollection = skillCollection;

        if (kernelConfig.getSkillDefinitions() != null) {
            kernelConfig
                    .getSkillDefinitions()
                    .forEach(
                            semanticFunctionBuilder -> {
                                semanticFunctionBuilder.registerOnKernel(this);
                            });
        }
    }

    @Override
    public <T> T getService(@Nullable String name, Class<T> clazz) throws KernelException {
        if (TextCompletion.class.isAssignableFrom(clazz)) {
            name = kernelConfig.getTextCompletionServiceIdOrDefault(name);
            Function<Kernel, TextCompletion> factory = kernelConfig.getTextCompletionServices(name);
            if (factory == null) {
                // TODO correct exception
                throw new KernelException();
                // throw new KernelException(KernelException.ErrorCodes.ServiceNotFound, "No text
                // completion service available");
            }

            return (T) factory.apply(this);
        } else {
            // TODO correct exception
            throw new NotSupportedException(
                    "The kernel service collection doesn't support the type " + clazz.getName());
        }
    }

    @Override
    public <
                    RequestConfiguration,
                    ContextType extends ReadOnlySKContext<ContextType>,
                    Result extends SKFunction<RequestConfiguration, ContextType>>
            Result registerSemanticFunction(
                    SemanticFunctionDefinition<RequestConfiguration, ContextType, Result>
                            semanticFunctionDefinition) {
        Result func = (Result) semanticFunctionDefinition.build(this);
        registerSemanticFunction(func);
        return func;
    }
    /*
       @Override
       public <RequestConfiguration, ContextType extends ReadOnlySKContext<ContextType>> SemanticSKFunction<RequestConfiguration, ContextType> registerSemanticFunction(
               SemanticFunctionBuilder<RequestConfiguration, ContextType> semanticFunctionBuilder) {
           SemanticSKFunction<RequestConfiguration, ContextType> func = semanticFunctionBuilder.build(this);
           registerSemanticFunction(func);
           return func;
       }

    */

    @Override
    public KernelConfig getConfig() {
        return kernelConfig;
    }

    private <RequestConfiguration, ContextType extends ReadOnlySKContext<ContextType>>
            void registerSemanticFunction(SKFunction<RequestConfiguration, ContextType> func) {
        skillCollection = skillCollection.addSemanticFunction(func);
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
    public ReadOnlyFunctionCollection importSkills(
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
            // this._log.LogTrace("Importing skill {0} in the global namespace",
            // skillInstance.GetType().FullName);
        }

        // skill = new Dictionary<string, ISKFunction>(StringComparer.OrdinalIgnoreCase);
        ReadOnlyFunctionCollection functions =
                SkillImporter.importSkill(skillInstance, skillName, () -> skillCollection);

        ReadOnlySkillCollection newSkills =
                functions.getAll().stream()
                        .reduce(
                                new DefaultReadOnlySkillCollection(),
                                ReadOnlySkillCollection::addNativeFunction,
                                ReadOnlySkillCollection::merge);

        this.skillCollection = this.skillCollection.merge(newSkills);

        /*
           foreach (ISKFunction f in functions)
           {
             f.SetDefaultSkillCollection(this.Skills);
             this._skillCollection.AddNativeFunction(f);
             skill.Add(f.Name, f);
           }

           return skill;

        */
        return functions;
    }

    @Override
    public ReadOnlySkillCollection getSkillCollection() {
        return skillCollection;
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
    public ReadOnlyFunctionCollection getSkill(String funSkill) throws FunctionNotFound {
        ReadOnlyFunctionCollection functions = this.skillCollection.getFunctions(funSkill);
        if (functions == null) {
            throw new FunctionNotFound(funSkill);
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
    public Mono<ReadOnlySKContext<?>> runAsync(SKFunction... pipeline) {
        return runAsync(SKBuilders.variables().build(), pipeline);
    }

    @Override
    public Mono<ReadOnlySKContext<?>> runAsync(String input, SKFunction... pipeline) {
        return runAsync(SKBuilders.variables().build(input), pipeline);
    }

    public Mono<ReadOnlySKContext<?>> runAsync(
            ReadOnlyContextVariables variables, SKFunction... pipeline) {
        DefaultSemanticSKContext context =
                new DefaultSemanticSKContext(variables, this.memory, () -> this.skillCollection);

        Mono<ReadOnlySKContext<?>> pipelineBuilder = Mono.just(context);

        for (SKFunction f : Arrays.asList(pipeline)) {
            pipelineBuilder =
                    pipelineBuilder.flatMap(
                            newContext -> {
                                return f.invokeAsync(newContext, null);
                            });
        }

        return pipelineBuilder;
    }
}
