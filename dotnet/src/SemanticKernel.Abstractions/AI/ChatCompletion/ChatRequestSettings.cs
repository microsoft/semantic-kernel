// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.AI.ChatCompletion;

/// <summary>
/// Settings for a chat completion request.
/// For OpenAI see https://platform.openai.com/docs/api-reference/chat
/// </summary>
public class ChatRequestSettings
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
    /// The maximum number of tokens to generate in the completion.
    /// </summary>
    public int? MaxTokens { get; set; }

    /// <summary>
    /// Modify the likelihood of specified tokens appearing in the completion.
    /// </summary>
    public IDictionary<int, int> TokenSelectionBiases { get; set; } = new Dictionary<int, int>();

    /// <summary>
    /// Enabling or disabling function calling is done by setting this parameter.
    /// Possible values are none, auto, or a specific function.
    /// </summary>
    //public bool FunctionCall { get; set; } = false; // This is not needed. Will default to "auto" when functions present and "none" when functions not present.
}
