// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion.ChatCompletion;

/// <summary>
/// HTTP Schema for an single Oobabooga result as part of a completion response.
/// </summary>
public sealed class ChatCompletionResponseHistory
{
    /// <summary>
    /// Completed text.
    /// </summary>
    [JsonPropertyName("history")]
    public OobaboogaChatHistory History { get; set; } = new();
}
