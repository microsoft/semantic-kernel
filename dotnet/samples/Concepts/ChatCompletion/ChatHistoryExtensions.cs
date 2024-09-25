// Copyright (c) Microsoft. All rights reserved.

using Microsoft.ML.Tokenizers;
using Microsoft.SemanticKernel.ChatCompletion;

namespace ChatCompletion;

/// <summary>
/// Extension methods for <see cref="ChatHistory"/>."/>
/// </summary>
internal static class ChatHistoryExtensions
{
    private static readonly Tokenizer s_tokenizer = TiktokenTokenizer.CreateForModel("gpt-4");

    /// <summary>
    /// Add a system message to the chat history
    /// </summary>
    /// <param name="chatHistory">Chat history instance</param>
    /// <param name="content">Message content</param>
    public static void AddSystemMessageWithTokenCount(this ChatHistory chatHistory, string content)
    {
        IReadOnlyDictionary<string, object?> metadata = new Dictionary<string, object?>
        {
            ["TokenCount"] = s_tokenizer.CountTokens(content)
        };
        chatHistory.AddMessage(AuthorRole.System, content, metadata: metadata);
    }

    /// <summary>
    /// Add a user message to the chat history
    /// </summary>
    /// <param name="chatHistory">Chat history instance</param>
    /// <param name="content">Message content</param>
    public static void AddUserMessageWithTokenCount(this ChatHistory chatHistory, string content)
    {
        IReadOnlyDictionary<string, object?> metadata = new Dictionary<string, object?>
        {
            ["TokenCount"] = s_tokenizer.CountTokens(content)
        };
        chatHistory.AddMessage(AuthorRole.User, content, metadata: metadata);
    }

    /// <summary>
    /// Add a assistant message to the chat history
    /// </summary>
    /// <param name="chatHistory">Chat history instance</param>
    /// <param name="content">Message content</param>
    public static void AddAssistantMessageWithTokenCount(this ChatHistory chatHistory, string content)
    {
        IReadOnlyDictionary<string, object?> metadata = new Dictionary<string, object?>
        {
            ["TokenCount"] = s_tokenizer.CountTokens(content)
        };
        chatHistory.AddMessage(AuthorRole.Assistant, content, metadata: metadata);
    }
}
