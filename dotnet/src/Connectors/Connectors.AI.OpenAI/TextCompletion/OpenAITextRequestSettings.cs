// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextCompletion;

/// <summary>
/// Request settings for an OpenAI text completion request.
/// </summary>
public class OpenAITextRequestSettings
{
    /// <summary>
    /// Temperature controls the randomness of the completion.
    /// The higher the temperature, the more random the completion.
    /// </summary>
    public double Temperature { get; set; } = 0;

    /// <summary>
    /// TopP controls the diversity of the completion.
    /// The higher the TopP, the more diverse the completion.
    /// </summary>
    public double TopP { get; set; } = 0;

    /// <summary>
    /// Number between -2.0 and 2.0. Positive values penalize new tokens
    /// based on whether they appear in the text so far, increasing the
    /// model's likelihood to talk about new topics.
    /// </summary>
    public double PresencePenalty { get; set; } = 0;

    /// <summary>
    /// Number between -2.0 and 2.0. Positive values penalize new tokens
    /// based on their existing frequency in the text so far, decreasing
    /// the model's likelihood to repeat the same line verbatim.
    /// </summary>
    public double FrequencyPenalty { get; set; } = 0;

    /// <summary>
    /// The maximum number of tokens to generate in the completion.
    /// </summary>
    public int? MaxTokens { get; set; }

    /// <summary>
    /// Sequences where the completion will stop generating further tokens.
    /// </summary>
    public IList<string> StopSequences { get; set; } = Array.Empty<string>();

    /// <summary>
    /// How many completions to generate for each prompt. Default is 1.
    /// Note: Because this parameter generates many completions, it can quickly consume your token quota.
    /// Use carefully and ensure that you have reasonable settings for max_tokens and stop.
    /// </summary>
    public int ResultsPerPrompt { get; set; } = 1;

    /// <summary>
    /// The system prompt to use when generating text completions using a chat model.
    /// Defaults to "Assistant is a large language model."
    /// </summary>
    public string ChatSystemPrompt { get; set; } = "Assistant is a large language model.";

    /// <summary>
    /// Modify the likelihood of specified tokens appearing in the completion.
    /// </summary>
    public IDictionary<int, int> TokenSelectionBiases { get; set; } = new Dictionary<int, int>();

    /// <summary>
    /// Create a new settings object with the values from another settings object.
    /// </summary>
    /// <param name="config">Template configuration</param>
    /// <returns>An instance of <see cref="CompleteRequestSettings"/></returns>
    public static OpenAITextRequestSettings FromCompletionConfig(dynamic completionConfig)
    {
        var settings = new OpenAITextRequestSettings
        {
            Temperature = completionConfig.Temperature,
            TopP = completionConfig.TopP,
            PresencePenalty = completionConfig.PresencePenalty,
            FrequencyPenalty = completionConfig.FrequencyPenalty,
            MaxTokens = completionConfig.MaxTokens,
            StopSequences = completionConfig.StopSequences,
        };

        if (!string.IsNullOrWhiteSpace(completionConfig.ChatSystemPrompt))
        {
            settings.ChatSystemPrompt = completionConfig.ChatSystemPrompt!;
        }

        return settings;
    }
}
