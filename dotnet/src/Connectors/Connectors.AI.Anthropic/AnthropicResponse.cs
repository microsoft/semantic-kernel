// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.Anthropic;

/// <summary>
/// A successful response from the Anthropic API.
/// </summary>
public class AnthropicResponse
{
    /// <summary>
    /// The resulting completion up to and excluding the stop sequences.
    /// </summary>
    [JsonPropertyName("completion")]
    public string Completion { get; init; } = string.Empty;

    /// <summary>
    /// The reason that we stopped sampling.
    /// </summary>
    /// <remarks>
    /// This may be one of the following values:
    /// <list type="bullet">
    /// <item><c>"stop_sequence"</c>: we reached a stop sequence — either provided by you via the <see cref="AnthropicRequestSettings.StopSequences"/> parameter, or a stop sequence built into the model</item>
    /// <item><c>"max_tokens"</c>: we exceeded <see cref="AnthropicRequestSettings.MaxTokensToSample"/> or the model's maximum</item>
    /// </list>
    /// </remarks>
    [JsonPropertyName("stop_reason")]
    public string StopReason { get; init; } = string.Empty;
}
