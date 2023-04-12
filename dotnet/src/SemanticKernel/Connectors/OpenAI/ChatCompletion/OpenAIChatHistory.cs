// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.OpenAI.ChatCompletion;

/// <summary>
/// OpenAI Chat content
/// See https://platform.openai.com/docs/guides/chat for details
/// </summary>
public class OpenAIChatHistory : ChatHistory
{
    private const string SystemRole = "system";
    private const string AssistantRole = "assistant";
    private const string UserRole = "user";

    /// <summary>
    /// Create a new and empty chat history
    /// </summary>
    /// <param name="assistantInstructions">Optional instructions for the assistant</param>
    public OpenAIChatHistory(string? assistantInstructions = null)
    {
        if (!assistantInstructions.IsNullOrWhitespace())
        {
            this.AddSystemMessage(assistantInstructions);
        }
    }

    /// <summary>
    /// Add a system message to the chat history
    /// </summary>
    /// <param name="content">Message content</param>
    public void AddSystemMessage(string content)
    {
        this.AddMessage(SystemRole, content);
    }

    /// <summary>
    /// Add an assistant message to the chat history
    /// </summary>
    /// <param name="content">Message content</param>
    public void AddAssistantMessage(string content)
    {
        this.AddMessage(AssistantRole, content);
    }

    /// <summary>
    /// Add a user message to the chat history
    /// </summary>
    /// <param name="content">Message content</param>
    public void AddUserMessage(string content)
    {
        this.AddMessage(UserRole, content);
    }
}
