// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// OpenAI specialized chat message content
/// </summary>
public sealed class OpenAIChatMessageContent : ChatMessageContent
{
    /// <summary>
    /// Gets the metadata key for the <see cref="ChatCompletionsToolCall.Id"/> name property.
    /// </summary>
    public static string ToolIdProperty => $"{nameof(ChatCompletionsToolCall)}.{nameof(ChatCompletionsToolCall.Id)}";

    /// <summary>
    /// Gets the metadata key for the list of <see cref="ChatCompletionsFunctionToolCall"/>.
    /// </summary>
    internal static string FunctionToolCallsProperty => $"{nameof(ChatResponseMessage)}.FunctionToolCalls";

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIChatMessageContent"/> class.
    /// </summary>
    internal OpenAIChatMessageContent(ChatResponseMessage chatMessage, string modelId, IReadOnlyDictionary<string, object?>? metadata = null)
        : base(new AuthorRole(chatMessage.Role.ToString()), chatMessage.Content, modelId, chatMessage, System.Text.Encoding.UTF8, metadata)
    {
        this.ToolCalls = chatMessage.ToolCalls;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIChatMessageContent"/> class.
    /// </summary>
    internal OpenAIChatMessageContent(ChatRole role, string? content, string modelId, IReadOnlyList<ChatCompletionsToolCall> toolCalls, IReadOnlyDictionary<string, object?>? metadata = null)
        : base(new AuthorRole(role.ToString()), content, modelId, content, System.Text.Encoding.UTF8, metadata)
    {
        this.ToolCalls = toolCalls;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIChatMessageContent"/> class.
    /// </summary>
    internal OpenAIChatMessageContent(AuthorRole role, string? content, string modelId, IReadOnlyList<ChatCompletionsToolCall> toolCalls, IReadOnlyDictionary<string, object?>? metadata = null)
        : base(role, content, modelId, content, System.Text.Encoding.UTF8, metadata)
    {
        this.ToolCalls = toolCalls;
    }

    /// <summary>
    /// A list of the tools called by the model.
    /// </summary>
    public IReadOnlyList<ChatCompletionsToolCall> ToolCalls { get; }

    /// <summary>
    /// Retrieve the resulting function from the chat result.
    /// </summary>
    /// <returns>The <see cref="OpenAIFunctionToolCall"/>, or null if no function was returned by the model.</returns>
    public IReadOnlyList<OpenAIFunctionToolCall> GetOpenAIFunctionToolCalls()
    {
        List<OpenAIFunctionToolCall>? functionToolCallList = null;

        foreach (var toolCall in this.ToolCalls)
        {
            if (toolCall is ChatCompletionsFunctionToolCall functionToolCall)
            {
                (functionToolCallList ??= new List<OpenAIFunctionToolCall>()).Add(new OpenAIFunctionToolCall(functionToolCall));
            }
        }

        if (functionToolCallList is not null)
        {
            return functionToolCallList;
        }

        return Array.Empty<OpenAIFunctionToolCall>();
    }
}
