// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Functions;

/// <summary>
/// Represents a contextual function provider that performs RAG (Retrieval-Augmented Generation) on the provided functions to identify
/// the most relevant functions for the current context. The provider vectorizes the provided function names and descriptions
/// and stores them in the specified vector store, allowing for a vector search to find the most relevant
/// functions for a given context and provide the functions to the AI model/agent.
/// </summary>
/// <remarks>
/// <list type="bullet">
/// <item>
/// The provider is designed to work with in-memory vector stores. Using other vector stores
/// will require the data synchronization and data lifetime management to be done by the caller.
/// </item>
/// <item>
/// The in-memory vector store is supposed to be created per provider and not shared between providers
/// unless each provider uses a different collection name. Not following this may lead to a situation
/// where one provider identifies a function belonging to another provider as relevant and, as a result,
/// an attempt to access it by the first provider will fail because the function is not registered with it.
/// </item>
/// <item>
/// The provider uses function name as a key for the records and as such the specified vector store
/// should support record keys of string type.
/// </item>
/// </list>
/// </remarks>
[Experimental("SKEXP0130")]
public sealed class ContextualFunctionProvider : AIContextProvider
{
    private readonly FunctionStore _functionStore;
    private readonly ConcurrentQueue<ChatMessage> _recentMessages = new();
    private readonly int _contextSize;
    private readonly ContextualFunctionProviderOptions _options;
    private bool _areFunctionsVectorized = false;

    /// <summary>
    /// Initializes a new instance of the <see cref="ContextualFunctionProvider"/> class.
    /// </summary>
    /// <param name="vectorStore">An instance of a vector store.</param>
    /// <param name="vectorDimensions">The number of dimensions to use for the memory embeddings.</param>
    /// <param name="functions">The functions to vectorize and store for searching related functions.</param>
    /// <param name="maxNumberOfFunctions">The maximum number of relevant functions to retrieve from the vector store.</param>
    /// <param name="contextSize">
    /// The number of messages the provider uses to form a context. The provider collects new messages, up to this number, and uses them to build a context.
    /// While adding new messages, the provider will remove the oldest messages to keep the context size within the specified limit.
    /// </param>
    /// <param name="options">The provider options.</param>
    /// <param name="collectionName">The collection name to use for storing and retrieving functions.</param>
    public ContextualFunctionProvider(
        VectorStore vectorStore,
        int vectorDimensions,
        IEnumerable<AIFunction> functions,
        int maxNumberOfFunctions,
        int contextSize = 1,
        ContextualFunctionProviderOptions? options = null,
        string collectionName = "functions")
    {
        Verify.NotNull(vectorStore);
        Verify.True(vectorDimensions > 0, "Vector dimensions must be greater than 0");
        Verify.NotNull(functions);
        Verify.True(maxNumberOfFunctions > 0, "Max number of functions must be greater than 0");
        Verify.True(contextSize > 0, "Context size must be greater than 0");
        Verify.NotNullOrWhiteSpace(collectionName);
        this._contextSize = contextSize;
        this._options = options ?? new ContextualFunctionProviderOptions();

        this._functionStore = new FunctionStore(
            vectorStore,
            collectionName,
            vectorDimensions,
            functions,
            maxNumberOfFunctions,
            options: new()
            {
                EmbeddingValueProvider = this._options.EmbeddingValueProvider,
            }
         );
    }

    /// <inheritdoc />
    public override async Task<AIContext> ModelInvokingAsync(ICollection<ChatMessage> newMessages, CancellationToken cancellationToken = default)
    {
        // Vectorize the functions if they are not already vectorized
        if (!this._areFunctionsVectorized)
        {
            await this._functionStore.SaveAsync(cancellationToken).ConfigureAwait(false);

            this._areFunctionsVectorized = true;
        }

        // Build the context from the messages
        var context = await this.BuildContextAsync(cancellationToken).ConfigureAwait(false);

        // Get the function relevant to the context
        var functions = await this._functionStore
                .SearchAsync(context, cancellationToken: cancellationToken)
                .ConfigureAwait(false);

        return new AIContext { AIFunctions = [.. functions] };
    }

    /// <inheritdoc/>
    public override Task MessageAddingAsync(string? conversationId, ChatMessage newMessage, CancellationToken cancellationToken = default)
    {
        // Add the new message to the recent messages queue
        this._recentMessages.Enqueue(newMessage);

        // If there are more than ContextSize messages in the queue, remove the oldest ones
        for (int i = this._contextSize; i < this._recentMessages.Count; i++)
        {
            this._recentMessages.TryDequeue(out _);
        }

        return Task.CompletedTask;
    }

    /// <summary>
    /// Builds the context from chat messages.
    /// </summary>
    /// <param name="messages">The messages to build the context from.</param>
    /// <param name="cancellationToken">The cancellation token to use for cancellation.</param>
    private async Task<string> BuildContextAsync(CancellationToken cancellationToken)
    {
        if (this._options.ContextEmbeddingValueProvider is not null)
        {
            return await this._options.ContextEmbeddingValueProvider.Invoke([.. this._recentMessages], cancellationToken).ConfigureAwait(false);
        }

        return string.Join(
            Environment.NewLine,
            this._recentMessages.
                Where(m => !string.IsNullOrWhiteSpace(m?.Text)).
                Select(m => m.Text));
    }
}
