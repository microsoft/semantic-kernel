// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SemanticFunctions;
using Microsoft.SemanticKernel.SkillDefinition;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the namespace of IKernel
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Class for extensions methods to define semantic functions.
/// </summary>
public static class InlineFunctionsDefinitionExtension
{
    /// <summary>
    /// Build and register a function in the internal skill collection, in a global generic skill.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance</param>
    /// <param name="functionName">Name of the semantic function. The name can contain only alphanumeric chars + underscore.</param>
    /// <param name="functionConfig">Function configuration, e.g. I/O params, AI settings, localization details, etc.</param>
    /// <returns>A C# function wrapping AI logic, usually defined with natural language</returns>
    public static ISKFunction RegisterSemanticFunction(this IKernel kernel, string functionName, SemanticFunctionConfig functionConfig)
    {
        return kernel.RegisterSemanticFunction(SkillCollection.GlobalSkill, functionName, functionConfig);
    }

    /// <summary>
    /// Build and register a function in the internal skill collection.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance</param>
    /// <param name="skillName">Name of the skill containing the function. The name can contain only alphanumeric chars + underscore.</param>
    /// <param name="functionName">Name of the semantic function. The name can contain only alphanumeric chars + underscore.</param>
    /// <param name="functionConfig">Function configuration, e.g. I/O params, AI settings, localization details, etc.</param>
    /// <returns>A C# function wrapping AI logic, usually defined with natural language</returns>
    public static ISKFunction RegisterSemanticFunction(this IKernel kernel, string skillName, string functionName, SemanticFunctionConfig functionConfig)
    {
        // Future-proofing the name not to contain special chars
        Verify.ValidSkillName(skillName);
        Verify.ValidFunctionName(functionName);

        ISKFunction function = kernel.CreateSemanticFunction(skillName, functionName, functionConfig);
        return kernel.RegisterCustomFunction(function);
    }

    /// <summary>
    /// Define a string-to-string semantic function, with no direct support for input context.
    /// The function can be referenced in templates and will receive the context, but when invoked programmatically you
    /// can only pass in a string in input and receive a string in output.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance</param>
    /// <param name="promptTemplate">Plain language definition of the semantic function, using SK template language</param>
    /// <param name="functionName">A name for the given function. The name can be referenced in templates and used by the pipeline planner.</param>
    /// <param name="skillName">Optional skill name, for namespacing and avoid collisions</param>
    /// <param name="description">Optional description, useful for the planner</param>
    /// <param name="maxTokens">Max number of tokens to generate</param>
    /// <param name="temperature">Temperature parameter passed to LLM</param>
    /// <param name="topP">Top P parameter passed to LLM</param>
    /// <param name="presencePenalty">Presence Penalty parameter passed to LLM</param>
    /// <param name="frequencyPenalty">Frequency Penalty parameter passed to LLM</param>
    /// <param name="stopSequences">Strings the LLM will detect to stop generating (before reaching max tokens)</param>
    /// <returns>A function ready to use</returns>
    public static ISKFunction CreateSemanticFunction(
        this IKernel kernel,
        string promptTemplate,
        string? functionName = null,
        string? skillName = null,
        string? description = null,
        int? maxTokens = null,
        double temperature = 0,
        double topP = 0,
        double presencePenalty = 0,
        double frequencyPenalty = 0,
        IEnumerable<string>? stopSequences = null)
    {
        functionName ??= RandomFunctionName();

        var config = new PromptTemplateConfig
        {
            Description = description ?? "Generic function, unknown purpose",
            Type = "completion",
            Completion = new PromptTemplateConfig.CompletionConfig
            {
                Temperature = temperature,
                TopP = topP,
                PresencePenalty = presencePenalty,
                FrequencyPenalty = frequencyPenalty,
                MaxTokens = maxTokens,
                StopSequences = stopSequences?.ToList() ?? new List<string>()
            }
        };

        return kernel.CreateSemanticFunction(
            promptTemplate: promptTemplate,
            config: config,
            functionName: functionName,
            skillName: skillName);
    }

    /// <summary>
    /// Define a semantic function passing in the definition in natural language, i.e. the prompt template.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance</param>
    /// <param name="promptTemplate">Plain language definition of the semantic function, using SK template language</param>
    /// <param name="config">Optional function settings</param>
    /// <param name="functionName">A name for the given function. The name can be referenced in templates and used by the pipeline planner.</param>
    /// <param name="skillName">An optional skill name, e.g. to namespace functions with the same name. When empty,
    /// the function is added to the global namespace, overwriting functions with the same name</param>
    /// <returns>A function ready to use</returns>
    public static ISKFunction CreateSemanticFunction(
        this IKernel kernel,
        string promptTemplate,
        PromptTemplateConfig config,
        string? functionName = null,
        string? skillName = null)
    {
        functionName ??= RandomFunctionName();
        Verify.ValidFunctionName(functionName);
        if (!string.IsNullOrEmpty(skillName)) { Verify.ValidSkillName(skillName); }

        var template = new PromptTemplate(promptTemplate, config, kernel.PromptTemplateEngine);

        // Prepare lambda wrapping AI logic
        var functionConfig = new SemanticFunctionConfig(config, template);

        // TODO: manage overwrites, potentially error out
        return string.IsNullOrEmpty(skillName)
            ? kernel.RegisterSemanticFunction(functionName, functionConfig)
            : kernel.RegisterSemanticFunction(skillName!, functionName, functionConfig);
    }

    /// <summary>
    /// Invoke a semantic function using the provided prompt template.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance</param>
    /// <param name="promptTemplate">Plain language definition of the semantic function, using SK template language</param>
    /// <param name="functionName">A name for the given function. The name can be referenced in templates and used by the pipeline planner.</param>
    /// <param name="skillName">Optional skill name, for namespacing and avoid collisions</param>
    /// <param name="description">Optional description, useful for the planner</param>
    /// <param name="maxTokens">Max number of tokens to generate</param>
    /// <param name="temperature">Temperature parameter passed to LLM</param>
    /// <param name="topP">Top P parameter passed to LLM</param>
    /// <param name="presencePenalty">Presence Penalty parameter passed to LLM</param>
    /// <param name="frequencyPenalty">Frequency Penalty parameter passed to LLM</param>
    /// <param name="stopSequences">Strings the LLM will detect to stop generating (before reaching max tokens)</param>
    /// <returns>A function ready to use</returns>
    public static Task<SKContext> InvokeSemanticFunctionAsync(
        this IKernel kernel,
        string promptTemplate,
        string? functionName = null,
        string? skillName = null,
        string? description = null,
        int maxTokens = 256,
        double temperature = 0,
        double topP = 0,
        double presencePenalty = 0,
        double frequencyPenalty = 0,
        IEnumerable<string>? stopSequences = null)
    {
        var skfunction = kernel.CreateSemanticFunction(
            promptTemplate,
            functionName,
            skillName,
            description,
            maxTokens,
            temperature,
            topP,
            presencePenalty,
            frequencyPenalty,
            stopSequences);

        return kernel.RunAsync(skfunction);
    }

    /// <summary>
    /// Define a semantic function.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance</param>
    /// <param name="skillName"></param>
    /// <param name="functionName"></param>
    /// <param name="functionConfig"></param>
    /// <returns></returns>
    /// <exception cref="SKException"></exception>
    private static ISKFunction CreateSemanticFunction(
        this IKernel kernel,
        string skillName,
        string functionName,
        SemanticFunctionConfig functionConfig)
    {
        if (!functionConfig.PromptTemplateConfig.Type.Equals("completion", StringComparison.OrdinalIgnoreCase))
        {
            throw new SKException($"Function type not supported: {functionConfig.PromptTemplateConfig}");
        }

        ISKFunction func = SemanticFunction.FromSemanticConfig(
            skillName,
            functionName,
            functionConfig,
            kernel.LoggerFactory
        );

        // Connect the function to the current kernel skill collection, in case the function
        // is invoked manually without a context and without a way to find other functions.
        func.SetDefaultSkillCollection(kernel.Skills);

        func.SetAIConfiguration(FromCompletionConfig(functionConfig.PromptTemplateConfig.Completion));

        // Note: the service is instantiated using the kernel configuration state when the function is invoked
        func.SetAIService(() => kernel.GetService<ITextCompletion>());

        return func;
    }

    /// <summary>
    /// Create a new settings object with the values from another settings object.
    /// </summary>
    /// <param name="config"></param>
    /// <returns>An instance of <see cref="CompleteRequestSettings"/> </returns>
    private static CompleteRequestSettings FromCompletionConfig(PromptTemplateConfig.CompletionConfig config)
    {
        return new CompleteRequestSettings
        {
            Temperature = config.Temperature,
            TopP = config.TopP,
            PresencePenalty = config.PresencePenalty,
            FrequencyPenalty = config.FrequencyPenalty,
            MaxTokens = config.MaxTokens,
            StopSequences = config.StopSequences,
        };
    }

    private static string RandomFunctionName() => "func" + Guid.NewGuid().ToString("N");
}
