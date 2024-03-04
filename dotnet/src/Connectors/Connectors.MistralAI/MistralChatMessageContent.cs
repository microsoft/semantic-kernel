// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.MistralAI.Client;

namespace Microsoft.SemanticKernel.Connectors.MistralAI;

/// <summary>
/// Mistral specialized chat message content
/// </summary>
public sealed class MistralChatMessageContent : ChatMessageContent
{
    /// <summary>
    /// Initializes a new instance of the <see cref="MistralChatMessageContent"/> class.
    /// </summary>
    /// <param name="chatMessage">Mistral chat message</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="metadata">Additional metadata</param>
    internal MistralChatMessageContent(MistralChatMessage chatMessage, string modelId, IReadOnlyDictionary<string, object?>? metadata = null)
        : base(new AuthorRole(chatMessage.Role), chatMessage.Content, modelId, chatMessage, System.Text.Encoding.UTF8, metadata)
    {
    }
}
