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
/// A container class for <see cref="AIContextBehavior"/> objects that manages their lifecycle and interactions.
/// </summary>
[Experimental("SKEXP0130")]
public sealed class AIContextBehaviorsManager
{
    private readonly List<AIContextBehavior> _behaviors = new();

    /// <summary>
    /// Gets the list of registered <see cref="AIContextBehavior"/> objects.
    /// </summary>
    public IReadOnlyList<AIContextBehavior> Behaviors => this._behaviors;

    /// <summary>
    /// Initializes a new instance of the <see cref="AIContextBehaviorsManager"/> class with the specified <see cref="AIContextBehavior"/> objects.
    /// </summary>
    /// <param name="aiContextBehaviors">The <see cref="AIContextBehavior"/> objects to add to the manager.</param>
    public AIContextBehaviorsManager(IEnumerable<AIContextBehavior>? aiContextBehaviors = null)
    {
        this._behaviors.AddRange(aiContextBehaviors ?? []);
    }

    /// <summary>
    /// Adds a new <see cref="AIContextBehavior"/> objects.
    /// </summary>
    /// <param name="aiContextBehavior">The <see cref="AIContextBehavior"/> object to register.</param>
    public void Add(AIContextBehavior aiContextBehavior)
    {
        this._behaviors.Add(aiContextBehavior);
    }

    /// <summary>
    /// Adds all <see cref="AIContextBehavior"/> objects registered on the provided dependency injection service provider.
    /// </summary>
    /// <param name="serviceProvider">The dependency injection service provider to read <see cref="AIContextBehavior"/> objects from.</param>
    public void AddFromServiceProvider(IServiceProvider serviceProvider)
    {
        foreach (var behavior in serviceProvider.GetServices<AIContextBehavior>())
        {
            this.Add(behavior);
        }
    }

    /// <summary>
    /// Called when a new thread is created.
    /// </summary>
    /// <param name="threadId">The ID of the new thread.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    public async Task OnThreadCreatedAsync(string? threadId, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(this.Behaviors.Select(x => x.OnThreadCreatedAsync(threadId, cancellationToken)).ToList()).ConfigureAwait(false);
    }

    /// <summary>
    /// Called just before a thread is deleted.
    /// </summary>
    /// <param name="threadId">The id of the thread that will be deleted.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that represents the asynchronous operation.</returns>
    public async Task OnThreadDeleteAsync(string threadId, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(this.Behaviors.Select(x => x.OnThreadDeleteAsync(threadId, cancellationToken)).ToList()).ConfigureAwait(false);
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
        await Task.WhenAll(this.Behaviors.Select(x => x.OnNewMessageAsync(threadId, newMessage, cancellationToken)).ToList()).ConfigureAwait(false);
    }

    /// <summary>
    /// Called just before the Model/Agent/etc. is invoked
    /// </summary>
    /// <param name="newMessages">The most recent messages that the Model/Agent/etc. is being invoked with.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task that represents the asynchronous operation, containing the combined context from all <see cref="AIContextBehavior"/> objects.</returns>
    public async Task<AIContextPart> OnModelInvokeAsync(ICollection<ChatMessage> newMessages, CancellationToken cancellationToken = default)
    {
        var subContexts = await Task.WhenAll(this.Behaviors.Select(x => x.OnModelInvokeAsync(newMessages, cancellationToken)).ToList()).ConfigureAwait(false);
        subContexts = subContexts.Where(x => x != null).ToArray();

        var combinedContext = new AIContextPart();
        combinedContext.AIFunctions = subContexts.Where(x => x.AIFunctions != null).SelectMany(x => x.AIFunctions).ToArray();
        combinedContext.Instructions = string.Join("\n", subContexts.Where(x => !string.IsNullOrWhiteSpace(x.Instructions)).Select(x => x.Instructions));
        return combinedContext;
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
        await Task.WhenAll(this.Behaviors.Select(x => x.OnSuspendAsync(threadId, cancellationToken))).ConfigureAwait(false);
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
        await Task.WhenAll(this.Behaviors.Select(x => x.OnResumeAsync(threadId, cancellationToken))).ConfigureAwait(false);
    }
}
