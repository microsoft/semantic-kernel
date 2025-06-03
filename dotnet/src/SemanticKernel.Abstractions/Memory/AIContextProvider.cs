// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Base class for all AI context providers.
/// </summary>
/// <remarks>
/// An AI context provider is a component that can be used to enhance the AI's context management.
/// It can listen to changes in the conversation, provide additional context to
/// the AI model just before invocation and supply additional tools for function invocation.
/// </remarks>
[Experimental("SKEXP0130")]
public abstract class AIContextProvider
{
    /// <summary>
    /// Called just after a new conversation/thread is created.
    /// </summary>
    /// <remarks>
    /// Implementers can use this method to do any operations required at the creation of a new conversation/thread.
    /// For example, checking long term storage for any data that is relevant to the current session based on the input text.
    /// </remarks>
    /// <param name="conversationId">The ID of the new conversation/thread, if the conversation/thread has an ID.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that completes when the context has been loaded.</returns>
    public virtual Task ConversationCreatedAsync(string? conversationId, CancellationToken cancellationToken = default)
    {
        return Task.CompletedTask;
    }

    /// <summary>
    /// Called just before a message is added to the chat by any participant.
    /// </summary>
    /// <remarks>
    /// Inheritors can use this method to update their context based on the new message.
    /// </remarks>
    /// <param name="conversationId">The ID of the conversation/thread for the new message, if the conversation/thread has an ID.</param>
    /// <param name="newMessage">The new message.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that completes when the context has been updated.</returns>
    public virtual Task MessageAddingAsync(string? conversationId, ChatMessage newMessage, CancellationToken cancellationToken = default)
    {
        return Task.CompletedTask;
    }

    /// <summary>
    /// Called just before a conversation/thread is deleted.
    /// </summary>
    /// <remarks>
    /// Implementers can use this method to do any operations required before a conversation/thread is deleted.
    /// For example, storing the context to long term storage.
    /// </remarks>
    /// <param name="conversationId">The ID of the conversation/thread that will be deleted, if the conversation/thread has an ID.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that completes when the context has been saved.</returns>
    public virtual Task ConversationDeletingAsync(string? conversationId, CancellationToken cancellationToken = default)
    {
        return Task.CompletedTask;
    }

    /// <summary>
    /// Called just before the Model/Agent/etc. is invoked
    /// Implementers can load any additional context required at this time,
    /// and they should return any context that should be passed to the Model/Agent/etc.
    /// </summary>
    /// <param name="newMessages">The most recent messages that the Model/Agent/etc. is being invoked with.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that completes when the context has been rendered and returned.</returns>
    public abstract Task<AIContext> ModelInvokingAsync(ICollection<ChatMessage> newMessages, CancellationToken cancellationToken = default);

    /// <summary>
    /// Called when the current conversion is temporarily suspended and any state should be saved.
    /// </summary>
    /// <param name="conversationId">The ID of the current conversation/thread, if the conversation/thread has an ID.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An async task.</returns>
    /// <remarks>
    /// In a service that hosts an agent, that is invoked via calls to the service, this might be at the end of each service call.
    /// In a client application, this might be when the user closes the chat window or the application.
    /// </remarks>
    public virtual Task SuspendingAsync(string? conversationId, CancellationToken cancellationToken = default)
    {
        return Task.CompletedTask;
    }

    /// <summary>
    /// Called when the current conversion is resumed and any state should be restored.
    /// </summary>
    /// <param name="conversationId">The ID of the current conversation/thread, if the conversation/thread has an ID.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An async task.</returns>
    /// <remarks>
    /// In a service that hosts an agent, that is invoked via calls to the service, this might be at the start of each service call where a previous conversation is being continued.
    /// In a client application, this might be when the user re-opens the chat window to resume a conversation after having previously closed it.
    /// </remarks>
    public virtual Task ResumingAsync(string? conversationId, CancellationToken cancellationToken = default)
    {
        return Task.CompletedTask;
    }
}
