// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion.TextCompletion;

/// <summary>
/// HTTP Schema for an single Oobabooga result as part of a completion response.
/// </summary>
public sealed class TextCompletionResponseText
{
    /// <summary>
    /// Completed text.
    /// </summary>
    [JsonPropertyName("text")]
    public string? Text { get; set; } = string.Empty;
}
