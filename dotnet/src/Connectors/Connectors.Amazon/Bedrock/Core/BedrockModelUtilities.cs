// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Utilities class for functions all Bedrock models need to use.
/// </summary>
internal static class BedrockModelUtilities
{
    /// <summary>
    /// Maps the AuthorRole to the corresponding ConversationRole because AuthorRole is static and { readonly get; }. Only called if AuthorRole is User or Assistant (System set outside/beforehand).
    /// </summary>
    /// <param name="role">The AuthorRole to be converted to ConversationRole</param>
    /// <returns>The corresponding ConversationRole</returns>
    /// <exception cref="ArgumentOutOfRangeException">Thrown if invalid role.</exception>
    internal static ConversationRole MapAuthorRoleToConversationRole(AuthorRole role)
    {
        if (role == AuthorRole.User)
        {
            return ConversationRole.User;
        }

        if (role == AuthorRole.Assistant)
        {
            return ConversationRole.Assistant;
        }

        // Tool role maps to User in Bedrock (tool results are sent as user messages).
        if (role == AuthorRole.Tool)
        {
            return ConversationRole.User;
        }

        throw new ArgumentOutOfRangeException($"Invalid role: {role}");
    }

    /// <summary>
    /// Gets the system messages from the ChatHistory and adds them to the ConverseRequest System parameter.
    /// </summary>
    /// <param name="chatHistory">The ChatHistory object to be parsed.</param>
    /// <returns>The list of SystemContentBlock for the converse request.</returns>
    internal static List<SystemContentBlock> GetSystemMessages(ChatHistory chatHistory)
    {
        return chatHistory
            .Where(m => m.Role == AuthorRole.System)
            .Select(m => new SystemContentBlock { Text = m.Content })
            .ToList();
    }

    /// <summary>
    /// Creates the list of user and assistant messages for the Converse Request from the Chat History.
    /// Handles FunctionCallContent (tool use) and FunctionResultContent (tool result) items,
    /// and merges consecutive messages with the same Bedrock role into a single message.
    /// This is required because Bedrock expects all tool_use blocks from one assistant turn
    /// in a single message and all tool_result blocks in a single user message.
    /// </summary>
    /// <param name="chatHistory">The ChatHistory object to be building the message list from.</param>
    /// <returns>The list of messages for the converse request.</returns>
    /// <exception cref="ArgumentException">Thrown if the chat history is empty.</exception>
    internal static List<Message> BuildMessageList(ChatHistory chatHistory)
    {
        Verify.NotNullOrEmpty(chatHistory);

        var messages = new List<Message>();

        foreach (var chatMessage in chatHistory)
        {
            if (chatMessage.Role == AuthorRole.System)
            {
                continue;
            }

            var bedrockRole = MapAuthorRoleToConversationRole(chatMessage.Role);
            var contentBlocks = BuildContentBlocks(chatMessage);

            if (contentBlocks.Count == 0)
            {
                continue;
            }

            // Merge with the previous message if it has the same role.
            // This handles consecutive assistant tool-call messages and consecutive tool-result messages.
            if (messages.Count > 0 && messages[messages.Count - 1].Role == bedrockRole)
            {
                messages[messages.Count - 1].Content.AddRange(contentBlocks);
            }
            else
            {
                messages.Add(new Message
                {
                    Role = bedrockRole,
                    Content = contentBlocks
                });
            }
        }

        return messages;
    }

    /// <summary>
    /// Builds the list of Bedrock ContentBlock objects from a ChatMessageContent,
    /// handling text, FunctionCallContent (ToolUse), and FunctionResultContent (ToolResult).
    /// </summary>
    /// <param name="chatMessage">The chat message to convert.</param>
    /// <returns>A list of ContentBlock objects.</returns>
    private static List<ContentBlock> BuildContentBlocks(ChatMessageContent chatMessage)
    {
        var contentBlocks = new List<ContentBlock>();

        foreach (var item in chatMessage.Items)
        {
            switch (item)
            {
                case FunctionCallContent functionCall:
                    contentBlocks.Add(new ContentBlock
                    {
                        ToolUse = new ToolUseBlock
                        {
                            ToolUseId = functionCall.Id,
                            Name = functionCall.PluginName is not null
                                ? $"{functionCall.PluginName}-{functionCall.FunctionName}"
                                : functionCall.FunctionName,
                            Input = ConvertArgumentsToDocument(functionCall.Arguments)
                        }
                    });
                    break;

                case FunctionResultContent functionResult:
                    contentBlocks.Add(new ContentBlock
                    {
                        ToolResult = new ToolResultBlock
                        {
                            ToolUseId = functionResult.CallId,
                            Content = [new ToolResultContentBlock { Text = functionResult.Result?.ToString() ?? string.Empty }]
                        }
                    });
                    break;

                case TextContent textContent:
                    if (!string.IsNullOrEmpty(textContent.Text))
                    {
                        contentBlocks.Add(new ContentBlock { Text = textContent.Text });
                    }
                    break;

                default:
                    // For other content types, fall back to using ToString.
                    var text = item.ToString();
                    if (!string.IsNullOrEmpty(text))
                    {
                        contentBlocks.Add(new ContentBlock { Text = text });
                    }
                    break;
            }
        }

        // If no items were processed but there's text content on the message itself, use that.
        if (contentBlocks.Count == 0 && !string.IsNullOrEmpty(chatMessage.Content))
        {
            contentBlocks.Add(new ContentBlock { Text = chatMessage.Content });
        }

        return contentBlocks;
    }

    /// <summary>
    /// Converts KernelArguments to an Amazon.Runtime.Documents.Document
    /// for use as ToolUseBlock input.
    /// </summary>
    /// <param name="arguments">The arguments to convert.</param>
    /// <returns>A Document representing the arguments as a JSON-like structure.</returns>
    private static Document ConvertArgumentsToDocument(KernelArguments? arguments)
    {
        if (arguments == null || arguments.Count == 0)
        {
            return new Document(new Dictionary<string, Document>());
        }

        var dict = new Dictionary<string, Document>();
        foreach (var kvp in arguments)
        {
            dict[kvp.Key] = ConvertValueToDocument(kvp.Value);
        }

        return new Document(dict);
    }

    /// <summary>
    /// Converts a single value to a Document, handling common types.
    /// </summary>
    private static Document ConvertValueToDocument(object? value)
    {
        return value switch
        {
            null => new Document(),
            string s => new Document(s),
            bool b => new Document(b),
            int i => new Document(i),
            long l => new Document(l),
            float f => new Document(f),
            double d => new Document(d),
            decimal dec => new Document((double)dec),
            _ => new Document(value.ToString() ?? string.Empty)
        };
    }

    /// <summary>
    /// Gets the prompt execution settings extension data for the model request body build.
    /// Returns null if the extension data value is not set (default is null if TValue is a nullable type).
    /// </summary>
    /// <param name="extensionData">The execution settings extension data.</param>
    /// <param name="key">The key name of the settings parameter</param>
    /// <typeparam name="TValue">The value of the settings parameter</typeparam>
    /// <returns>The conversion to the given value of the data for execution settings</returns>
    internal static TValue? GetExtensionDataValue<TValue>(IDictionary<string, object>? extensionData, string key)
    {
        if (extensionData?.TryGetValue(key, out object? value) == true)
        {
            try
            {
                return (TValue)value;
            }
            catch (InvalidCastException)
            {
                // Handle the case where the value cannot be cast to TValue
                return default;
            }
        }

        // As long as TValue is nullable this will be properly set to null
        return default;
    }

    /// <summary>
    /// Sets Prompt Execution Settings data if the value is not null.
    /// </summary>
    /// <param name="getValue">Getter function delegate</param>
    /// <param name="setValue">Setter function delegate</param>
    /// <typeparam name="T">Parameter type</typeparam>
    internal static void SetPropertyIfNotNull<T>(Func<T?> getValue, Action<T> setValue) where T : struct
    {
        var value = getValue();
        if (value.HasValue)
        {
            setValue(value.Value);
        }
    }

    /// <summary>
    /// Sets nullable property if the value is not null.
    /// </summary>
    /// <param name="getValue">Getter function delegate</param>
    /// <param name="setValue">Setter function delegate</param>
    /// <typeparam name="T">Parameter type</typeparam>
    internal static void SetNullablePropertyIfNotNull<T>(Func<T?> getValue, Action<T?> setValue) where T : class
    {
        var value = getValue();
        setValue(value);
    }
}
