// Copyright (c) Microsoft. All rights reserved.

using System;
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
    public virtual string? Id { get; protected set; }

    /// <summary>
    /// Gets a value indicating whether the thread has been deleted.
    /// </summary>
    public virtual bool IsDeleted { get; protected set; } = false;

    /// <summary>
    /// Creates the thread and returns the thread id.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that completes when the thread has been created.</returns>
    /// <exception cref="InvalidOperationException">The thread has been deleted.</exception>
    protected internal virtual async Task CreateAsync(CancellationToken cancellationToken = default)
    {
        if (this.IsDeleted)
        {
            throw new InvalidOperationException("This thread has been deleted and cannot be recreated.");
        }

        if (this.Id is not null)
        {
            return;
        }

        this.Id = await this.CreateInternalAsync(cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Deletes the current thread.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that completes when the thread has been deleted.</returns>
    /// <exception cref="InvalidOperationException">The thread was never created.</exception>
    public virtual async Task DeleteAsync(CancellationToken cancellationToken = default)
    {
        if (this.IsDeleted)
        {
            return;
        }

        if (this.Id is null)
        {
            throw new InvalidOperationException("This thread cannot be deleted, since it has not been created.");
        }

        await this.DeleteInternalAsync(cancellationToken).ConfigureAwait(false);

        this.IsDeleted = true;
    }

    /// <summary>
    /// This method is called when a new message has been contributed to the chat by any participant.
    /// </summary>
    /// <remarks>
    /// Inheritors can use this method to update their context based on the new message.
    /// </remarks>
    /// <param name="newMessage">The new message.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that completes when the context has been updated.</returns>
    /// <exception cref="InvalidOperationException">The thread has been deleted.</exception>
    internal virtual async Task OnNewMessageAsync(ChatMessageContent newMessage, CancellationToken cancellationToken = default)
    {
        if (this.IsDeleted)
        {
            throw new InvalidOperationException("This thread has been deleted and cannot be used anymore.");
        }

        if (this.Id is null)
        {
            await this.CreateAsync(cancellationToken).ConfigureAwait(false);
        }

        await this.OnNewMessageInternalAsync(newMessage, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Creates the thread and returns the thread id.
    /// Checks have already been completed in the <see cref="CreateAsync"/> method to ensure that the thread can be created.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The id of the thread that was created if one is available.</returns>
    protected abstract Task<string?> CreateInternalAsync(CancellationToken cancellationToken);

    /// <summary>
    /// Deletes the current thread.
    /// Checks have already been completed in the <see cref="DeleteAsync"/> method to ensure that the thread can be deleted.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that completes when the thread has been deleted.</returns>
    protected abstract Task DeleteInternalAsync(CancellationToken cancellationToken);

    /// <summary>
    /// This method is called when a new message has been contributed to the chat by any participant.
    /// Checks have already been completed in the <see cref="OnNewMessageAsync"/> method to ensure that the thread can be updated.
    /// </summary>
    /// <param name="newMessage">The new message.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that completes when the context has been updated.</returns>
    protected abstract Task OnNewMessageInternalAsync(ChatMessageContent newMessage, CancellationToken cancellationToken = default);
}
