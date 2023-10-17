// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Orchestration;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the namespace of IKernel
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Class for extensions methods to define semantic functions using OpenAI request settings.
/// </summary>
public static class KernelOpenAISemanticFunctionExtensions
{
    /// <summary>
    /// Define a string-to-string semantic function, with no direct support for input context.
    /// The function can be referenced in templates and will receive the context, but when invoked programmatically you
    /// can only pass in a string in input and receive a string in output.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance</param>
    /// <param name="promptTemplate">Plain language definition of the semantic function, using SK template language</param>
    /// <param name="functionName">A name for the given function. The name can be referenced in templates and used by the pipeline planner.</param>
    /// <param name="pluginName">Optional plugin name, for namespacing and avoid collisions</param>
    /// <param name="description">Optional description, useful for the planner</param>
    /// <param name="maxTokens">Max number of tokens to generate</param>
    /// <param name="temperature">Temperature parameter passed to LLM</param>
    /// <param name="topP">Top P parameter passed to LLM</param>
    /// <param name="presencePenalty">Presence Penalty parameter passed to LLM</param>
    /// <param name="frequencyPenalty">Frequency Penalty parameter passed to LLM</param>
    /// <param name="stopSequences">Strings the LLM will detect to stop generating (before reaching max tokens)</param>
    /// <param name="chatSystemPrompt">When provided will be used to set the system prompt while using Chat Completions</param>
    /// <param name="serviceId">When provided will be used to select the AI service used</param>
    /// <returns>A function ready to use</returns>
    public static ISKFunction CreateSemanticFunctionForOpenAI(
        this IKernel kernel,
        string promptTemplate,
        string? functionName = null,
        string? pluginName = null,
        string? description = null,
        int? maxTokens = null,
        double temperature = 0,
        double topP = 0,
        double presencePenalty = 0,
        double frequencyPenalty = 0,
        IEnumerable<string>? stopSequences = null,
        string? chatSystemPrompt = null,
        string? serviceId = null)
    {
        OpenAIRequestSettings requestSettings = CreateRequestSettings(maxTokens, temperature, topP, presencePenalty, frequencyPenalty, stopSequences, chatSystemPrompt, serviceId);
        return kernel.CreateSemanticFunction(
            promptTemplate,
            functionName,
            pluginName,
            description,
            requestSettings);
    }

    /// <summary>
    /// Invoke a semantic function using the provided prompt template.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance</param>
    /// <param name="promptTemplate">Plain language definition of the semantic function, using SK template language</param>
    /// <param name="functionName">A name for the given function. The name can be referenced in templates and used by the pipeline planner.</param>
    /// <param name="pluginName">Optional plugin name, for namespacing and avoid collisions</param>
    /// <param name="description">Optional description, useful for the planner</param>
    /// <param name="maxTokens">Max number of tokens to generate</param>
    /// <param name="temperature">Temperature parameter passed to LLM</param>
    /// <param name="topP">Top P parameter passed to LLM</param>
    /// <param name="presencePenalty">Presence Penalty parameter passed to LLM</param>
    /// <param name="frequencyPenalty">Frequency Penalty parameter passed to LLM</param>
    /// <param name="stopSequences">Strings the LLM will detect to stop generating (before reaching max tokens)</param>
    /// <param name="chatSystemPrompt">When provided will be used to set the system prompt while using Chat Completions</param>
    /// <param name="serviceId">When provided will be used to select the AI service used</param>
    /// <returns>A function ready to use</returns>
    public static Task<KernelResult> InvokeSemanticFunctionWithOpenAIAsync(
        this IKernel kernel,
        string promptTemplate,
        string? functionName = null,
        string? pluginName = null,
        string? description = null,
        int maxTokens = 256,
        double temperature = 0,
        double topP = 0,
        double presencePenalty = 0,
        double frequencyPenalty = 0,
        IEnumerable<string>? stopSequences = null,
        string? chatSystemPrompt = null,
        string? serviceId = null)
    {
        OpenAIRequestSettings requestSettings = CreateRequestSettings(maxTokens, temperature, topP, presencePenalty, frequencyPenalty, stopSequences, chatSystemPrompt, serviceId);
        return kernel.InvokeSemanticFunctionAsync(
            promptTemplate,
            functionName,
            pluginName,
            description,
            requestSettings);
    }

    #region private
    private static OpenAIRequestSettings CreateRequestSettings(int? maxTokens, double temperature, double topP, double presencePenalty, double frequencyPenalty, IEnumerable<string>? stopSequences, string? chatSystemPrompt, string? serviceId)
    {
        var requestSettings = new OpenAIRequestSettings()
        {
            MaxTokens = maxTokens,
            Temperature = temperature,
            TopP = topP,
            PresencePenalty = presencePenalty,
            FrequencyPenalty = frequencyPenalty,
            ServiceId = serviceId
        };
        if (stopSequences is not null)
        {
            foreach (var stopSequence in stopSequences)
            {
                requestSettings.StopSequences.Add(stopSequence);
            }
        }
        if (!string.IsNullOrEmpty(chatSystemPrompt))
        {
            requestSettings.ChatSystemPrompt = chatSystemPrompt!;
        }

        return requestSettings;
    }
    #endregion
}
