// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.AI.ChatCompletion;
#pragma warning restore IDE0130

/// <summary>
/// OpenAI-specific extensions to the <see cref="ChatHistory"/> class.
/// </summary>
public static class ChatHistoryExtensions
{
    /// <summary>
    /// Add a function message to the chat history
    /// </summary>
    /// <param name="chatHistory">Chat history</param>
    /// <param name="message">Message content</param>
    /// <param name="functionName">Name of the function that generated the content</param>
    public static void AddFunctionMessage(this ChatHistory chatHistory, string message, string functionName)
    {
        chatHistory.AddMessage(AuthorRole.Function, message, new Dictionary<string, string> { { "Name", functionName } });
    }

    /// <summary>
    /// Add an assistant message to the chat history.
    /// </summary>
    /// <param name="chatHistory">Chat history</param>
    /// <param name="chatResult">Chat result from the model</param>
    public static void AddAssistantMessage(this ChatHistory chatHistory, IChatResult chatResult)
    {
        var chatMessage = chatResult.ModelResult.GetOpenAIChatResult().Choice.Message;

        if (!string.IsNullOrEmpty(chatMessage.Content))
        {
            chatHistory.AddAssistantMessage(chatMessage.Content);
        }

        var functionCall = chatMessage.FunctionCall;
        if (functionCall is not null)
        {
            chatHistory.AddMessage(AuthorRole.Assistant, string.Empty, new Dictionary<string, string>
            {
                { "Name", functionCall.Name },
                { "Arguments", functionCall.Arguments }
            });
        }
    }
}
