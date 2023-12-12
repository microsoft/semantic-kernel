// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// Represents a thread that contains messages.
/// </summary>
public interface IChatThread
{
    /// <summary>
    /// The thread identifier (which can be referenced in API endpoints).
    /// </summary>
    string Id { get; }

    /// <summary>
    /// Add a textual user message to the thread.
    /// </summary>
    /// <param name="message">The user message</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns></returns>
    Task<IChatMessage> AddUserMessageAsync(string message, CancellationToken cancellationToken = default);

    /// <summary>
    /// Advance the thread with the specified assistant.
    /// </summary>
    /// <param name="assistant">An assistant instance.</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>The resulting assistant message(s)</returns>
    IAsyncEnumerable<IChatMessage> InvokeAsync(IAssistant assistant, CancellationToken cancellationToken = default);

    /// <summary>
    /// Advance the thread with the specified assistant.
    /// </summary>
    /// <param name="assistant">An assistant instance.</param>
    /// <param name="userMessage">The user message</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>The resulting assistant message(s)</returns>
    IAsyncEnumerable<IChatMessage> InvokeAsync(IAssistant assistant, string userMessage, CancellationToken cancellationToken = default);

    /// <summary>
    /// Delete current thread.  Terminal state - Unable to perform any
    /// subsequent actions.
    /// </summary>
    /// <param name="cancellationToken">A cancellation token</param>
    Task DeleteAsync(CancellationToken cancellationToken = default);
}
