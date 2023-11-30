// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI.ChatCompletion;

#pragma warning disable IDE0130 // Namespace does not match folder structure
namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI;
#pragma warning restore IDE0130 // Namespace does not match folder structure

/// <summary>
/// Chat message representation fir Azure OpenAI
/// </summary>
public class AzureOpenAIChatMessage : SemanticKernel.AI.ChatCompletion.ChatMessage
{
    /// <summary>
    /// Exposes the underlying OpenAI SDK chat message representation
    /// </summary>
    public Azure.AI.OpenAI.ChatMessage? InnerChatMessage { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureOpenAIChatMessage"/> class.
    /// </summary>
    /// <param name="message">OpenAI SDK chat message representation</param>
    public AzureOpenAIChatMessage(Azure.AI.OpenAI.ChatMessage message)
        : base(new AuthorRole(message.Role.ToString()), message.Content)
    {
        this.InnerChatMessage = message;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureOpenAIChatMessage"/> class.
    /// </summary>
    /// <param name="role">Role of the author of the message.</param>
    /// <param name="content">Content of the message.</param>
    public AzureOpenAIChatMessage(string role, string content)
        : base(new AuthorRole(role), content)
    {
    }
}
