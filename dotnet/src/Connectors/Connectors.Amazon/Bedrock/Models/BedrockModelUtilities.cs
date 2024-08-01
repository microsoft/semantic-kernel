// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Connectors.Amazon.Models;

/// <summary>
/// Utilities class for functions all Bedrock models need to use.
/// </summary>
public static class BedrockModelUtilities
{
    /// <summary>
    /// Maps the AuthorRole to the corresponding ConversationRole because AuthorRole is static and { readonly get; }. Only called if AuthorRole is User or Assistant (System set outside/beforehand).
    /// </summary>
    /// <param name="role"></param>
    /// <returns></returns>
    /// <exception cref="ArgumentOutOfRangeException"></exception>
    public static ConversationRole MapAuthorRoleToConversationRole(AuthorRole role)
    {
        if (role == AuthorRole.User)
        {
            return ConversationRole.User;
        }

        if (role == AuthorRole.Assistant)
        {
            return ConversationRole.Assistant;
        }
        throw new ArgumentException($"Invalid role: {role}");
    }
    /// <summary>
    /// Gets the system messages from the ChatHistory and adds them to the ConverseRequest System parameter.
    /// </summary>
    /// <param name="chatHistory"></param>
    /// <returns></returns>
    public static List<SystemContentBlock> GetSystemMessages(ChatHistory chatHistory)
    {
        return chatHistory
            .Where(m => m.Role == AuthorRole.System)
            .Select(m => new SystemContentBlock { Text = m.Content })
            .ToList();
    }
    /// <summary>
    /// Creates the list of user and assistant messages for the Converse Request from the Chat History.
    /// </summary>
    /// <param name="chatHistory"></param>
    /// <returns></returns>
    public static List<Message> BuildMessageList(ChatHistory chatHistory)
    {
        // Check that the text from the latest message in the chat history  is not empty.
        Verify.NotNullOrEmpty(chatHistory);
        string? text = chatHistory[^1].Content;
        if (string.IsNullOrWhiteSpace(text))
        {
            throw new ArgumentException("Last message in chat history was null or whitespace.");
        }
        return chatHistory
            .Where(m => m.Role != AuthorRole.System)
            .Select(m => new Message
            {
                Role = MapAuthorRoleToConversationRole(m.Role),
                Content = new List<ContentBlock> { new() { Text = m.Content } }
            })
            .ToList();
    }
    /// <summary>
    /// Gets the prompt execution settings extension data for the model request body build.
    /// </summary>
    /// <param name="extensionData"></param>
    /// <param name="key"></param>
    /// <param name="defaultValue"></param>
    /// <typeparam name="TValue"></typeparam>
    /// <returns></returns>
    public static TValue GetExtensionDataValue<TValue>(IDictionary<string, object>? extensionData, string key, TValue defaultValue)
    {
        if (extensionData?.TryGetValue(key, out object? value) == true && value is TValue typedValue)
        {
            return typedValue;
        }
        return defaultValue;
    }
}
