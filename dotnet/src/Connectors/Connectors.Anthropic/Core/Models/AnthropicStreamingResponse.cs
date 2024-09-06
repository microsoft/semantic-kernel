// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Core.Models;

/// <summary>
/// Represents the response from the Anthropic streaming API.
/// <see href="https://docs.anthropic.com/en/api/messages-streaming#raw-http-stream-response"/>
/// </summary>
internal sealed class AnthropicStreamingResponse
{
    /// <summary>
    /// SSE data type.
    /// </summary>
    [JsonRequired]
    [JsonPropertyName("type")]
    public string Type { get; init; } = null!;

    /// <summary>
    /// Response message, only if the type is "message_start", otherwise null.
    /// </summary>
    [JsonPropertyName("message")]
    public AnthropicResponse? Response { get; init; }

    /// <summary>
    /// Index of a message.
    /// </summary>
    [JsonPropertyName("index")]
    public int Index { get; init; }

#pragma warning disable CS0649 // Field is assigned via reflection
    [JsonPropertyName("content_block")]
    [JsonInclude]
    private readonly AnthropicContent? _contentBlock;

    [JsonPropertyName("delta")]
    [JsonInclude]
    private readonly JsonNode? _delta;
#pragma warning restore CS0649

    /// <summary>
    /// Delta of anthropic content, only if the type is "content_block_start" or "content_block_delta", otherwise null.
    /// </summary>
    public AnthropicContent? ContentDelta =>
        this.Type switch
        {
            "content_block_start" => this._contentBlock,
            "content_block_delta" => this._delta?.Deserialize<AnthropicContent>(),
            _ => null
        };

    /// <summary>
    /// Usage metadata, only if the type is "message_delta", otherwise null.
    /// </summary>
    public AnthropicUsage? Usage { get; init; }

    /// <summary>
    /// Stop reason metadata, only if the type is "message_delta", otherwise null.
    /// </summary>
    public StopDelta? StopMetadata => this.Type == "message_delta" ? this._delta?.Deserialize<StopDelta>() : null;

    /// <summary>
    /// Represents the reason that message streaming stopped.
    /// </summary>
    public sealed class StopDelta
    {
        /// <summary>
        /// The reason that we stopped.
        /// </summary>
        [JsonPropertyName("stop_reason")]
        public AnthropicFinishReason? StopReason { get; init; }

        /// <summary>
        /// Which custom stop sequence was generated, if any.
        /// This value will be a non-null string if one of your custom stop sequences was generated.
        /// </summary>
        [JsonPropertyName("stop_sequence")]
        public string? StopSequence { get; init; }
    }
}
