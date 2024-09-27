// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.SemanticFunctions;
using Microsoft.SemanticKernel.Services;
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
        string skillName = "",
        string? description = null,
        int maxTokens = 256,
        double temperature = 0,
        double topP = 0,
        double presencePenalty = 0,
        double frequencyPenalty = 0,
        IEnumerable<string>? stopSequences = null)
    {
        functionName ??= RandomFunctionName();

        JsonArray stopSequencesArray = new();

        if (stopSequences != null)
        {
            foreach (var stopSequence in stopSequences)
            {
                stopSequencesArray.Add(JsonValue.Create<string>(stopSequence));
            }
        }

        var serviceSettings = new JsonObject
        {
            ["temperature"] = temperature,
            ["top_p"] = topP,
            ["presence_penalty"] = presencePenalty,
            ["frequency_penalty"] = frequencyPenalty,
            ["max_tokens"] = maxTokens,
            ["stop_sequences"] = stopSequencesArray,
        };

        var config = new PromptTemplateConfig
        {
            Description = description ?? "Generic function, unknown purpose",
            DefaultSettings = serviceSettings
        };

        return kernel.CreateSemanticFunction(
            promptTemplate: promptTemplate,
            config: config,
            functionName: functionName,
            skillName: skillName);
    }

    /// <summary>
    /// Allow to define a semantic function passing in the definition in natural language, i.e. the prompt template.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance</param>
    /// <param name="functionName">A name for the given function. The name can be referenced in templates and used by the pipeline planner.</param>
    /// <param name="promptTemplate">Plain language definition of the semantic function, using SK template language</param>
    /// <param name="skillName">An optional skill name, e.g. to namespace functions with the same name. When empty,
    /// the function is added to the global namespace, overwriting functions with the same name</param>
    /// <param name="config">Optional function settings</param>
    /// <returns>A function ready to use</returns>
    public static ISKFunction CreateSemanticFunction(
        this IKernel kernel,
        string promptTemplate,
        PromptTemplateConfig config,
        string? functionName = null,
        string skillName = "")
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
            : kernel.RegisterSemanticFunction(skillName, functionName, functionConfig);
    }

    private static string RandomFunctionName() => "func" + Guid.NewGuid().ToString("N");
}
