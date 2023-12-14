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
    internal OpenAIChatMessageContent(ChatResponseMessage chatMessage, string modelId, IReadOnlyDictionary<string, object?>? metadata = null)
        : base(new AuthorRole(chatMessage.Role.ToString()), chatMessage.Content, modelId, chatMessage, System.Text.Encoding.UTF8, CreateMetadataDictionary(chatMessage.ToolCalls, metadata))
    {
        this.ToolCalls = chatMessage.ToolCalls;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIChatMessageContent"/> class.
    /// </summary>
    internal OpenAIChatMessageContent(ChatRole role, string? content, string modelId, IReadOnlyList<ChatCompletionsToolCall> toolCalls, IReadOnlyDictionary<string, object?>? metadata = null)
        : base(new AuthorRole(role.ToString()), content, modelId, content, System.Text.Encoding.UTF8, CreateMetadataDictionary(toolCalls, metadata))
    {
        this.ToolCalls = toolCalls;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIChatMessageContent"/> class.
    /// </summary>
    internal OpenAIChatMessageContent(AuthorRole role, string? content, string modelId, IReadOnlyList<ChatCompletionsToolCall> toolCalls, IReadOnlyDictionary<string, object?>? metadata = null)
        : base(role, content, modelId, content, System.Text.Encoding.UTF8, CreateMetadataDictionary(toolCalls, metadata))
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

    private static IReadOnlyDictionary<string, object?>? CreateMetadataDictionary(
        IReadOnlyList<ChatCompletionsToolCall> toolCalls,
        IReadOnlyDictionary<string, object?>? original)
    {
        // We only need to augment the metadata if there are any tool calls.
        if (toolCalls.Count > 0)
        {
            Dictionary<string, object?> newDictionary;
            if (original is null)
            {
                // There's no existing metadata to clone; just allocate a new dictionary.
                newDictionary = new Dictionary<string, object?>(1);
            }
            else if (original is IDictionary<string, object?> origIDictionary)
            {
                // Efficiently clone the old dictionary to a new one.
                newDictionary = new Dictionary<string, object?>(origIDictionary);
            }
            else
            {
                // There's metadata to clone but we have to do so one item at a time.
                newDictionary = new Dictionary<string, object?>(original.Count + 1);
                foreach (var kvp in original)
                {
                    newDictionary[kvp.Key] = kvp.Value;
                }
            }

            // Add the additional entry.
            newDictionary.Add(ToolCallsProperty, toolCalls);

            return newDictionary;
        }

        return original;
    }
}
