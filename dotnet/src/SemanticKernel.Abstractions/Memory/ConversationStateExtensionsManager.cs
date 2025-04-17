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
/// A container class for <see cref="ConversationStateExtension"/> objects that manages their lifecycle and interactions.
/// </summary>
[Experimental("SKEXP0001")]
public class ConversationStateExtensionsManager
{
    private readonly List<ConversationStateExtension> _conversationStateExtensions = new();

    private List<AIFunction>? _currentAIFunctions = null;

    /// <summary>
    /// Gets the list of registered conversation state extensions.
    /// </summary>
    public virtual IReadOnlyList<ConversationStateExtension> ConversationStateExtensions => this._conversationStateExtensions;

    /// <summary>
    /// Initializes a new instance of the <see cref="ConversationStateExtensionsManager"/> class.
    /// </summary>
    public ConversationStateExtensionsManager()
    {
    }

    /// <summary>
    /// Gets the list of AI functions that all contained extension component expose
    /// and which should be used by the consuming AI when using these components.
    /// </summary>
    public virtual IReadOnlyCollection<AIFunction> AIFunctions
    {
        get
        {
            if (this._currentAIFunctions == null)
            {
                this._currentAIFunctions = this.ConversationStateExtensions.SelectMany(ConversationStateExtensions => ConversationStateExtensions.AIFunctions).ToList();
            }

            return this._currentAIFunctions;
        }
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ConversationStateExtensionsManager"/> class with the specified conversation state extensions.
    /// </summary>
    /// <param name="conversationtStateExtensions">The conversation state extensions to add to the manager.</param>
    public ConversationStateExtensionsManager(IEnumerable<ConversationStateExtension> conversationtStateExtensions)
    {
        this._conversationStateExtensions.AddRange(conversationtStateExtensions);
    }

    /// <summary>
    /// Registers a new conversation state extension.
    /// </summary>
    /// <param name="conversationtStateExtension">The conversation state extension to register.</param>
    public virtual void RegisterThreadExtension(ConversationStateExtension conversationtStateExtension)
    {
        this._conversationStateExtensions.Add(conversationtStateExtension);
        this._currentAIFunctions = null;
    }

    /// <summary>
    /// Registers all conversation state extensions registered on the provided dependency injection service provider.
    /// </summary>
    /// <param name="serviceProvider">The dependency injection service provider to read conversation state extensions from.</param>
    public virtual void RegisterThreadExtensionsFromContainer(IServiceProvider serviceProvider)
    {
        foreach (var extension in serviceProvider.GetServices<ConversationStateExtension>())
        {
            this.RegisterThreadExtension(extension);
        }
        this._currentAIFunctions = null;
    }

    /// <summary>
    /// Called when a new thread is created.
    /// </summary>
    /// <param name="threadId">The ID of the new thread.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    public virtual async Task OnThreadCreatedAsync(string? threadId, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(this.ConversationStateExtensions.Select(x => x.OnThreadCreatedAsync(threadId, cancellationToken)).ToList()).ConfigureAwait(false);
    }

    /// <summary>
    /// Called just before a thread is deleted.
    /// </summary>
    /// <param name="threadId">The id of the thread that will be deleted.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    public virtual async Task OnThreadDeleteAsync(string threadId, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(this.ConversationStateExtensions.Select(x => x.OnThreadDeleteAsync(threadId, cancellationToken)).ToList()).ConfigureAwait(false);
    }

    /// <summary>
    /// This method is called when a new message has been contributed to the chat by any participant.
    /// </summary>
    /// <param name="newMessage">The new message.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    public virtual async Task OnNewMessageAsync(ChatMessage newMessage, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(this.ConversationStateExtensions.Select(x => x.OnNewMessageAsync(newMessage, cancellationToken)).ToList()).ConfigureAwait(false);
    }

    /// <summary>
    /// Called just before the AI is invoked
    /// </summary>
    /// <param name="newMessages">The most recent messages that the AI is being invoked with.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that represents the asynchronous operation, containing the combined context from all conversation state extensions.</returns>
    public virtual async Task<string> OnAIInvocationAsync(ICollection<ChatMessage> newMessages, CancellationToken cancellationToken = default)
    {
        var subContexts = await Task.WhenAll(this.ConversationStateExtensions.Select(x => x.OnAIInvocationAsync(newMessages, cancellationToken)).ToList()).ConfigureAwait(false);
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
    public virtual async Task OnSuspendAsync(string? threadId, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(this.ConversationStateExtensions.Select(x => x.OnSuspendAsync(threadId, cancellationToken)).ToList()).ConfigureAwait(false);
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
    public virtual async Task OnResumeAsync(string? threadId, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(this.ConversationStateExtensions.Select(x => x.OnResumeAsync(threadId, cancellationToken)).ToList()).ConfigureAwait(false);
    }
}
