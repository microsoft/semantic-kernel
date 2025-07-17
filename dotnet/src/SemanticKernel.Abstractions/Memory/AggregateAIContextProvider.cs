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
/// An <see cref="AIContextProvider"/> that contains context providers inside, delegates events to them, and aggregates responses from those events before returning.
/// </summary>
[Experimental("SKEXP0130")]
public sealed class AggregateAIContextProvider : AIContextProvider
{
    private readonly List<AIContextProvider> _providers = new();

    /// <summary>
    /// Gets the list of registered <see cref="AIContextProvider"/> objects.
    /// </summary>
    public IReadOnlyList<AIContextProvider> Providers => this._providers;

    /// <summary>
    /// Initializes a new instance of the <see cref="AggregateAIContextProvider"/> class with the specified <see cref="AIContextProvider"/> objects.
    /// </summary>
    /// <param name="aiContextProviders">The <see cref="AIContextProvider"/> objects to add to the manager.</param>
    public AggregateAIContextProvider(IEnumerable<AIContextProvider>? aiContextProviders = null)
    {
        this._providers.AddRange(aiContextProviders ?? []);
    }

    /// <summary>
    /// Adds a new <see cref="AIContextProvider"/> objects.
    /// </summary>
    /// <param name="aiContextProvider">The <see cref="AIContextProvider"/> object to register.</param>
    public void Add(AIContextProvider aiContextProvider)
    {
        this._providers.Add(aiContextProvider);
    }

    /// <summary>
    /// Adds all <see cref="AIContextProvider"/> objects registered on the provided dependency injection service provider.
    /// </summary>
    /// <param name="serviceProvider">The dependency injection service provider to read <see cref="AIContextProvider"/> objects from.</param>
    public void AddFromServiceProvider(IServiceProvider serviceProvider)
    {
        foreach (var aiContextProvider in serviceProvider.GetServices<AIContextProvider>())
        {
            this.Add(aiContextProvider);
        }
    }

    /// <inheritdoc />
    public override async Task ConversationCreatedAsync(string? conversationId, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(this.Providers.Select(x => x.ConversationCreatedAsync(conversationId, cancellationToken)).ToList()).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public override async Task ConversationDeletingAsync(string? conversationId, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(this.Providers.Select(x => x.ConversationDeletingAsync(conversationId, cancellationToken)).ToList()).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public override async Task MessageAddingAsync(string? conversationId, ChatMessage newMessage, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(this.Providers.Select(x => x.MessageAddingAsync(conversationId, newMessage, cancellationToken)).ToList()).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public override async Task<AIContext> ModelInvokingAsync(ICollection<ChatMessage> newMessages, CancellationToken cancellationToken = default)
    {
        var subContexts = await Task.WhenAll(this.Providers.Select(x => x.ModelInvokingAsync(newMessages, cancellationToken)).ToList()).ConfigureAwait(false);
        subContexts = subContexts.Where(x => x != null).ToArray();

        var combinedContext = new AIContext();
        combinedContext.AIFunctions = subContexts.Where(x => x.AIFunctions != null).SelectMany(x => x.AIFunctions).ToList();
        combinedContext.Instructions = string.Join("\n", subContexts.Where(x => !string.IsNullOrWhiteSpace(x.Instructions)).Select(x => x.Instructions));
        return combinedContext;
    }

    /// <inheritdoc />
    public override async Task SuspendingAsync(string? conversationId, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(this.Providers.Select(x => x.SuspendingAsync(conversationId, cancellationToken))).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public override async Task ResumingAsync(string? conversationId, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(this.Providers.Select(x => x.ResumingAsync(conversationId, cancellationToken))).ConfigureAwait(false);
    }
}
