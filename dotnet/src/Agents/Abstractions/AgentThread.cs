// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Base abstraction for all Semantic Kernel agent threads.
/// A thread represents a specific conversation with an agent.
/// </summary>
/// <remarks>
/// This class is used to manage the lifecycle of an agent thread.
/// The thread can be not-start, started or ended.
/// </remarks>
public abstract class AgentThread
{
    /// <summary>
    /// Gets the id of the current thread.
    /// </summary>
    public abstract string? Id { get; }

    /// <summary>
    /// Creates the thread and returns the thread id.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The id of the new thread.</returns>
    public abstract Task<string> CreateAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Deletes the current thread.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that completes when the thread has been ended.</returns>
    public abstract Task DeleteAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// This method is called when a new message has been contributed to the chat by any participant.
    /// </summary>
    /// <remarks>
    /// Inheritors can use this method to update their context based on the new message.
    /// </remarks>
    /// <param name="newMessage">The new message.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that completes when the context has been updated.</returns>
    public abstract Task OnNewMessageAsync(ChatMessageContent newMessage, CancellationToken cancellationToken = default);
}
