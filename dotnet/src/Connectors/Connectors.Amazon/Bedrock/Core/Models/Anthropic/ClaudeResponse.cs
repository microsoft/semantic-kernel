// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Anthropic Claude completion response.
/// </summary>
internal class ClaudeResponse
{
    /// <summary>
    /// The resulting completion up to and excluding the stop sequences.
    /// </summary>
    [JsonPropertyName("completion")]
    public string? Completion { get; set; }

    /// <summary>
    /// The reason why the model stopped generating the response.
    /// "stop_sequence" – The model reached a stop sequence — either provided by you with the stop_sequences inference parameter, or a stop sequence built into the model.
    /// "max_tokens" – The model exceeded max_tokens_to_sample or the model's maximum number of tokens.
    /// </summary>
    [JsonPropertyName("stop_reason")]
    public string? StopReason { get; set; }

    /// <summary>
    /// If you specify the stop_sequences inference parameter, stop contains the stop sequence that signalled the model to stop generating text. For example, holes in the following response.
    /// </summary>
    [JsonPropertyName("stop")]
    public string? Stop { get; set; }
}
