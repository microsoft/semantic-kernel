// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Globalization;
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
    /// Execute a function allowing to pass the main input separately from the rest of the context.
    /// </summary>
    /// <param name="function">Function to execute</param>
    /// <param name="input">Main input string</param>
    /// <param name="variables">Variables other than input</param>
    /// <param name="skills">Skills that the function can access</param>
    /// <param name="culture">Culture to use for the function execution</param>
    /// <param name="settings">LLM completion settings (for semantic functions only)</param>
    /// <param name="logger">Logger to use for the function execution</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The result of the function execution</returns>
    public static Task<SKContext> InvokeAsync(this ISKFunction function,
        string? input = null,
        IReadOnlyDictionary<string, string>? variables = null,
        IReadOnlySkillCollection? skills = null,
        CultureInfo? culture = null,
        CompleteRequestSettings? settings = null,
        ILogger? logger = null,
        CancellationToken cancellationToken = default)
    {
        ContextVariables contextVariables = new(input);
        if (variables != null)
        {
            foreach (var variable in variables)
            {
                contextVariables.Set(variable.Key, variable.Value);
            }
        }

        var context = new SKContext(contextVariables, skills, logger)
        {
            Culture = culture!
        };

        return function.InvokeAsync(context, settings, cancellationToken);
    }

    /// <summary>
    /// Returns decorated instance of <see cref="ISKFunction"/> with enabled instrumentation.
    /// </summary>
    /// <param name="function">Instance of <see cref="ISKFunction"/> to decorate.</param>
    /// <param name="logger">Optional logger.</param>
    public static ISKFunction WithInstrumentation(this ISKFunction function, ILogger? logger = null)
    {
        return new InstrumentedSKFunction(function, logger);
    }
}
