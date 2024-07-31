// Copyright (c) Microsoft. All rights reserved.
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
    /// <param name="strategy"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public static async Task<ChatHistory> ReducedHistoryAsync(this ChatHistory history, IChatHistoryReducer strategy, CancellationToken cancellationToken)
    {
        IEnumerable<ChatMessageContent>? reducedHistory = await strategy.ReduceAsync(history, cancellationToken).ConfigureAwait(false);

        if (reducedHistory == null)
        {
            return history;
        }

        return [.. reducedHistory];
    }
}
