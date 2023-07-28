// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.SemanticFunctions;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.AI.TextCompletion;

/// <summary>
/// Settings for a text completion request.
/// </summary>
public class CompleteRequestSettings
{
    /// <summary>
    /// Temperature controls the randomness of the completion.
    /// The higher the temperature, the more random the completion.
    /// </summary>
    [JsonPropertyName("temperature")]
    [JsonPropertyOrder(1)]
    public double Temperature { get; set; } = 0;

    /// <summary>
    /// TopP controls the diversity of the completion.
    /// The higher the TopP, the more diverse the completion.
    /// </summary>
    [JsonPropertyName("top_p")]
    [JsonPropertyOrder(2)]
    public double TopP { get; set; } = 0;

    /// <summary>
    /// Number between -2.0 and 2.0. Positive values penalize new tokens
    /// based on whether they appear in the text so far, increasing the
    /// model's likelihood to talk about new topics.
    /// </summary>
    [JsonPropertyName("presence_penalty")]
    [JsonPropertyOrder(3)]
    public double PresencePenalty { get; set; } = 0;

    /// <summary>
    /// Number between -2.0 and 2.0. Positive values penalize new tokens
    /// based on their existing frequency in the text so far, decreasing
    /// the model's likelihood to repeat the same line verbatim.
    /// </summary>
    [JsonPropertyName("frequency_penalty")]
    [JsonPropertyOrder(4)]
    public double FrequencyPenalty { get; set; } = 0;

    /// <summary>
    /// The maximum number of tokens to generate in the completion.
    /// </summary>
    [JsonPropertyName("max_tokens")]
    [JsonPropertyOrder(5)]
    public int? MaxTokens { get; set; }

    /// <summary>
    /// Sequences where the completion will stop generating further tokens.
    /// </summary>
    [JsonPropertyName("stop_sequences")]
    [JsonPropertyOrder(6)]
    public IList<string> StopSequences { get; set; } = Array.Empty<string>();

    /// <summary>
    /// How many completions to generate for each prompt. Default is 1.
    /// Note: Because this parameter generates many completions, it can quickly consume your token quota.
    /// Use carefully and ensure that you have reasonable settings for max_tokens and stop.
    /// </summary>
    [JsonPropertyName("results_per_prompt")]
    [JsonPropertyOrder(7)]
    public int ResultsPerPrompt { get; set; } = 1;

    /// <summary>
    /// The system prompt to use when generating text completions using a chat model.
    /// Defaults to "Assistant is a large language model."
    /// </summary>
    [JsonPropertyName("chat_system_prompt")]
    [JsonPropertyOrder(8)]
    public string ChatSystemPrompt { get; set; } = "Assistant is a large language model.";

    /// <summary>
    /// Modify the likelihood of specified tokens appearing in the completion.
    /// </summary>
    [JsonPropertyName("token_selection_biases")]
    [JsonPropertyOrder(9)]
    public IDictionary<int, int> TokenSelectionBiases { get; set; } = new Dictionary<int, int>();

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

    /// <summary>
    /// Create a new CompleteRequestSettings instance with the values from a JSON string
    /// or the default values if the string is null or empty.
    /// </summary>
    /// <param name="json">JSON string containing the completion request settings</param>
    /// <returns>An instance of <see cref="CompleteRequestSettings"/> </returns>
    public static CompleteRequestSettings FromJson(string? json)
    {
        if (string.IsNullOrEmpty(json))
        {
            return new CompleteRequestSettings();
        }

        var result = Json.Deserialize<CompleteRequestSettings>(json!);
        return result ?? throw new ArgumentException("Unable to deserialize complete request settings from argument. The deserialization returned null.", nameof(json));
    }
}
