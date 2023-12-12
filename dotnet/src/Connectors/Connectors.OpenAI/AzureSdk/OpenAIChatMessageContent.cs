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
    /// Gets the metadata key for the <see cref="ChatCompletionsToolCall.Id"/> name property.
    /// </summary>
    public static string ToolCallsProperty => $"{nameof(ChatResponseMessage)}.{nameof(ChatResponseMessage.ToolCalls)}";

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIChatMessageContent"/> class.
    /// </summary>
    /// <param name="chatMessage">Azure SDK chat message</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="metadata">Additional metadata</param>
    internal OpenAIChatMessageContent(ChatResponseMessage chatMessage, string modelId, Dictionary<string, object?>? metadata = null)
        : base(new AuthorRole(chatMessage.Role.ToString()), chatMessage.Content, modelId, chatMessage, System.Text.Encoding.UTF8, metadata ?? new Dictionary<string, object?>(1))
    {
        this.ToolCalls = chatMessage.ToolCalls;
        this.Metadata!.Add(ToolCallsProperty, chatMessage.ToolCalls);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIChatMessageContent"/> class.
    /// </summary>
    internal OpenAIChatMessageContent(ChatRole role, string content, string modelId, IReadOnlyList<ChatCompletionsToolCall> toolCalls, Dictionary<string, object?>? metadata = null)
        : base(new AuthorRole(role.ToString()), content, modelId, content, System.Text.Encoding.UTF8, metadata ?? new Dictionary<string, object?>(1))
    {
        this.ToolCalls = toolCalls;
        this.Metadata![ToolCallsProperty] = toolCalls;
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
        if (this.ToolCalls is not null)
        {
            List<OpenAIFunctionToolCall>? list = null;

            for (int i = 0; i < this.ToolCalls.Count; i++)
            {
                if (this.ToolCalls[i] is ChatCompletionsFunctionToolCall ftc)
                {
                    (list ??= new List<OpenAIFunctionToolCall>()).Add(new OpenAIFunctionToolCall(ftc));
                }
            }

            if (list is not null)
            {
                return list;
            }
        }

        return Array.Empty<OpenAIFunctionToolCall>();
    }
}
