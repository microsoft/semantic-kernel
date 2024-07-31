// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.History;

/// <summary>
/// %%%
/// </summary>
internal static class ChatHistoryReducerExtensions
{
    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="history"></param>
    /// <param name="startIndex"></param>
    /// <param name="finalIndex"></param>
    /// <returns></returns>
    public static IEnumerable<ChatMessageContent> Extract(this IReadOnlyList<ChatMessageContent> history, int startIndex, int? finalIndex = null)
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
            yield return history[index];
        }
    }

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="history"></param>
    /// <param name="summaryKey"></param>
    /// <returns></returns>
    public static int GetFinalSummaryIndex(this IReadOnlyList<ChatMessageContent> history, string summaryKey)
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
    /// %%%
    /// </summary>
    /// <param name="history"></param>
    /// <param name="reducer"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public static async Task<(bool isReduced, ChatHistory history)> ReduceHistoryAsync(this ChatHistory history, IChatHistoryReducer reducer, CancellationToken cancellationToken)
    {
        IEnumerable<ChatMessageContent>? reducedHistory = await reducer.ReduceAsync(history, cancellationToken).ConfigureAwait(false);

        if (reducedHistory == null)
        {
            return (false, history);
        }

        return (true, [.. reducedHistory]);
    }
}
