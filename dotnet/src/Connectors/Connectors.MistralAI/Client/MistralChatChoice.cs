// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.MistralAI.Client;

/// <summary>
/// Choice for chat completion.
/// </summary>
internal class MistralChatChoice
{
    [JsonPropertyName("index")]
    public int? Index { get; set; }

    [JsonPropertyName("message")]
    public MistralChatMessage? Message { get; set; }

    /// <summary>
    /// The reason the chat completion was finished.
    /// Enum: "stop" "length" "model_length" "error" "tool_calls"
    /// </summary>
    [JsonPropertyName("finish_reason")]
    public string? FinishReason { get; set; }
}
