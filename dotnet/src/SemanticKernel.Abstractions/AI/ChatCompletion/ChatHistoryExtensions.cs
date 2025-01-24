// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading.Tasks;
using System.Threading;
using System.Linq;

namespace Microsoft.SemanticKernel.ChatCompletion;

/// <summary>
/// Extension methods for chat history.
/// </summary>
[Experimental("SKEXP0001")]
public static class ChatHistoryExtensions
{
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

    /// <summary>
    /// Reduce the history using the provided reducer without mutating the source history.
    /// </summary>
    /// <param name="history">The source history</param>
    /// <param name="reducer">The target reducer</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public static async Task<IReadOnlyList<ChatMessageContent>> ReduceAsync(this IReadOnlyList<ChatMessageContent> history, IChatHistoryReducer? reducer, CancellationToken cancellationToken)
    {
        if (reducer != null)
        {
            IEnumerable<ChatMessageContent>? reducedHistory = await reducer.ReduceAsync(history, cancellationToken).ConfigureAwait(false);
            history = reducedHistory?.ToArray() ?? history;
        }

        return history;
    }
}
