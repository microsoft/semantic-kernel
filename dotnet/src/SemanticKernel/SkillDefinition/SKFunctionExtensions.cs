// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Class that holds extension methods for objects implementing ISKFunction.
/// </summary>
public static class SKFunctionExtensions
{
    /// <summary>
    /// Configure the LLM settings used by semantic function.
    /// </summary>
    /// <param name="skFunction">Semantic function</param>
    /// <param name="settings">Completion settings</param>
    /// <returns>Self instance</returns>
    public static ISKFunction UseCompletionSettings(this ISKFunction skFunction, CompleteRequestSettings settings)
    {
        return skFunction.SetAIConfiguration(settings);
    }

    /// <summary>
    /// Change the LLM Max Tokens configuration
    /// </summary>
    /// <param name="skFunction">Semantic function</param>
    /// <param name="maxTokens">Tokens count</param>
    /// <returns>Self instance</returns>
    public static ISKFunction UseMaxTokens(this ISKFunction skFunction, int? maxTokens)
    {
        skFunction.RequestSettings.MaxTokens = maxTokens;
        return skFunction;
    }

    /// <summary>
    /// Change the LLM Temperature configuration
    /// </summary>
    /// <param name="skFunction">Semantic function</param>
    /// <param name="temperature">Temperature value</param>
    /// <returns>Self instance</returns>
    public static ISKFunction UseTemperature(this ISKFunction skFunction, double temperature)
    {
        skFunction.RequestSettings.Temperature = temperature;
        return skFunction;
    }

    /// <summary>
    /// Change the Max Tokens configuration
    /// </summary>
    /// <param name="skFunction">Semantic function</param>
    /// <param name="topP">TopP value</param>
    /// <returns>Self instance</returns>
    public static ISKFunction UseTopP(this ISKFunction skFunction, double topP)
    {
        skFunction.RequestSettings.TopP = topP;
        return skFunction;
    }

    /// <summary>
    /// Change the Max Tokens configuration
    /// </summary>
    /// <param name="skFunction">Semantic function</param>
    /// <param name="presencePenalty">Presence penalty value</param>
    /// <returns>Self instance</returns>
    public static ISKFunction UsePresencePenalty(this ISKFunction skFunction, double presencePenalty)
    {
        skFunction.RequestSettings.PresencePenalty = presencePenalty;
        return skFunction;
    }

    /// <summary>
    /// Change the Max Tokens configuration
    /// </summary>
    /// <param name="skFunction">Semantic function</param>
    /// <param name="frequencyPenalty">Frequency penalty value</param>
    /// <returns>Self instance</returns>
    public static ISKFunction UseFrequencyPenalty(this ISKFunction skFunction, double frequencyPenalty)
    {
        skFunction.RequestSettings.FrequencyPenalty = frequencyPenalty;
        return skFunction;
    }

    /// <summary>
    /// Execute a function allowing to pass the main input separately from the rest of the context
    /// and the cancellation token without the need to name the parameter, to have a shorter more readable syntax.
    /// Note: if the context contains an INPUT key/value, that value is ignored, logging a warning.
    /// </summary>
    /// <param name="function">Function to execute</param>
    /// <param name="input">Main input string</param>
    /// /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The result of the function execution</returns>
    public static Task<SKContext> InvokeAsync(this ISKFunction function,
        string? input = null, CancellationToken cancellationToken = default)
    {
        return function.InvokeAsync(input, settings: null, memory: null, logger: null, cancellationToken: cancellationToken);
    }

    /// <summary>
    /// Execute a function allowing to pass the main input separately from the rest of the context.
    /// Note: if the context contains an INPUT key/value, that value is ignored, logging a warning.
    /// </summary>
    /// <param name="function">Function to execute</param>
    /// <param name="input">Main input string</param>
    /// <param name="context">Execution context, including variables other than input</param>
    /// <param name="mutableContext">Whether the function can modify the context variables, True by default</param>
    /// <param name="settings">LLM completion settings (for semantic functions only)</param>
    /// <returns>The result of the function execution</returns>
    public static Task<SKContext> InvokeAsync(this ISKFunction function,
        string input,
        SKContext context,
        bool mutableContext = true,
        CompleteRequestSettings? settings = null)
    {
        // Log a warning if the given input is overriding a different input in the context
        var inputInContext = context.Variables.Input;
        if (!string.IsNullOrEmpty(inputInContext) && !string.Equals(input, inputInContext, StringComparison.Ordinal))
        {
            context.Log.LogWarning(
                "Function {0}.{1} has been invoked with an explicit input text that is different and overrides the input text defined in the context",
                function.SkillName, function.Name);
        }

        if (!mutableContext)
        {
            // Create a copy of the context, to avoid editing the original set of variables
            context = context.Clone();
        }

        // Store the input in the context
        context.Variables.Update(input);
        return function.InvokeAsync(context, settings);
    }
}
