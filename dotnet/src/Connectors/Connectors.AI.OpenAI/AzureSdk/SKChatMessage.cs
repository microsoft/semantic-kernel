// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

/// <summary>
/// Chat message representation from Semantic Kernel ChatMessageBase Abstraction
/// </summary>
public class SKChatMessage : ChatMessageBase
{
    /// <summary>
    /// Create a new instance of a chat message
    /// </summary>
    /// <param name="message">OpenAI SDK chat message representation</param>
    public SKChatMessage(Azure.AI.OpenAI.ChatMessage message)
        : base(new AuthorRole(message.Role.ToString()), message.Content)
    {
    }
}
