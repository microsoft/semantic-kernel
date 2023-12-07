// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics;
using System.Text;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;

namespace Microsoft.SemanticKernel.ChatCompletion;

/// <summary>
/// OpenAI-specific extensions to the <see cref="ChatHistory"/> class.
/// </summary>
public static class OpenAIChatHistoryExtensions
{
    private static readonly AuthorRole s_functionAuthorRole = new("function");

    /// <summary>
    /// Add a function message to the chat history
    /// </summary>
    /// <param name="chatHistory">Chat history</param>
    /// <param name="message">Message content</param>
    /// <param name="functionName">Name of the function that generated the content</param>
    public static void AddFunctionMessage(this ChatHistory chatHistory, string message, string functionName)
    {
        Verify.NotNull(chatHistory);

        chatHistory.AddMessage(s_functionAuthorRole, message, metadata: new Dictionary<string, object?>(1) { { OpenAIChatMessageContent.FunctionNameProperty, functionName } });
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
            Encoding.UTF8,
            functionCall is not null ?
                new Dictionary<string, object?>(2)
                {
                    { OpenAIChatMessageContent.FunctionNameProperty, functionCall.Name },
                    { OpenAIChatMessageContent.FunctionArgumentsProperty, functionCall.Arguments }
                } :
            null);
    }
}
