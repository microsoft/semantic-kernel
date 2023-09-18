// Copyright (c) Microsoft. All rights reserved.

using System.Globalization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

#pragma warning disable IDE0130 // Namespace does not match folder structure
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130 // Namespace does not match folder structure

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
    /// <param name="variables">Input variables for the function</param>
    /// <param name="skills">Skills that the function can access</param>
    /// <param name="culture">Culture to use for the function execution</param>
    /// <param name="settings">LLM completion settings (for semantic functions only)</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The result of the function execution</returns>
    public static Task<FunctionResult> InvokeAsync(this ISKFunction function,
        ContextVariables? variables = null,
        IReadOnlySkillCollection? skills = null,
        CultureInfo? culture = null,
        CompleteRequestSettings? settings = null,
        ILoggerFactory? loggerFactory = null,
        CancellationToken cancellationToken = default)
    {
        var context = new SKContext(variables, skills, loggerFactory)
        {
            Culture = culture!
        };

        return function.InvokeAsync(context, settings, cancellationToken);
    }

    /// <summary>
    /// Execute a function allowing to pass the main input separately from the rest of the context.
    /// </summary>
    /// <param name="function">Function to execute</param>
    /// <param name="input">Input string for the function</param>
    /// <param name="skills">Skills that the function can access</param>
    /// <param name="culture">Culture to use for the function execution</param>
    /// <param name="settings">LLM completion settings (for semantic functions only)</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The result of the function execution</returns>
    public static Task<FunctionResult> InvokeAsync(this ISKFunction function,
        string input,
        IReadOnlySkillCollection? skills = null,
        CultureInfo? culture = null,
        CompleteRequestSettings? settings = null,
        ILoggerFactory? loggerFactory = null,
        CancellationToken cancellationToken = default)
        => function.InvokeAsync(new ContextVariables(input), skills, culture, settings, loggerFactory, cancellationToken);

    /// <summary>
    /// Returns decorated instance of <see cref="ISKFunction"/> with enabled instrumentation.
    /// </summary>
    /// <param name="function">Instance of <see cref="ISKFunction"/> to decorate.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public static ISKFunction WithInstrumentation(this ISKFunction function, ILoggerFactory? loggerFactory = null)
    {
        return new InstrumentedSKFunction(function, loggerFactory);
    }
}
