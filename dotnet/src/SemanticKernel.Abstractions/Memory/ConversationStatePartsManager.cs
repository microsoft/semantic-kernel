// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A container class for <see cref="ConversationStatePart"/> objects that manages their lifecycle and interactions.
/// </summary>
[Experimental("SKEXP0130")]
public sealed class ConversationStatePartsManager
{
    private readonly List<ConversationStatePart> _parts = new();

    private List<AIFunction>? _currentAIFunctions = null;

    /// <summary>
    /// Gets the list of registered conversation state parts.
    /// </summary>
    public IReadOnlyList<ConversationStatePart> Parts => this._parts;

    /// <summary>
    /// Initializes a new instance of the <see cref="ConversationStatePartsManager"/> class.
    /// </summary>
    public ConversationStatePartsManager()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ConversationStatePartsManager"/> class with the specified conversation state parts.
    /// </summary>
    /// <param name="conversationtStateExtensions">The conversation state parts to add to the manager.</param>
    public ConversationStatePartsManager(IEnumerable<ConversationStatePart> conversationtStateExtensions)
    {
        this._parts.AddRange(conversationtStateExtensions);
    }

    /// <summary>
    /// Gets the list of AI functions that all contained parts expose
    /// and which should be used by the consuming AI when using these parts.
    /// </summary>
    public IReadOnlyCollection<AIFunction> AIFunctions
    {
        get
        {
            if (this._currentAIFunctions == null)
            {
                this._currentAIFunctions = this.Parts.SelectMany(conversationStateParts => conversationStateParts.AIFunctions).ToList();
            }

            return this._currentAIFunctions;
        }
    }

    /// <summary>
    /// Adds a new conversation state part.
    /// </summary>
    /// <param name="conversationtStatePart">The conversation state part to register.</param>
    public void Add(ConversationStatePart conversationtStatePart)
    {
        this._parts.Add(conversationtStatePart);
        this._currentAIFunctions = null;
    }

    /// <summary>
    /// Adds all conversation state parts registered on the provided dependency injection service provider.
    /// </summary>
    /// <param name="serviceProvider">The dependency injection service provider to read conversation state parts from.</param>
    public void AddFromServiceProvider(IServiceProvider serviceProvider)
    {
        foreach (var part in serviceProvider.GetServices<ConversationStatePart>())
        {
            this.Add(part);
        }
        this._currentAIFunctions = null;
    }

    /// <summary>
    /// Called when a new thread is created.
    /// </summary>
    /// <param name="threadId">The ID of the new thread.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    public async Task OnThreadCreatedAsync(string? threadId, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(this.Parts.Select(x => x.OnThreadCreatedAsync(threadId, cancellationToken)).ToList()).ConfigureAwait(false);
    }

    /// <summary>
    /// Called just before a thread is deleted.
    /// </summary>
    /// <param name="threadId">The id of the thread that will be deleted.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    public async Task OnThreadDeleteAsync(string threadId, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(this.Parts.Select(x => x.OnThreadDeleteAsync(threadId, cancellationToken)).ToList()).ConfigureAwait(false);
    }

    /// <summary>
    /// This method is called when a new message has been contributed to the chat by any participant.
    /// </summary>
    /// <param name="threadId">The ID of the thread for the new message, if the thread has an ID.</param>
    /// <param name="newMessage">The new message.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    public async Task OnNewMessageAsync(string? threadId, ChatMessage newMessage, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(this.Parts.Select(x => x.OnNewMessageAsync(threadId, newMessage, cancellationToken)).ToList()).ConfigureAwait(false);
    }

    /// <summary>
    /// Called just before the Model/Agent/etc. is invoked
    /// </summary>
    /// <param name="newMessages">The most recent messages that the Model/Agent/etc. is being invoked with.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that represents the asynchronous operation, containing the combined context from all conversation state parts.</returns>
    public async Task<string> OnModelInvokeAsync(ICollection<ChatMessage> newMessages, CancellationToken cancellationToken = default)
    {
        var subContexts = await Task.WhenAll(this.Parts.Select(x => x.OnModelInvokeAsync(newMessages, cancellationToken)).ToList()).ConfigureAwait(false);
        return string.Join("\n", subContexts);
    }

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
    public async Task OnSuspendAsync(string? threadId, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(this.Parts.Select(x => x.OnSuspendAsync(threadId, cancellationToken)).ToList()).ConfigureAwait(false);
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
    public async Task OnResumeAsync(string? threadId, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(this.Parts.Select(x => x.OnResumeAsync(threadId, cancellationToken)).ToList()).ConfigureAwait(false);
    }
}
