// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion.ChatCompletion;

/// <summary>
/// HTTP Schema for streaming completion response. Adapted from <see href="https://github.com/oobabooga/text-generation-webui/blob/main/extensions/api/streaming_api.py"/>
/// </summary>
public sealed class ChatCompletionStreamingResponse : CompletionStreamingResponseBase
{
    /// <summary>
    /// A field used by Oobabooga with the text chunk sent in the websocket message.
    /// </summary>
    [JsonPropertyName("text")]
    public ChatHistory History { get; set; } = new();
}
