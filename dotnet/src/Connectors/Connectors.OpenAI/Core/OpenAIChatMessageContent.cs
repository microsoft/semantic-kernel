// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
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
    /// Gets the metadata key for the tool id.
    /// </summary>
    public static string ToolIdProperty => "ChatCompletionsToolCall.Id";

    /// <summary>
    /// Gets the metadata key for the list of <see cref="ChatToolCall"/>.
    /// </summary>
    internal static string FunctionToolCallsProperty => "ChatResponseMessage.FunctionToolCalls";

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIChatMessageContent"/> class.
    /// This constructor is for internal use and JSON deserialization.
    /// </summary>
    [JsonConstructor]
    internal OpenAIChatMessageContent()
    {
        this.Role = AuthorRole.User; // Default role
        this.ToolCalls = [];
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIChatMessageContent"/> class.
    /// </summary>
    internal OpenAIChatMessageContent(OpenAIChatCompletion completion, string modelId, IReadOnlyDictionary<string, object?>? metadata = null)
        : base(new AuthorRole(completion.Role.ToString()), CreateContentItems(completion.Content), modelId, completion, System.Text.Encoding.UTF8, CreateMetadataDictionary(completion.ToolCalls, metadata))
    {
        this.ToolCalls = completion.ToolCalls;
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

    private static ChatMessageContentItemCollection CreateContentItems(IReadOnlyList<ChatMessageContentPart> contentUpdate)
    {
        ChatMessageContentItemCollection collection = [];

        foreach (var part in contentUpdate)
        {
            // We only support text content for now.
            if (part.Kind == ChatMessageContentPartKind.Text)
            {
                collection.Add(new TextContent(part.Text));
            }
        }

        return collection;
    }

    /// <summary>
    /// A list of the tools called by the model.
    /// </summary>
    [JsonConverter(typeof(ChatToolCallListJsonConverter))]
    public IReadOnlyList<ChatToolCall> ToolCalls { get; set; }

    /// <summary>
    /// Retrieve the resulting function from the chat result.
    /// </summary>
    /// <returns>The <see cref="OpenAIFunctionToolCall"/>, or null if no function was returned by the model.</returns>
    public IReadOnlyList<OpenAIFunctionToolCall> GetOpenAIFunctionToolCalls()
    {
        List<OpenAIFunctionToolCall>? functionToolCallList = null;

        foreach (var toolCall in this.ToolCalls)
        {
            if (toolCall.Kind == ChatToolCallKind.Function)
            {
                (functionToolCallList ??= []).Add(new OpenAIFunctionToolCall(toolCall));
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
            newDictionary.Add(FunctionToolCallsProperty, toolCalls.Where(ctc => ctc.Kind == ChatToolCallKind.Function).ToList());

            return newDictionary;
        }

        return original;
    }
}
