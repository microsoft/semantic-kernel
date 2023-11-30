// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130
using System.Collections.Generic;
using System.Diagnostics;
using Azure.AI.OpenAI;

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
        Verify.NotNull(chatHistory);

        chatHistory.AddMessage(AuthorRole.Function, message, new Dictionary<string, string>(1) { { "Name", functionName } });
    }

    /// <summary>
    /// Add an assistant message to the chat history.
    /// </summary>
    /// <param name="chatHistory">Chat history</param>
    /// <param name="chatResult">Chat result from the model</param>
    public static void AddAssistantMessage(this ChatHistory chatHistory, IChatResult chatResult)
    {
        Verify.NotNull(chatHistory);

        var chatMessage = chatResult.ModelResult.GetOpenAIChatResult().Choice.Message;
        if (!string.IsNullOrEmpty(chatMessage.Content) || chatMessage.FunctionCall is not null)
        {
            chatHistory.AddAssistantMessage(chatMessage.Content, chatMessage.FunctionCall);
        }
    }

    /// <summary>
    /// Add an assistant message to the chat history.
    /// </summary>
    internal static void AddAssistantMessage(this ChatHistory chatHistory, string? message, FunctionCall? functionCall)
    {
        Debug.Assert(chatHistory is not null);
        Debug.Assert(!string.IsNullOrEmpty(message) || functionCall is not null);

        chatHistory!.AddMessage(
            AuthorRole.Assistant,
            message ?? string.Empty,
            functionCall is not null ?
                new Dictionary<string, string>(2)
                {
                    { "Name", functionCall.Name },
                    { "Arguments", functionCall.Arguments }
                } :
                null);
    }
}
