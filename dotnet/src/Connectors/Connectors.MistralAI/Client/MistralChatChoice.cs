// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.MistralAI.Client;

/// <summary>
/// Choice for chat completion.
/// </summary>
internal sealed class MistralChatChoice
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

    /// <summary>
    /// Returns true if the finish reason is "tool_calls"
    /// </summary>
    internal bool IsToolCall => this.FinishReason?.Equals("tool_calls", StringComparison.Ordinal) ?? false;

    /// <summary>
    /// Returns the number of tool calls
    /// </summary>
    internal int ToolCallCount => this.Message?.ToolCalls?.Count ?? 0;

    /// <summary>
    /// Return the list of tools calls
    /// </summary>
    internal IList<MistralToolCall>? ToolCalls => this.Message?.ToolCalls;
}
