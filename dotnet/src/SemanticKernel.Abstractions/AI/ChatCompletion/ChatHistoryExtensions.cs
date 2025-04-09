// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.ChatCompletion;

/// <summary>
/// Extension methods for chat history.
/// </summary>
public static class ChatHistoryExtensions
{
    /// <summary>
    /// Process history reduction and mutate the provided history in place.
    /// </summary>
    /// <param name="chatHistory">The source history</param>
    /// <param name="reducer">The target reducer</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>True if reduction has occurred.</returns>
    /// <remarks>
    /// Using the existing <see cref="ChatHistory"/> for a reduction in collection size eliminates the need
    /// for re-allocation (of memory).
    /// </remarks>
    public static async Task<bool> ReduceInPlaceAsync(this ChatHistory chatHistory, IChatHistoryReducer? reducer, CancellationToken cancellationToken)
    {
        if (reducer is null)
        {
            return false;
        }

        IEnumerable<ChatMessageContent>? reducedHistory = await reducer.ReduceAsync(chatHistory, cancellationToken).ConfigureAwait(false);

        if (reducedHistory is null)
        {
            return false;
        }

        // Mutate the history in place
        ChatMessageContent[] reduced = reducedHistory.ToArray();
        chatHistory.Clear();
        chatHistory.AddRange(reduced);

        return true;
    }

    /// <summary>
    /// Returns the reduced history using the provided reducer without mutating the source history.
    /// </summary>
    /// <param name="chatHistory">The source history</param>
    /// <param name="reducer">The target reducer</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public static async Task<IReadOnlyList<ChatMessageContent>> ReduceAsync(this IReadOnlyList<ChatMessageContent> chatHistory, IChatHistoryReducer? reducer, CancellationToken cancellationToken)
    {
        if (reducer is not null)
        {
            IEnumerable<ChatMessageContent>? reducedHistory = await reducer.ReduceAsync(chatHistory, cancellationToken).ConfigureAwait(false);
            chatHistory = reducedHistory?.ToArray() ?? chatHistory;
        }

        return chatHistory;
    }

    /// <summary>
    /// Returns the reduced history using the provided reducer without mutating the source history.
    /// </summary>
    /// <param name="chatHistory">The source history</param>
    /// <param name="reducer">The target reducer</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public static async Task<ChatHistory> ReduceAsync(this ChatHistory chatHistory, IChatHistoryReducer? reducer, CancellationToken cancellationToken)
    {
        if (reducer is not null)
        {
            IEnumerable<ChatMessageContent>? reduced = await reducer.ReduceAsync(chatHistory, cancellationToken).ConfigureAwait(false);
            return new ChatHistory(reduced ?? chatHistory);
        }

        return chatHistory;
    }
}
