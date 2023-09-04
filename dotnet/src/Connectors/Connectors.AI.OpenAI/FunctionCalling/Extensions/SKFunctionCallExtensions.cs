// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.FunctionCalling.Extensions;

using System;
using System.Collections.Generic;
using System.Linq;
using Azure.AI.OpenAI;
using Microsoft.Extensions.Logging;
using SemanticFunctions;
using SemanticKernel.AI.TextCompletion;
using SkillDefinition;


/// <summary>
///  Extensions for creating function calls via the kernel
/// </summary>
public static class SKFunctionCallExtensions
{
    /// <summary>
    ///  Create a function call from a config
    /// </summary>
    /// <param name="kernel"></param>
    /// <param name="promptTemplate"></param>
    /// <param name="functionName"></param>
    /// <param name="skillName"></param>
    /// <param name="description"></param>
    /// <param name="targetFunction"></param>
    /// <param name="callableFunctions"></param>
    /// <param name="callFunctionsAutomatically"></param>
    /// <param name="maxTokens"></param>
    /// <param name="temperature"></param>
    /// <param name="topP"></param>
    /// <param name="presencePenalty"></param>
    /// <param name="frequencyPenalty"></param>
    /// <param name="stopSequences"></param>
    /// <param name="loggerFactory"></param>
    /// <returns></returns>
    public static ISKFunction CreateFunctionCall(
        this IKernel kernel,
        string promptTemplate,
        string? functionName = null,
        string? skillName = null,
        string? description = null,
        FunctionDefinition? targetFunction = null,
        IEnumerable<FunctionDefinition>? callableFunctions = null,
        bool callFunctionsAutomatically = true,
        int? maxTokens = null,
        double temperature = 0,
        double topP = 0,
        double presencePenalty = 0,
        double frequencyPenalty = 0,
        IEnumerable<string>? stopSequences = null,
        ILoggerFactory? loggerFactory = null)
    {
        functionName ??= RandomFunctionName();

        var config = new PromptTemplateConfig
        {
            Description = description ?? "Function call",
            Type = "completion",
            Completion = new PromptTemplateConfig.CompletionConfig
            {
                MaxTokens = maxTokens,
                Temperature = temperature,
                TopP = topP,
                PresencePenalty = presencePenalty,
                FrequencyPenalty = frequencyPenalty,
                StopSequences = stopSequences?.ToList() ?? new List<string>()
            }
        };

        var template = new PromptTemplate(promptTemplate, config, kernel.PromptTemplateEngine);

        SKFunctionCallConfig functionConfig = new(template, config, targetFunction, callableFunctions, callFunctionsAutomatically);
        var functionCall = SKFunctionCall.FromConfig(skillName ?? "sk_function_call", functionName, functionConfig, loggerFactory);
        functionCall.SetAIService(() => kernel.GetService<ITextCompletion>());
        functionCall.SetDefaultSkillCollection(kernel.Skills);
        return functionCall;
    }


    private static string RandomFunctionName() => "functionCall" + Guid.NewGuid().ToString("N");
}
