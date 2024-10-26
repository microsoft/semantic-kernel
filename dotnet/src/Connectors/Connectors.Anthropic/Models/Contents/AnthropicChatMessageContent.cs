// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

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
    /// The metadata associated with the content.
    /// </summary>
    public new AnthropicMetadata? Metadata
    {
        get => base.Metadata as AnthropicMetadata;
        init => base.Metadata = value;
    }
}
