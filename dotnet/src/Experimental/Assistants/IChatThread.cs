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
    Task<IEnumerable<IChatMessage>> InvokeAsync(IAssistant assistant, CancellationToken cancellationToken = default);

    /// <summary>
    /// Delete existing thread.
    /// </summary>
    /// <param name="cancellationToken">A cancellation token</param>
    Task DeleteThreadAsync(CancellationToken cancellationToken = default);
}
