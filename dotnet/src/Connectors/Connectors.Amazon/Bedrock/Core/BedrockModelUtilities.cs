// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
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
    /// Gets the system messages with optional cache point injection for prompt caching.
    /// </summary>
    /// <param name="chatHistory">The ChatHistory object to be parsed.</param>
    /// <param name="enableSystemCaching">Whether to enable caching for system messages.</param>
    /// <param name="cacheBreakpoint">Optional index where to place the cache breakpoint. If null, places at the end.</param>
    /// <returns>The list of SystemContentBlock for the converse request with cache points if enabled.</returns>
    internal static List<SystemContentBlock> GetSystemMessagesWithCaching(
        ChatHistory chatHistory,
        bool enableSystemCaching,
        int? cacheBreakpoint = null)
    {
        var systemMessages = chatHistory
            .Where(m => m.Role == AuthorRole.System)
            .ToList();

        if (systemMessages.Count == 0)
        {
            return [];
        }

        var result = new List<SystemContentBlock>();

        for (int i = 0; i < systemMessages.Count; i++)
        {
            result.Add(new SystemContentBlock { Text = systemMessages[i].Content });

            // Add cache point if enabled and we're at the specified breakpoint or at the end
            bool shouldAddCachePoint = enableSystemCaching &&
                ((cacheBreakpoint.HasValue && i == cacheBreakpoint.Value) ||
                 (!cacheBreakpoint.HasValue && i == systemMessages.Count - 1));

            if (shouldAddCachePoint)
            {
                result.Add(new SystemContentBlock
                {
                    CachePoint = new CachePointBlock { Type = "default" }
                });
            }
        }

        return result;
    }

    /// <summary>
    /// Creates the list of user and assistant messages for the Converse Request from the Chat History.
    /// </summary>
    /// <param name="chatHistory">The ChatHistory object to be building the message list from.</param>
    /// <returns>The list of messages for the converse request.</returns>
    /// <exception cref="ArgumentException">Thrown if invalid last message in chat history.</exception>
    internal static List<Message> BuildMessageList(ChatHistory chatHistory)
    {
        // Check that the text from the latest message in the chat history  is not empty.
        Verify.NotNullOrEmpty(chatHistory);
        string? text = chatHistory[chatHistory.Count - 1].Content;
        if (string.IsNullOrWhiteSpace(text))
        {
            throw new ArgumentException("Last message in chat history was null or whitespace.");
        }
        return chatHistory
            .Where(m => m.Role != AuthorRole.System)
            .Select(m => new Message
            {
                Role = MapAuthorRoleToConversationRole(m.Role),
                Content = [new() { Text = m.Content }]
            })
            .ToList();
    }

    /// <summary>
    /// Creates the list of user and assistant messages with optional cache point injection for prompt caching.
    /// </summary>
    /// <param name="chatHistory">The ChatHistory object to be building the message list from.</param>
    /// <param name="enableMessageCaching">Whether to enable caching for messages.</param>
    /// <param name="cacheBreakpoints">Optional list of message indices where cache breakpoints should be placed.</param>
    /// <returns>The list of messages for the converse request with cache points if enabled.</returns>
    /// <exception cref="ArgumentException">Thrown if invalid last message in chat history or invalid cache breakpoints.</exception>
    internal static List<Message> BuildMessageListWithCaching(
        ChatHistory chatHistory,
        bool enableMessageCaching,
        List<int>? cacheBreakpoints = null)
    {
        // Check that the text from the latest message in the chat history is not empty.
        Verify.NotNullOrEmpty(chatHistory);
        string? text = chatHistory[chatHistory.Count - 1].Content;
        if (string.IsNullOrWhiteSpace(text))
        {
            throw new ArgumentException("Last message in chat history was null or whitespace.");
        }

        var nonSystemMessages = chatHistory
            .Where(m => m.Role != AuthorRole.System)
            .ToList();

        // Validate cache breakpoints
        if (enableMessageCaching && cacheBreakpoints != null)
        {
            if (cacheBreakpoints.Count > 2)
            {
                throw new ArgumentException("Maximum of 2 message cache breakpoints are allowed.");
            }

            foreach (var breakpoint in cacheBreakpoints)
            {
                if (breakpoint < 0 || breakpoint >= nonSystemMessages.Count)
                {
                    throw new ArgumentException($"Cache breakpoint {breakpoint} is out of range. Valid range: 0-{nonSystemMessages.Count - 1}");
                }
            }
        }

        var result = new List<Message>();

        for (int i = 0; i < nonSystemMessages.Count; i++)
        {
            var contentBlocks = new List<ContentBlock>
            {
                new() { Text = nonSystemMessages[i].Content }
            };

            // Add cache point if enabled and this index is in the breakpoints list
            if (enableMessageCaching && cacheBreakpoints != null && cacheBreakpoints.Contains(i))
            {
                contentBlocks.Add(new ContentBlock
                {
                    CachePoint = new CachePointBlock { Type = "default" }
                });
            }

            result.Add(new Message
            {
                Role = MapAuthorRoleToConversationRole(nonSystemMessages[i].Role),
                Content = contentBlocks
            });
        }

        return result;
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
