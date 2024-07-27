// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Anthropic;

/// <summary>
/// Billing and rate-limit usage.<br/>
/// Anthropic's API bills and rate-limits by token counts, as tokens represent the underlying cost to our systems.<br/>
/// Under the hood, the API transforms requests into a format suitable for the model.
/// The model's output then goes through a parsing stage before becoming an API response.
/// As a result, the token counts in usage will not match one-to-one with the exact visible content of an API request or response.<br/>
/// For example, OutputTokens will be non-zero, even for an empty string response from Anthropic.
/// </summary>
public sealed class AnthropicUsage
{
    /// <summary>
    /// The number of input tokens which were used.
    /// </summary>
    [JsonRequired]
    [JsonPropertyName("input_tokens")]
    public int? InputTokens { get; init; }

    /// <summary>
    /// The number of output tokens which were used
    /// </summary>
    [JsonRequired]
    [JsonPropertyName("output_tokens")]
    public int? OutputTokens { get; init; }
}
