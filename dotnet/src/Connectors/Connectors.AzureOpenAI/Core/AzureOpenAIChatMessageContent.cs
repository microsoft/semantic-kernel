// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.AzureOpenAI;

/// <summary>
/// AzureOpenAI specialized chat message content
/// </summary>
public sealed class AzureOpenAIChatMessageContent : ChatMessageContent
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
    /// Initializes a new instance of the <see cref="AzureOpenAIChatMessageContent"/> class.
    /// </summary>
    internal AzureOpenAIChatMessageContent(ChatResponseMessage chatMessage, string modelId, IReadOnlyDictionary<string, object?>? metadata = null)
        : base(new AuthorRole(chatMessage.Role.ToString()), chatMessage.Content, modelId, chatMessage, System.Text.Encoding.UTF8, CreateMetadataDictionary(chatMessage.ToolCalls, metadata))
    {
        this.ToolCalls = chatMessage.ToolCalls;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureOpenAIChatMessageContent"/> class.
    /// </summary>
    internal AzureOpenAIChatMessageContent(ChatRole role, string? content, string modelId, IReadOnlyList<ChatCompletionsToolCall> toolCalls, IReadOnlyDictionary<string, object?>? metadata = null)
        : base(new AuthorRole(role.ToString()), content, modelId, content, System.Text.Encoding.UTF8, CreateMetadataDictionary(toolCalls, metadata))
    {
        this.ToolCalls = toolCalls;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureOpenAIChatMessageContent"/> class.
    /// </summary>
    internal AzureOpenAIChatMessageContent(AuthorRole role, string? content, string modelId, IReadOnlyList<ChatCompletionsToolCall> toolCalls, IReadOnlyDictionary<string, object?>? metadata = null)
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
    /// <returns>The <see cref="AzureOpenAIFunctionToolCall"/>, or null if no function was returned by the model.</returns>
    public IReadOnlyList<AzureOpenAIFunctionToolCall> GetOpenAIFunctionToolCalls()
    {
        List<AzureOpenAIFunctionToolCall>? functionToolCallList = null;

        foreach (var toolCall in this.ToolCalls)
        {
            if (toolCall is ChatCompletionsFunctionToolCall functionToolCall)
            {
                (functionToolCallList ??= []).Add(new AzureOpenAIFunctionToolCall(functionToolCall));
            }
        }

        if (functionToolCallList is not null)
        {
            return functionToolCallList;
        }

        return [];
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
            newDictionary.Add(FunctionToolCallsProperty, toolCalls.OfType<ChatCompletionsFunctionToolCall>().ToList());

            return newDictionary;
        }

        return original;
    }
}
