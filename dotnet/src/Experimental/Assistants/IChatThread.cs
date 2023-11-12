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
    /// The messages associated with the thread.
    /// </summary>
    IReadOnlyList<ChatMessage> Messages { get; }

    /// <summary>
    /// Add a textual user message to the thread.
    /// </summary>
    /// <param name="message">The user message</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns></returns>
    Task<ChatMessage> AddUserMessageAsync(string message, CancellationToken cancellationToken = default);

    /// <summary>
    /// Advance the thread with the specified assistant.
    /// </summary>
    /// <param name="assistantId">The specified assisant id</param>
    /// <param name="instructions">Optional instruction override</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>The resulting assisant message(s)</returns>
    Task<IEnumerable<ChatMessage>> InvokeAsync(string assistantId, string? instructions, CancellationToken cancellationToken = default);
}
