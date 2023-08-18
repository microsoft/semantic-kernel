// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

/// <summary>
/// Chat message representation from Semantic Kernel ChatMessageBase Abstraction
/// </summary>
public class SKChatMessage : ChatMessageBase
{
    /// <summary>
    /// Initializes a new instance of the <see cref="SKChatMessage"/> class.
    /// </summary>
    /// <param name="message">OpenAI SDK chat message representation</param>
    public SKChatMessage(Azure.AI.OpenAI.ChatMessage message)
        : base(new AuthorRole(message.Role.ToString()), message.Content)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="SKChatMessage"/> class.
    /// </summary>
    /// <param name="role">Role of the author of the message.</param>
    /// <param name="content">Content of the message.</param>
    public SKChatMessage(string role, string content)
        : base(new AuthorRole(role), content)
    {
    }
}
