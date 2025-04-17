// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Base class for all conversation state extensions.
/// </summary>
/// <remarks>
/// A conversation state extension is a component that can be used to store additional state related
/// to a conversation, listen to changes in the conversation state, and provide additional context to
/// the AI model in use just before invocation.
/// </remarks>
[Experimental("SKEXP0001")]
public abstract class ConversationStateExtension
{
    /// <summary>
    /// Gets the list of AI functions that this extension component exposes
    /// and which should be used by the consuming AI when using this component.
    /// </summary>
    public virtual IReadOnlyCollection<AIFunction> AIFunctions => Array.Empty<AIFunction>();

    /// <summary>
    /// Called just after a new thread is created.
    /// </summary>
    /// <remarks>
    /// Implementers can use this method to do any operations required at the creation of a new thread.
    /// For example, checking long term storage for any data that is relevant to the current session based on the input text.
    /// </remarks>
    /// <param name="threadId">The ID of the new thread, if the thread has an ID.</param>
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
    public virtual Task OnNewMessageAsync(ChatMessage newMessage, CancellationToken cancellationToken = default)
    {
        return Task.CompletedTask;
    }

    /// <summary>
    /// Called just before a thread is deleted.
    /// </summary>
    /// <remarks>
    /// Implementers can use this method to do any operations required before a thread is deleted.
    /// For example, storing the context to long term storage.
    /// </remarks>
    /// <param name="threadId">The ID of the thread that will be deleted, if the thread has an ID.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that completes when the context has been saved.</returns>
    public virtual Task OnThreadDeleteAsync(string? threadId, CancellationToken cancellationToken = default)
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
    public abstract Task<string> OnAIInvocationAsync(ICollection<ChatMessage> newMessages, CancellationToken cancellationToken = default);

    /// <summary>
    /// Called when the current conversion is temporarily suspended and any state should be saved.
    /// </summary>
    /// <param name="threadId">The ID of the current thread, if the thread has an ID.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An async task.</returns>
    /// <remarks>
    /// In a service that hosts an agent, that is invoked via calls to the service, this might be at the end of each service call.
    /// In a client application, this might be when the user closes the chat window or the application.
    /// </remarks>
    public virtual Task OnSuspendAsync(string? threadId, CancellationToken cancellationToken = default)
    {
        return Task.CompletedTask;
    }

    /// <summary>
    /// Called when the current conversion is resumed and any state should be restored.
    /// </summary>
    /// <param name="threadId">The ID of the current thread, if the thread has an ID.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An async task.</returns>
    /// <remarks>
    /// In a service that hosts an agent, that is invoked via calls to the service, this might be at the start of each service call where a previous conversation is being continued.
    /// In a client application, this might be when the user re-opens the chat window to resume a conversation after having previously closed it.
    /// </remarks>
    public virtual Task OnResumeAsync(string? threadId, CancellationToken cancellationToken = default)
    {
        return Task.CompletedTask;
    }
}
