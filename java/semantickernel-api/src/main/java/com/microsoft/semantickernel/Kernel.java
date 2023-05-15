// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.builders.BuildersSingleton;
import com.microsoft.semantickernel.exceptions.SkillsNotFoundException;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.orchestration.ContextVariables;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.orchestration.SKFunction;
import com.microsoft.semantickernel.semanticfunctions.SemanticFunctionConfig;
import com.microsoft.semantickernel.skilldefinition.ReadOnlyFunctionCollection;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import com.microsoft.semantickernel.templateengine.PromptTemplateEngine;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;

import reactor.core.publisher.Mono;

import java.util.Map;

import javax.annotation.Nullable;

/** Interface for the semantic kernel. */
public interface Kernel {

    /**
     * Settings required to execute functions, including details about AI dependencies, e.g.
     * endpoints and API keys.
     */
    KernelConfig getConfig();

    /*
    SKFunction<CompleteRequestSettings> registerSemanticFunction(
        String promptTemplate,
        @Nullable String functionName,
        @Nullable String skillName,
        @Nullable String description,
        int maxTokens,
        double temperature,
        double topP,
        double presencePenalty,
        double frequencyPenalty,
        List<String> stopSequences);

        TODO:

            /// <summary>
            /// App logger
            /// </summary>
            ILogger Log { get; }

            /// <summary>
            /// Semantic memory instance
            /// </summary>
            ISemanticTextMemory Memory { get; }
    */

    /**
     * Reference to the engine rendering prompt templates
     *
     * @return
     */
    PromptTemplateEngine getPromptTemplateEngine();

    /*

            /// <summary>
            /// Reference to the read-only skill collection containing all the imported functions
            /// </summary>
            IReadOnlySkillCollection Skills { get; }

            /// <summary>
            /// Build and register a function in the internal skill collection, in a global generic skill.
            /// </summary>
            /// <param name="functionName">Name of the semantic function. The name can contain only alphanumeric chars + underscore.</param>
            /// <param name="functionConfig">Function configuration, e.g. I/O params, AI settings, localization details, etc.</param>
            /// <returns>A C# function wrapping AI logic, usually defined with natural language</returns>
            ISKFunction RegisterSemanticFunction(
                    string functionName,
                    SemanticFunctionConfig functionConfig);

            /// <summary>
            /// Build and register a function in the internal skill collection.
            /// </summary>
            /// <param name="skillName">Name of the skill containing the function. The name can contain only alphanumeric chars + underscore.</param>
            /// <param name="functionName">Name of the semantic function. The name can contain only alphanumeric chars + underscore.</param>
            /// <param name="functionConfig">Function configuration, e.g. I/O params, AI settings, localization details, etc.</param>
            /// <returns>A C# function wrapping AI logic, usually defined with natural language</returns>
            ISKFunction RegisterSemanticFunction(
                    string skillName,
                    string functionName,
                    SemanticFunctionConfig functionConfig);

            /// <summary>
            /// Registers a custom function in the internal skill collection.
            /// </summary>
            /// <param name="skillName">Name of the skill containing the function. The name can contain only alphanumeric chars + underscore.</param>
            /// <param name="customFunction">The custom function to register.</param>
            /// <returns>A C# function wrapping the function execution logic.</returns>
            ISKFunction RegisterCustomFunction(string skillName, ISKFunction customFunction);
    */

    /**
     * Set the semantic memory to use.
     *
     * @param memory {@link SemanticTextMemory} instance
     */
    void registerMemory(SemanticTextMemory memory);

    /*
        /// <summary>
        /// Set the semantic memory to use
        /// </summary>
        /// <param name="memory">Semantic memory instance</param>
        void RegisterMemory(ISemanticTextMemory memory);
    */
    /**
     * Run a pipeline composed of synchronous and asynchronous functions.
     *
     * @param pipeline List of functions
     * @return Result of the function composition
     */
    Mono<SKContext<?>> runAsync(SKFunction... pipeline);

    /**
     * Run a pipeline composed of synchronous and asynchronous functions.
     *
     * @param input Input to process
     * @param pipeline List of functions
     * @return Result of the function composition
     */
    Mono<SKContext<?>> runAsync(String input, SKFunction... pipeline);

    /**
     * Run a pipeline composed of synchronous and asynchronous functions.
     *
     * @param variables variables to initialise the context with
     * @param pipeline List of functions
     * @return Result of the function composition
     */
    Mono<SKContext<?>> runAsync(ContextVariables variables, SKFunction... pipeline);

    /*
    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="variables">Input to process</param>
    /// <param name="pipeline">List of functions</param>
    /// <returns>Result of the function composition</returns>
    Task<SKContext> RunAsync(
            ContextVariables variables,
            params ISKFunction[] pipeline);

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <param name="pipeline">List of functions</param>
    /// <returns>Result of the function composition</returns>
    Task<SKContext> RunAsync(
            CancellationToken cancellationToken,
            params ISKFunction[] pipeline);

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="input">Input to process</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <param name="pipeline">List of functions</param>
    /// <returns>Result of the function composition</returns>
    Task<SKContext> RunAsync(
            string input,
            CancellationToken cancellationToken,
            params ISKFunction[] pipeline);

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="variables">Input to process</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <param name="pipeline">List of functions</param>
    /// <returns>Result of the function composition</returns>
    Task<SKContext> RunAsync(
            ContextVariables variables,
            CancellationToken cancellationToken,
            params ISKFunction[] pipeline);

    /// <summary>
    /// Access registered functions by skill + name. Not case sensitive.
    /// The function might be native or semantic, it's up to the caller handling it.
    /// </summary>
    /// <param name="skillName">Skill name</param>
    /// <param name="functionName">Function name</param>
    /// <returns>Delegate to execute the function</returns>
    ISKFunction Func(string skillName, string functionName);

    /// <summary>
    /// Create a new instance of a context, linked to the kernel internal state.
    /// </summary>
    /// <returns>SK context</returns>
    SKContext CreateNewContext();

    /// <summary>
    /// Get one of the configured services. Currently limited to AI services.
    /// </summary>
    /// <param name="name">Optional name. If the name is not provided, returns the default T available</param>
    /// <typeparam name="T">Service type</typeparam>
    /// <returns>Instance of T</returns>
    T GetService<T>(string name = "");
    */

    /**
     * Import a set of skills
     *
     * @param skillName
     * @param skills
     * @return
     * @throws SkillsNotFoundException
     */
    ReadOnlyFunctionCollection importSkills(
            String skillName, Map<String, SemanticFunctionConfig> skills)
            throws SkillsNotFoundException;

    /**
     * Get function collection with the skill name
     *
     * @param funSkill
     * @return
     * @throws SkillsNotFoundException
     */
    ReadOnlyFunctionCollection getSkill(String funSkill) throws SkillsNotFoundException;

    /**
     * Imports the native functions annotated on the given object as a skill.
     *
     * @param nativeSkill
     * @param skillName
     * @return
     */
    ReadOnlyFunctionCollection importSkill(Object nativeSkill, @Nullable String skillName);

    /**
     * Returns all skills
     *
     * @return
     */
    ReadOnlySkillCollection getSkillCollection();

    CompletionSKFunction.Builder createSemanticFunction();

    /** Obtains the service with the given name and type */
    <T> T getService(@Nullable String name, Class<T> clazz) throws KernelException;

    /** Registers a semantic functon on this kernel */
    <
                    RequestConfiguration,
                    ContextType extends SKContext<ContextType>,
                    FunctionType extends SKFunction<RequestConfiguration, ContextType>>
            FunctionType registerSemanticFunction(FunctionType semanticFunctionDefinition);

    // <T extends ReadOnlySKContext<T>> T createNewContext();

    class Builder {
        @Nullable private KernelConfig kernelConfig = null;
        @Nullable private PromptTemplateEngine promptTemplateEngine = null;

        @Nullable private ReadOnlySkillCollection skillCollection = null;

        public Builder setKernelConfig(KernelConfig kernelConfig) {
            this.kernelConfig = kernelConfig;
            return this;
        }

        public Builder setPromptTemplateEngine(PromptTemplateEngine promptTemplateEngine) {
            this.promptTemplateEngine = promptTemplateEngine;
            return this;
        }

        public Builder setSkillCollection(@Nullable ReadOnlySkillCollection skillCollection) {
            this.skillCollection = skillCollection;
            return this;
        }

        public Kernel build() {
            if (kernelConfig == null) {
                throw new IllegalStateException("Must provide a kernel configuration");
            }

            return BuildersSingleton.INST
                    .getKernelBuilder()
                    .build(kernelConfig, promptTemplateEngine, skillCollection);
        }
    }

    interface InternalBuilder {
        Kernel build(
                KernelConfig kernelConfig,
                @Nullable PromptTemplateEngine promptTemplateEngine,
                @Nullable ReadOnlySkillCollection skillCollection);
    }
}
