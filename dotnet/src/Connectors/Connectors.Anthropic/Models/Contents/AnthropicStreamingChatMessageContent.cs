// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.Anthropic;

/// <summary>
/// Anthropic specialized streaming chat message content
/// </summary>
public sealed class AnthropicStreamingChatMessageContent : StreamingChatMessageContent
{
    /// <summary>
    /// Creates a new instance of the <see cref="AnthropicStreamingChatMessageContent"/> class
    /// </summary>
    /// <param name="role">Role of the author of the message</param>
    /// <param name="content">Content of the message</param>
    /// <param name="innerContent">Inner content object reference</param>
    /// <param name="choiceIndex">Choice index</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="encoding">Encoding of the chat</param>
    /// <param name="metadata">Additional metadata</param>
    [JsonConstructor]
    public AnthropicStreamingChatMessageContent(
        AuthorRole? role,
        string? content,
        object? innerContent = null,
        int choiceIndex = 0,
        string? modelId = null,
        Encoding? encoding = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(role, content, innerContent, choiceIndex, modelId, encoding, metadata) { }

    /// <summary>
    /// The metadata associated with the content.
    /// </summary>
    public new AnthropicMetadata? Metadata
    {
        get => base.Metadata as AnthropicMetadata;
        init => base.Metadata = value;
    }
}
