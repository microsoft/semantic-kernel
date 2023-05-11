// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.Models;

internal sealed class CompletionRequestSettings
{
    /// <summary>
    /// Temperature controls the randomness of the completion.
    /// The higher the temperature, the more random the completion.
    /// </summary>
    [JsonPropertyName("temperature")]
    public double Temperature { get; set; } = 0;

    /// <summary>
    /// TopP controls the diversity of the completion.
    /// The higher the TopP, the more diverse the completion.
    /// </summary>
    [JsonPropertyName("top_p")]
    public double TopP { get; set; } = 0;

    /// <summary>
    /// Number between -2.0 and 2.0. Positive values penalize new tokens
    /// based on whether they appear in the text so far, increasing the
    /// model's likelihood to talk about new topics.
    /// </summary>
    [JsonPropertyName("presence_penalty")]
    public double PresencePenalty { get; set; } = 0;

    /// <summary>
    /// Number between -2.0 and 2.0. Positive values penalize new tokens
    /// based on their existing frequency in the text so far, decreasing
    /// the model's likelihood to repeat the same line verbatim.
    /// </summary>
    [JsonPropertyName("frequency_penalty")]
    public double FrequencyPenalty { get; set; } = 0;

    /// <summary>
    /// The maximum number of tokens to generate in the completion.
    /// </summary>
    [JsonPropertyName("max_tokens")]
    public int MaxTokens { get; set; } = 256;

    /// <summary>
    /// Sequences where the completion will stop generating further tokens.
    /// </summary>
    [JsonPropertyName("stop_sequences")]
    public IList<string> StopSequences { get; set; } = Array.Empty<string>();

    /// <summary>
    /// Create a new settings object with the values from <see cref="JsonObject"/> settings.
    /// </summary>
    /// <param name="settings">Instance of <see cref="JsonObject"/> settings.</param>
    /// <returns>An instance of <see cref="CompletionRequestSettings"/>.</returns>
    public static CompletionRequestSettings FromJson(JsonObject settings)
    {
        return settings.Deserialize<CompletionRequestSettings>() ?? new CompletionRequestSettings();
    }
}
