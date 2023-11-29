// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;

/// <summary>
/// OpenAI Chat content
/// See https://platform.openai.com/docs/guides/chat for details
/// </summary>
public class OpenAIChatHistory : ChatHistory
{
    /// <summary>
    /// Create a new and empty chat history
    /// </summary>
    /// <param name="systemMessage">Optional instructions for the assistant</param>
    public OpenAIChatHistory(string? systemMessage = null)
    {
        if (!string.IsNullOrWhiteSpace(systemMessage))
        {
            this.AddSystemMessage(systemMessage!);
        }
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIChatHistory"/> class based on <see cref="ChatHistory"/>.
    /// </summary>
    /// <param name="chatHistory"></param>
    public OpenAIChatHistory(ChatHistory chatHistory)
    {
        chatHistory.ForEach(message =>
        {
            this.AddMessage(message.Role, message.Content);
        });
    }
}
