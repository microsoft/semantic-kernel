// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;

namespace Microsoft.SemanticKernel.ChatCompletion;

/// <summary>
/// Discrete operations used when reducing chat history.
/// </summary>
/// <remarks>
/// Allows for improved testability.
/// </remarks>
internal static class ChatHistoryReducerExtensions
{
    /// <summary>
    /// Extract a range of messages from the source history.
    /// </summary>
    /// <param name="chatHistory">The source history</param>
    /// <param name="startIndex">The index of the first message to extract</param>
    /// <param name="finalIndex">The index of the last message to extract</param>
    /// <param name="systemMessage">An optional system message content to include</param>
    /// <param name="filter">The optional filter to apply to each message</param>
    public static IEnumerable<ChatMessageContent> Extract(
        this IReadOnlyList<ChatMessageContent> chatHistory,
        int startIndex,
        int? finalIndex = null,
        ChatMessageContent? systemMessage = null,
        Func<ChatMessageContent, bool>? filter = null)
    {
        int maxIndex = chatHistory.Count - 1;
        if (startIndex > maxIndex)
        {
            yield break;
        }

        if (systemMessage is not null)
        {
            yield return systemMessage;
        }

        finalIndex ??= maxIndex;

        finalIndex = Math.Min(finalIndex.Value, maxIndex);

        for (int index = startIndex; index <= finalIndex; ++index)
        {
            if (filter?.Invoke(chatHistory[index]) ?? false)
            {
                continue;
            }

            yield return chatHistory[index];
        }
    }

    /// <summary>
    /// Identify the index of the first message that is not a summary message, as indicated by
    /// the presence of the specified metadata key.
    /// </summary>
    /// <param name="chatHistory">The source history</param>
    /// <param name="summaryKey">The metadata key that identifies a summary message.</param>
    public static int LocateSummarizationBoundary(this IReadOnlyList<ChatMessageContent> chatHistory, string summaryKey)
    {
        for (int index = 0; index < chatHistory.Count; ++index)
        {
            ChatMessageContent message = chatHistory[index];

            if (!message.Metadata?.ContainsKey(summaryKey) ?? true)
            {
                return index;
            }
        }

        return chatHistory.Count;
    }

    /// <summary>
    /// Identify the index of the first message at or beyond the specified targetCount that
    /// does not orphan sensitive content.
    /// Specifically: function calls and results shall not be separated since chat-completion requires that
    /// a function-call always be followed by a function-result.
    /// In addition, the first user message (if present) within the threshold window will be included
    /// in order to maintain context with the subsequent assistant responses.
    /// </summary>
    /// <param name="chatHistory">The source history</param>
    /// <param name="targetCount">The desired message count, should reduction occur.</param>
    /// <param name="thresholdCount">
    /// The threshold, beyond targetCount, required to trigger reduction.
    /// History is not reduces it the message count is less than targetCount + thresholdCount.
    /// </param>
    /// <param name="offsetCount">
    /// Optionally ignore an offset from the start of the history.
    /// This is useful when messages have been injected that are not part of the raw dialog
    /// (such as summarization).
    /// </param>
    /// <param name="hasSystemMessage">Indicates whether chat history contains system message.</param>
    /// <returns>An index that identifies the starting point for a reduced history that does not orphan sensitive content.</returns>
    public static int LocateSafeReductionIndex(
        this IReadOnlyList<ChatMessageContent> chatHistory,
        int targetCount,
        int? thresholdCount = null,
        int offsetCount = 0,
        bool hasSystemMessage = false)
    {
        targetCount -= hasSystemMessage ? 1 : 0;

        // Compute the index of the truncation threshold
        int thresholdIndex = chatHistory.Count - (thresholdCount ?? 0) - targetCount;

        if (thresholdIndex <= offsetCount)
        {
            // History is too short to truncate
            return -1;
        }

        // Compute the index of truncation target
        int messageIndex = chatHistory.Count - targetCount;

        // Skip function related content
        while (messageIndex >= 0)
        {
            if (!chatHistory[messageIndex].Items.Any(i => i is FunctionCallContent or FunctionResultContent))
            {
                break;
            }

            --messageIndex;
        }

        // Capture the earliest non-function related message
        int targetIndex = messageIndex;

        // Scan for user message within truncation range to maximize chat cohesion
        while (messageIndex >= thresholdIndex)
        {
            // A user message provides a superb truncation point
            if (chatHistory[messageIndex].Role == AuthorRole.User)
            {
                return messageIndex;
            }

            --messageIndex;
        }

        // No user message found, fallback to the earliest non-function related message
        return targetIndex;
    }
}
