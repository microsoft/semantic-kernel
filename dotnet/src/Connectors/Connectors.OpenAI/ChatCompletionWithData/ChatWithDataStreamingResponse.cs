// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

[Experimental("SKEXP0010")]
[SuppressMessage("Performance", "CA1812:Avoid uninstantiated internal classes", Justification = "Used for JSON deserialization")]
internal sealed class ChatWithDataStreamingResponse
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("created")]
    public int Created { get; set; } = default;

    [JsonPropertyName("model")]
    public string Model { get; set; } = string.Empty;

    [JsonPropertyName("object")]
    public string Object { get; set; } = string.Empty;

    [JsonPropertyName("choices")]
    public IList<ChatWithDataStreamingChoice> Choices { get; set; } = Array.Empty<ChatWithDataStreamingChoice>();
}

[Experimental("SKEXP0010")]
[SuppressMessage("Performance", "CA1812:Avoid uninstantiated internal classes", Justification = "Used for JSON deserialization")]
internal sealed class ChatWithDataStreamingChoice
{
    [JsonPropertyName("messages")]
    public IList<ChatWithDataStreamingMessage> Messages { get; set; } = Array.Empty<ChatWithDataStreamingMessage>();

    [JsonPropertyName("index")]
    public int Index { get; set; } = 0;
}

[Experimental("SKEXP0010")]
[SuppressMessage("Performance", "CA1812:Avoid uninstantiated internal classes", Justification = "Used for JSON deserialization")]
internal sealed class ChatWithDataStreamingMessage
{
    [JsonPropertyName("delta")]
    public ChatWithDataStreamingDelta Delta { get; set; } = new();

    [JsonPropertyName("end_turn")]
    public bool EndTurn { get; set; }
}

[Experimental("SKEXP0010")]
internal sealed class ChatWithDataStreamingDelta
{
    [JsonPropertyName("role")]
    public string? Role { get; set; }

    [JsonPropertyName("content")]
    public string Content { get; set; } = string.Empty;
}
