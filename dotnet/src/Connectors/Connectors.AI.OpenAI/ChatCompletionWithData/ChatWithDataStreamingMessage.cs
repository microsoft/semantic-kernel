// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

internal class ChatWithDataStreamingMessage
{
    [JsonPropertyName("delta")]
    public ChatWithDataStreamingDelta Delta { get; set; } = new();
}
