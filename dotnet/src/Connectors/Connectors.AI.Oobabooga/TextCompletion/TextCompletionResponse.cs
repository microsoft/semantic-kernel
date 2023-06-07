// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.TextCompletion;

/// <summary>
/// HTTP Schema for completion response.
/// </summary>
public sealed class TextCompletionResponse
{
    [JsonPropertyName("results")]
    public List<TextCompletionResponseText> Results { get; set; } = new();
}

public sealed class TextCompletionResponseText
{
    /// <summary>
    /// Completed text.
    /// </summary>
    [JsonPropertyName("text")]
    public string? Text { get; set; } = string.Empty;
}

/// <summary>
/// HTTP Schema for streaming completion response.
/// </summary>
public sealed class TextCompletionStreamingResponse
{
    [JsonPropertyName("event")]
    public string Event { get; set; } = string.Empty;

    [JsonPropertyName("message_num")]
    public int MessageNum { get; set; }

    [JsonPropertyName("text")]
    public string Text { get; set; } = string.Empty;
}
