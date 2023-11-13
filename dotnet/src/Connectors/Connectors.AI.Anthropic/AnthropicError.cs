// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.Anthropic;

/// <summary>
/// Details of the error response from the Anthropic API.
/// </summary>
public class AnthropicErrorDetails
{
    /// <summary>
    /// The error type.
    /// </summary>
    [JsonPropertyName("type")]
    public string Type { get; init; } = string.Empty;

    /// <summary>
    /// The error message.
    /// </summary>
    [JsonPropertyName("message")]
    public string Message { get; init; } = string.Empty;
}

/// <summary>
/// Represents an error response from the Anthropic API.
/// </summary>
public class AnthropicError
{
    /// <summary>
    /// The error details.
    /// </summary>
    [JsonPropertyName("error")]
    public AnthropicErrorDetails Error { get; init; } = new AnthropicErrorDetails();
}
