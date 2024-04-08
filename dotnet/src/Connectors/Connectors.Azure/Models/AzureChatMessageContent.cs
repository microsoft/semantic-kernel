// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.Azure;

/// <summary>
/// OpenAI specialized chat message content
/// </summary>
public sealed class AzureChatMessageContent : ChatMessageContent
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AzureChatMessageContent"/> class.
    /// </summary>
    internal AzureChatMessageContent(ChatResponseMessage chatMessage, string modelId, IReadOnlyDictionary<string, object?>? metadata = null)
        : base(new AuthorRole(chatMessage.Role.ToString()), chatMessage.Content, modelId, chatMessage, System.Text.Encoding.UTF8, metadata)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureChatMessageContent"/> class.
    /// </summary>
    internal AzureChatMessageContent(AuthorRole role, string? content, string modelId, IReadOnlyDictionary<string, object?>? metadata = null)
        : base(role, content, modelId, content, System.Text.Encoding.UTF8, metadata)
    {
    }
}
