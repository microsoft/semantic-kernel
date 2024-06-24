// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.MistralAI.Client;

/// <summary>
/// Mistral chat completion choice.
/// </summary>
internal sealed class MistralChatCompletionChoice
{
    [JsonPropertyName("finish_reason")]
    public string? FinishReason { get; set; }

    [JsonPropertyName("index")]
    public int? Index { get; set; }

    [JsonPropertyName("delta")]
    public MistralChatMessage? Delta { get; set; }

    [JsonPropertyName("logprobs")]
    public string? LogProbs { get; set; }

    /// <summary>
    /// Returns true if the finish reason is "tool_calls"
    /// </summary>
    internal bool IsToolCall => this.FinishReason?.Equals("tool_calls", StringComparison.Ordinal) ?? false;

    /// <summary>
    /// Returns the number of tool calls
    /// </summary>
    internal int ToolCallCount => this.Delta?.ToolCalls?.Count ?? 0;

    /// <summary>
    /// Return the list of tools calls
    /// </summary>
    internal IList<MistralToolCall>? ToolCalls => this.Delta?.ToolCalls;
}
