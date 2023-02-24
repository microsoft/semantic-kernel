// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.SemanticFunctions;

namespace Microsoft.SemanticKernel.AI;

/// <summary>
/// Settings for a completion request.
/// </summary>
public class CompleteRequestSettings
{
    /// <summary>
    /// Temperature controls the randomness of the completion. The higher the temperature, the more random the completion.
    /// </summary>
    public double Temperature { get; set; } = 0;

    /// <summary>
    /// TopP controls the diversity of the completion. The higher the TopP, the more diverse the completion.
    /// </summary>
    public double TopP { get; set; } = 0;

    /// <summary>
    /// Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so far, increasing the model's likelihood to talk about new topics.
    /// </summary>
    public double PresencePenalty { get; set; } = 0;

    /// <summary>
    /// Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.
    /// </summary>
    public double FrequencyPenalty { get; set; } = 0;

    /// <summary>
    /// The maximum number of tokens to generate in the completion.
    /// </summary>
    public int MaxTokens { get; set; } = 100;

    /// <summary>
    /// Sequences where the completion will stop generating further tokens.
    /// </summary>
    public IList<string> StopSequences { get; set; } = Array.Empty<string>();

    /// <summary>
    /// Update this settings object with the values from another settings object.
    /// </summary>
    /// <param name="config">The config whose values to use</param>
    /// <returns>Returns this CompleteRequestSettings object</returns>
    public CompleteRequestSettings UpdateFromCompletionConfig(PromptTemplateConfig.CompletionConfig config)
    {
        this.Temperature = config.Temperature;
        this.TopP = config.TopP;
        this.PresencePenalty = config.PresencePenalty;
        this.FrequencyPenalty = config.FrequencyPenalty;
        this.MaxTokens = config.MaxTokens;
        this.StopSequences = config.StopSequences;
        return this;
    }

    /// <summary>
    /// Create a new settings object with the values from another settings object.
    /// </summary>
    /// <param name="config"></param>
    /// <returns>An instance of <see cref="CompleteRequestSettings"/> </returns>
    public static CompleteRequestSettings FromCompletionConfig(PromptTemplateConfig.CompletionConfig config)
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
}
