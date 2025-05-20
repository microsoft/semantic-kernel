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
/// An <see cref="AIContextBehavior"/> that contains context behaviors inside, delegates events to them, and aggregates responses from those events before returning.
/// </summary>
[Experimental("SKEXP0130")]
public sealed class AggregateAIContextBehavior : AIContextBehavior
{
    private readonly List<AIContextBehavior> _behaviors = new();

    /// <summary>
    /// Gets the list of registered <see cref="AIContextBehavior"/> objects.
    /// </summary>
    public IReadOnlyList<AIContextBehavior> Behaviors => this._behaviors;

    /// <summary>
    /// Initializes a new instance of the <see cref="AggregateAIContextBehavior"/> class with the specified <see cref="AIContextBehavior"/> objects.
    /// </summary>
    /// <param name="aiContextBehaviors">The <see cref="AIContextBehavior"/> objects to add to the manager.</param>
    public AggregateAIContextBehavior(IEnumerable<AIContextBehavior>? aiContextBehaviors = null)
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

    /// <inheritdoc />
    public override async Task ThreadCreatedAsync(string? threadId, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(this.Behaviors.Select(x => x.ThreadCreatedAsync(threadId, cancellationToken)).ToList()).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public override async Task ThreadDeletingAsync(string? threadId, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(this.Behaviors.Select(x => x.ThreadDeletingAsync(threadId, cancellationToken)).ToList()).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public override async Task MessageAddingAsync(string? threadId, ChatMessage newMessage, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(this.Behaviors.Select(x => x.MessageAddingAsync(threadId, newMessage, cancellationToken)).ToList()).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public override async Task<AIContextPart> ModelInvokingAsync(ICollection<ChatMessage> newMessages, CancellationToken cancellationToken = default)
    {
        var subContexts = await Task.WhenAll(this.Behaviors.Select(x => x.ModelInvokingAsync(newMessages, cancellationToken)).ToList()).ConfigureAwait(false);
        subContexts = subContexts.Where(x => x != null).ToArray();

        var combinedContext = new AIContextPart();
        combinedContext.AIFunctions = subContexts.Where(x => x.AIFunctions != null).SelectMany(x => x.AIFunctions).ToList();
        combinedContext.Instructions = string.Join("\n", subContexts.Where(x => !string.IsNullOrWhiteSpace(x.Instructions)).Select(x => x.Instructions));
        return combinedContext;
    }

    /// <inheritdoc />
    public override async Task SuspendingAsync(string? threadId, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(this.Behaviors.Select(x => x.SuspendingAsync(threadId, cancellationToken))).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public override async Task ResumingAsync(string? threadId, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(this.Behaviors.Select(x => x.ResumingAsync(threadId, cancellationToken))).ConfigureAwait(false);
    }
}
