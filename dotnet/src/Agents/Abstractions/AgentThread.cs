// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
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
    /// Gets or sets the container for <see cref="AIContextProvider"/> objects that manages their lifecycle and interactions.
    /// </summary>
    [Experimental("SKEXP0110")]
    public virtual AggregateAIContextProvider AIContextProviders { get; init; } = new AggregateAIContextProvider();

    /// <summary>
    /// Called when the current conversion is temporarily suspended and any state should be saved.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An async task.</returns>
    /// <remarks>
    /// In a service that hosts an agent, that is invoked via calls to the service, this might be at the end of each service call.
    /// In a client application, this might be when the user closes the chat window or the application.
    /// </remarks>
    [Experimental("SKEXP0110")]
    public virtual Task OnSuspendAsync(CancellationToken cancellationToken = default)
    {
        return this.AIContextProviders.SuspendingAsync(this.Id, cancellationToken);
    }

    /// <summary>
    /// Called when the current conversion is resumed and any state should be restored.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An async task.</returns>
    /// <remarks>
    /// In a service that hosts an agent, that is invoked via calls to the service, this might be at the start of each service call where a previous conversation is being continued.
    /// In a client application, this might be when the user re-opens the chat window to resume a conversation after having previously closed it.
    /// </remarks>
    [Experimental("SKEXP0110")]
    public virtual Task OnResumeAsync(CancellationToken cancellationToken = default)
    {
        if (this.IsDeleted)
        {
            throw new InvalidOperationException("This thread has been deleted and cannot be used anymore.");
        }

        if (this.Id is null)
        {
            throw new InvalidOperationException("This thread cannot be resumed, since it has not been created.");
        }

        return this.AIContextProviders.ResumingAsync(this.Id, cancellationToken);
    }

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

        this.Id = await this.CreateInternalAsync(cancellationToken).ConfigureAwait(false);

#pragma warning disable SKEXP0110 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
        await this.AIContextProviders.ConversationCreatedAsync(this.Id, cancellationToken).ConfigureAwait(false);
#pragma warning restore SKEXP0110 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
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

#pragma warning disable SKEXP0110 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
        await this.AIContextProviders.ConversationDeletingAsync(this.Id, cancellationToken).ConfigureAwait(false);
#pragma warning restore SKEXP0110 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

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

#pragma warning disable SKEXP0110 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
        await this.AIContextProviders.MessageAddingAsync(this.Id, newMessage, cancellationToken).ConfigureAwait(false);
#pragma warning restore SKEXP0110 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

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
