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
