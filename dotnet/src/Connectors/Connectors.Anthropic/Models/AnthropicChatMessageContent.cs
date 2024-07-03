// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Anthropic.Core;

namespace Microsoft.SemanticKernel.Connectors.Anthropic;

/// <summary>
/// Anthropic specialized chat message content
/// </summary>
public sealed class AnthropicChatMessageContent : ChatMessageContent
{
    /// <summary>
    /// Creates a new instance of the <see cref="AnthropicChatMessageContent"/> class
    /// </summary>
    [JsonConstructor]
    internal AnthropicChatMessageContent() { }

    /// <summary>
    /// Initializes a new instance of the <see cref="AnthropicChatMessageContent"/> class.
    /// </summary>
    /// <param name="role">Role of the author of the message</param>
    /// <param name="items">Instance of <see cref="ChatMessageContentItemCollection"/> with content items</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="innerContent">Inner content object reference</param>
    /// <param name="metadata">Additional metadata</param>
    internal AnthropicChatMessageContent(
        AuthorRole role,
        ChatMessageContentItemCollection items,
        string modelId,
        object? innerContent = null,
        AnthropicMetadata? metadata = null)
        : base(
            role: role,
            items: items,
            modelId: modelId,
            innerContent: innerContent,
            encoding: Encoding.UTF8,
            metadata: metadata) { }

    /// <summary>
    /// The metadata associated with the content.
    /// </summary>
    public new AnthropicMetadata? Metadata => (AnthropicMetadata?)base.Metadata;
}
