// Copyright (c) Microsoft. All rights reserved.

using Microsoft.ML.Tokenizers;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace ChatCompletion;

/// <summary>
/// Extension methods for <see cref="ChatHistory"/>."/>
/// </summary>
internal static class ChatHistoryExtensions
{
    private static readonly Tokenizer s_tokenizer = TiktokenTokenizer.CreateForModel("gpt-4");

    /// <summary>
    /// Returns the system prompt from the chat history.
    /// </summary>
    /// <remarks>
    /// For simplicity only a single system message is supported in these examples.
    /// </remarks>
    internal static ChatMessageContent? GetSystemMessage(this IReadOnlyList<ChatMessageContent> chatHistory)
    {
        return chatHistory.FirstOrDefault(m => m.Role == AuthorRole.System);
    }

    /// <summary>
    /// Extract a range of messages from the provided <see cref="ChatHistory"/>.
    /// </summary>
    /// <param name="chatHistory">The source history</param>
    /// <param name="startIndex">The index of the first messageContent to extract</param>
    /// <param name="endIndex">The index of the first messageContent to extract, if null extract up to the end of the chat history</param>
    /// <param name="systemMessage">An optional system messageContent to include</param>
    /// <param name="summaryMessage">An optional summary messageContent to include</param>
    /// <param name="messageFilter">An optional message filter</param>
    public static IEnumerable<ChatMessageContent> Extract(
        this IReadOnlyList<ChatMessageContent> chatHistory,
        int startIndex,
        int? endIndex = null,
        ChatMessageContent? systemMessage = null,
        ChatMessageContent? summaryMessage = null,
        Func<ChatMessageContent, bool>? messageFilter = null)
    {
        endIndex ??= chatHistory.Count - 1;
        if (startIndex > endIndex)
        {
            yield break;
        }

        if (systemMessage is not null)
        {
            yield return systemMessage;
        }

        if (summaryMessage is not null)
        {
            yield return summaryMessage;
        }

        for (int index = startIndex; index <= endIndex; ++index)
        {
            var messageContent = chatHistory[index];

            if (messageFilter?.Invoke(messageContent) ?? false)
            {
                continue;
            }

            yield return messageContent;
        }
    }

    /// <summary>
    /// Compute the index truncation where truncation should begin using the current truncation threshold.
    /// </summary>
    /// <param name="chatHistory">The source history.</param>
    /// <param name="truncatedSize">Truncated size.</param>
    /// <param name="truncationThreshold">Truncation threshold.</param>
    /// <param name="hasSystemMessage">Flag indicating whether or not the chat history contains a system messageContent</param>
    public static int ComputeTruncationIndex(this IReadOnlyList<ChatMessageContent> chatHistory, int truncatedSize, int truncationThreshold, bool hasSystemMessage)
    {
        if (chatHistory.Count <= truncationThreshold)
        {
            return -1;
        }

        // Compute the index of truncation target
        var truncationIndex = chatHistory.Count - (truncatedSize - (hasSystemMessage ? 1 : 0));

        // Skip function related content
        while (truncationIndex < chatHistory.Count)
        {
            if (chatHistory[truncationIndex].Items.Any(i => i is FunctionCallContent || i is FunctionResultContent))
            {
                truncationIndex++;
            }
            else
            {
                break;
            }
        }

        return truncationIndex;
    }

    /// <summary>
    /// Add a system messageContent to the chat history
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
    /// Add a user messageContent to the chat history
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
    /// Add a assistant messageContent to the chat history
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
