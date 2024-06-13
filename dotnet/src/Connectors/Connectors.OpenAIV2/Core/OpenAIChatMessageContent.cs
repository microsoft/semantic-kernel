// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Chat;
using OpenAIChatCompletion = OpenAI.Chat.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// OpenAI specialized chat message content
/// </summary>
public sealed class OpenAIChatMessageContent : ChatMessageContent
{
    /// <summary>
    /// Gets the metadata key for the <see cref="ChatToolCall.Id"/> name property.
    /// </summary>
    public static string ToolIdProperty => $"{nameof(ChatToolCall)}.{nameof(ChatToolCall.Id)}";

    /// <summary>
    /// Gets the metadata key for the list of <see cref="ChatToolCall"/>.
    /// </summary>
    internal static string FunctionToolCallsProperty => $"{nameof(ChatMessage)}.FunctionToolCalls";

    internal OpenAIChatMessageContent(OpenAIChatCompletion chatCompletionResult)
    {
        this.Role = new AuthorRole(chatCompletionResult.Role.ToString());

        foreach (var item in chatCompletionResult.Content)
        {
            switch (item.Kind.ToString())
            {
                case nameof(ChatMessageContentPartKind.Text):
                {
                    this.Items.Add(new TextContent(item.Text) { ModelId = this.ModelId });
                    break;
                }
                case nameof(ChatMessageContentPartKind.Image):
                {
                    if (item.ImageUri is not null)
                    {
                        this.Items.Add(new ImageContent(item.ImageUri) { ModelId = this.ModelId });
                    }
                    else
                    {
                        this.Items.Add(new ImageContent(item.ImageBytes) { MimeType = item.ImageBytesMediaType, ModelId = this.ModelId });
                    }
                    break;
                }
                default:
                {
                    throw new NotSupportedException($"The content kind {item.Kind} is not supported.");
                }
            }
        }

        foreach (var toolCall in chatCompletionResult.ToolCalls)
        {
            // Adding items of 'FunctionCallContent' type to the 'Items' collection even though the function calls are available via the 'ToolCalls' property.
            // This allows consumers to work with functions in an LLM-agnostic way.
            if (toolCall is ChatToolCall functionToolCall)
            {
                var functionCallContent = ClientCore.GetFunctionCallContent(functionToolCall);
                this.Items.Add(functionCallContent);
            }
        }
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIChatMessageContent"/> class.
    /// </summary>
    internal OpenAIChatMessageContent(ChatMessageRole role, string? content, string modelId, IReadOnlyList<ChatToolCall> toolCalls, IReadOnlyDictionary<string, object?>? metadata = null)
        : base(new AuthorRole(role.ToString()), content, modelId, content, System.Text.Encoding.UTF8, CreateMetadataDictionary(toolCalls, metadata))
    {
        this.ToolCalls = toolCalls;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIChatMessageContent"/> class.
    /// </summary>
    internal OpenAIChatMessageContent(AuthorRole role, string? content, string modelId, IReadOnlyList<ChatToolCall> toolCalls, IReadOnlyDictionary<string, object?>? metadata = null)
        : base(role, content, modelId, content, System.Text.Encoding.UTF8, CreateMetadataDictionary(toolCalls, metadata))
    {
        this.ToolCalls = toolCalls;
    }

    /// <summary>
    /// A list of the tools called by the model.
    /// </summary>
    public IReadOnlyList<ChatToolCall> ToolCalls { get; }

    /// <summary>
    /// Retrieve the resulting function from the chat result.
    /// </summary>
    /// <returns>The <see cref="OpenAIFunctionToolCall"/>, or null if no function was returned by the model.</returns>
    public IReadOnlyList<OpenAIFunctionToolCall> GetOpenAIFunctionToolCalls()
    {
        List<OpenAIFunctionToolCall>? functionToolCallList = null;

        foreach (var toolCall in this.ToolCalls)
        {
            if (toolCall is ChatToolCall functionToolCall)
            {
                (functionToolCallList ??= []).Add(new OpenAIFunctionToolCall(functionToolCall));
            }
        }

        if (functionToolCallList is not null)
        {
            return functionToolCallList;
        }

        return [];
    }

    private static IReadOnlyDictionary<string, object?>? CreateMetadataDictionary(
        IReadOnlyList<ChatToolCall> toolCalls,
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
            newDictionary.Add(FunctionToolCallsProperty, toolCalls.OfType<ChatToolCall>().ToList());

            return newDictionary;
        }

        return original;
    }
}
