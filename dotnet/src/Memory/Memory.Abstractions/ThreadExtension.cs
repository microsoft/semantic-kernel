// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// Base class for all thread extensions.
/// </summary>
public abstract class ThreadExtension
{
    /// <summary>
    /// Called just after a new thread is created.
    /// </summary>
    /// <remarks>
    /// Implementers can use this method to do any operations required at the creation of a new thread.
    /// For exmple, checking long term storage for any data that is relevant to the current session based on the input text.
    /// </remarks>
    /// <param name="threadId">The ID of the new thread.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that completes when the context has been loaded.</returns>
    public virtual Task OnThreadCreatedAsync(string? threadId, CancellationToken cancellationToken = default)
    {
        return Task.CompletedTask;
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
    public virtual Task OnNewMessageAsync(ChatMessageContent newMessage, CancellationToken cancellationToken = default)
    {
        return Task.CompletedTask;
    }

    /// <summary>
    /// Called just before a thread is deleted.
    /// </summary>
    /// <remarks>
    /// Implementers can use this method to do any operations required before a thread is deleted.
    /// For exmple, storing the context to long term storage.
    /// </remarks>
    /// <param name="threadId">The id of the thread that will be deleted.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that completes when the context has been saved.</returns>
    public virtual Task OnThreadDeleteAsync(string threadId, CancellationToken cancellationToken = default)
    {
        return Task.CompletedTask;
    }

    /// <summary>
    /// Called just before the AI is invoked
    /// Implementers can load any additional context required at this time,
    /// but they should also return any context that should be passed to the AI.
    /// </summary>
    /// <param name="newMessages">The most recent messages that the AI is being invoked with.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that completes when the context has been rendered and returned.</returns>
    public abstract Task<string> OnAIInvocationAsync(ICollection<ChatMessageContent> newMessages, CancellationToken cancellationToken = default);

    /// <summary>
    /// Register plugins required by this extension component on the provided <see cref="Kernel"/>.
    /// </summary>
    /// <param name="kernel">The kernel to register the plugins on.</param>
    public virtual void RegisterPlugins(Kernel kernel)
    {
    }
}
