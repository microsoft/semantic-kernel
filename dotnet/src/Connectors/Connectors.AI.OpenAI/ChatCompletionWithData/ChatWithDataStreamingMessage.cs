// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

[Serializable]
[SuppressMessage("Performance", "CA1812:Avoid uninstantiated internal classes", Justification = "Used for JSON deserialization")]
internal sealed class ChatWithDataStreamingMessage
{
    [JsonPropertyName("delta")]
    public ChatWithDataStreamingDelta Delta { get; set; } = new();

    [JsonPropertyName("end_turn")]
    public bool EndTurn { get; set; }
}
