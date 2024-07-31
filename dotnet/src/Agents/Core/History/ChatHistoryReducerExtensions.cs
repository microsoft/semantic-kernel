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
