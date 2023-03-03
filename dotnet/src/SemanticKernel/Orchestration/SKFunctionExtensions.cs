// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Class that holds extension methods for objects implementing ISKFunction.
/// </summary>
public static class SKFunctionExtensions
{
    /// <summary>
    /// Change the LLM Max Tokens configuration
    /// </summary>
    /// <param name="skFunction">Semantic function</param>
    /// <param name="maxTokens">Tokens count</param>
    /// <returns>Self instance</returns>
    public static ISKFunction UseMaxTokens(this ISKFunction skFunction, int maxTokens)
    {
        Verify.NotNull(skFunction.RequestSettings.CompleteRequestSettings, "Completion request settings cannot be empty");
        skFunction.RequestSettings.CompleteRequestSettings.MaxTokens = maxTokens;
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
        Verify.NotNull(skFunction.RequestSettings.CompleteRequestSettings, "Completion request settings cannot be empty");
        skFunction.RequestSettings.CompleteRequestSettings.Temperature = temperature;
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
        Verify.NotNull(skFunction.RequestSettings.CompleteRequestSettings, "Completion request settings cannot be empty");
        skFunction.RequestSettings.CompleteRequestSettings.TopP = topP;
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
        Verify.NotNull(skFunction.RequestSettings.CompleteRequestSettings, "Completion request settings cannot be empty");
        skFunction.RequestSettings.CompleteRequestSettings.PresencePenalty = presencePenalty;
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
        Verify.NotNull(skFunction.RequestSettings.CompleteRequestSettings, "Completion request settings cannot be empty");
        skFunction.RequestSettings.CompleteRequestSettings.FrequencyPenalty = frequencyPenalty;
        return skFunction;
    }

    /// <summary>
    /// Execute a function with a custom set of context variables.
    /// Use case: template engine: semantic function with custom input variable.
    /// </summary>
    /// <param name="function">Function to execute</param>
    /// <param name="input">Custom function input</param>
    /// <param name="memory">Semantic memory</param>
    /// <param name="skills">Available skills</param>
    /// <param name="log">App logger</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>The temporary context</returns>
    public static async Task<SKContext> InvokeWithCustomInputAsync(this ISKFunction function,
        ContextVariables input,
        ISemanticTextMemory memory,
        IReadOnlySkillCollection? skills,
        ILogger log,
        CancellationToken cancellationToken)
    {
        var tmpContext = new SKContext(input, memory, skills, log, cancellationToken);
        try
        {
            await function.InvokeAsync(tmpContext);
        }
        catch (Exception ex) when (!ex.IsCriticalException())
        {
            tmpContext.Fail(ex.Message, ex);
        }

        return tmpContext;
    }
}
