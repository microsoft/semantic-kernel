// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.History;

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
    /// <param name="history">The source history</param>
    /// <param name="startIndex">The index of the first message to extract</param>
    /// <param name="finalIndex">The index of the last message to extract</param>
    /// <param name="filter">The optional filter to apply to each message</param>
    public static IEnumerable<ChatMessageContent> Extract(this IReadOnlyList<ChatMessageContent> history, int startIndex, int? finalIndex = null, Func<ChatMessageContent, bool>? filter = null)
    {
        int maxIndex = history.Count - 1;
        if (startIndex > maxIndex)
        {
            yield break;
        }

        finalIndex ??= maxIndex;

        finalIndex = Math.Min(finalIndex.Value, maxIndex);

        for (int index = startIndex; index <= finalIndex; ++index)
        {
            if (filter?.Invoke(history[index]) ?? false)
            {
                continue;
            }

            yield return history[index];
        }
    }

    /// <summary>
    /// Identify the index of the first message that is not a summary message, as indicated by
    /// the presence of the specified metadata key.
    /// </summary>
    /// <param name="history">The source history</param>
    /// <param name="summaryKey">The metadata key that identifies a summary message.</param>
    public static int LocateSummarizationBoundary(this IReadOnlyList<ChatMessageContent> history, string summaryKey)
    {
        for (int index = 0; index < history.Count; ++index)
        {
            ChatMessageContent message = history[index];

            if (!message.Metadata?.ContainsKey(summaryKey) ?? true)
            {
                return index;
            }
        }

        return history.Count;
    }

    /// <summary>
    /// Identify the index of the first message at or beyond the specified targetCount that
    /// does not orphan sensitive content.
    /// Specifically: function calls and results shall not be separated since chat-completion requires that
    /// a function-call always be followed by a function-result.
    /// In addition, the first user message (if present) within the threshold window will be included
    /// in order to maintain context with the subsequent assistant responses.
    /// </summary>
    /// <param name="history">The source history</param>
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
    /// <returns>An index that identifies the starting point for a reduced history that does not orphan sensitive content.</returns>
    public static int LocateSafeReductionIndex(this IReadOnlyList<ChatMessageContent> history, int targetCount, int? thresholdCount = null, int offsetCount = 0)
    {
        // Compute the index of the truncation threshold
        int thresholdIndex = history.Count - (thresholdCount ?? 0) - targetCount;

        if (thresholdIndex <= offsetCount)
        {
            // History is too short to truncate
            return 0;
        }

        // Compute the index of truncation target
        int messageIndex = history.Count - targetCount;

        // Skip function related content
        while (messageIndex >= 0)
        {
            if (!history[messageIndex].Items.Any(i => i is FunctionCallContent || i is FunctionResultContent))
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
            if (history[messageIndex].Role == AuthorRole.User)
            {
                return messageIndex;
            }

            --messageIndex;
        }

        // No user message found, fallback to the earliest non-function related message
        return targetIndex;
    }

    /// <summary>
    /// Process history reduction and mutate the provided history.
    /// </summary>
    /// <param name="history">The source history</param>
    /// <param name="reducer">The target reducer</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>True if reduction has occurred.</returns>
    /// <remarks>
    /// Using the existing <see cref="ChatHistory"/> for a reduction in collection size eliminates the need
    /// for re-allocation (of memory).
    /// </remarks>
    public static async Task<bool> ReduceAsync(this ChatHistory history, IChatHistoryReducer? reducer, CancellationToken cancellationToken)
    {
        if (reducer == null)
        {
            return false;
        }

        IEnumerable<ChatMessageContent>? reducedHistory = await reducer.ReduceAsync(history, cancellationToken).ConfigureAwait(false);

        if (reducedHistory == null)
        {
            return false;
        }

        // Mutate the history in place
        ChatMessageContent[] reduced = reducedHistory.ToArray();
        history.Clear();
        history.AddRange(reduced);

        return true;
    }
}
