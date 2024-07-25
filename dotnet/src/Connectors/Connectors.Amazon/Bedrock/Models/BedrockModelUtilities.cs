// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Connectors.Amazon.Models;

/// <summary>
/// Utilities class for functions all Bedrock models need to use.
/// </summary>
public class BedrockModelUtilities
{
    /// <summary>
    /// Maps the AuthorRole to the corresponding ConversationRole because AuthorRole is static and { readonly get; }.
    /// </summary>
    /// <param name="role"></param>
    /// <returns></returns>
    /// <exception cref="ArgumentOutOfRangeException"></exception>
    public ConversationRole MapRole(AuthorRole role)
    {
        if (role == AuthorRole.User)
        {
            return ConversationRole.User;
        }

        if (role == AuthorRole.Assistant)
        {
            return ConversationRole.Assistant;
        }
        throw new ArgumentOutOfRangeException(nameof(role), $"Invalid role: {role}");
    }
    /// <summary>
    /// Gets the system messages from the ChatHistory and adds them to the ConverseRequest System parameter.
    /// </summary>
    /// <param name="chatHistory"></param>
    /// <returns></returns>
    public List<SystemContentBlock> GetSystemMessages(ChatHistory chatHistory)
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
    public List<Message> BuildMessageList(ChatHistory chatHistory)
    {
        return chatHistory
            .Where(m => m.Role != AuthorRole.System)
            .Select(m => new Message
            {
                Role = new BedrockModelUtilities().MapRole(m.Role),
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
    public TValue GetExtensionDataValue<TValue>(IDictionary<string, object>? extensionData, string key, TValue defaultValue)
    {
        if (extensionData?.TryGetValue(key, out object? value) == true && value is TValue typedValue)
        {
            return typedValue;
        }
        return defaultValue;
    }
}
