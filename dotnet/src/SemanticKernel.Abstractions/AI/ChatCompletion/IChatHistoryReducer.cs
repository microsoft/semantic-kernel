// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.ChatCompletion;

/// <summary>
/// Interface for reducing the chat history.
/// </summary>
public interface IChatHistoryReducer
{
    /// <summary>
    /// Reduces the chat history.
    /// </summary>
    /// <param name="chatHistory">Chat history to be reduced.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The reduced history or <see langword="null"/> if no reduction has occurred.</returns>
    Task<IEnumerable<ChatMessageContent>?> ReduceAsync(IReadOnlyList<ChatMessageContent> chatHistory, CancellationToken cancellationToken = default);
}
