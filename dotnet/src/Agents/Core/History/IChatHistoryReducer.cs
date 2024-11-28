// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.History;

/// <summary>
/// Defines a contract for a reducing chat history.
/// </summary>
public interface IChatHistoryReducer
{
    /// <summary>
    /// Each reducer shall override equality evaluation so that different reducers
    /// of the same configuration can be evaluated for equivalency.
    /// </summary>
    bool Equals(object? obj);

    /// <summary>
    /// Each reducer shall implement custom hash-code generation so that different reducers
    /// of the same configuration can be evaluated for equivalency.
    /// </summary>
    int GetHashCode();

    /// <summary>
    /// Optionally reduces the chat history.
    /// </summary>
    /// <param name="history">The source history (which may have been previously reduced)</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The reduced history, or 'null' if no reduction has occurred</returns>
    Task<IEnumerable<ChatMessageContent>?> ReduceAsync(IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default);
}
