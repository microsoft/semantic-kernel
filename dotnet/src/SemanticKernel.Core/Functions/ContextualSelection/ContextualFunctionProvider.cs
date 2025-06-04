// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
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
    // Determines how many recent messages, in addition to the configured number of recent messages for context, should be kept in the queue.
    // This ensures that the recent messages (messages from previous invocations) are not pushed out of the queue by
    // the new messages enqueued during the current invocation.
    private const int RecentMessagesBufferSize = 20;
    private readonly FunctionStore _functionStore;
    private readonly ConcurrentQueue<ChatMessage> _recentMessages = [];
    private readonly ContextualFunctionProviderOptions _options;
    private bool _areFunctionsVectorized = false;

    /// <summary>
    /// Initializes a new instance of the <see cref="ContextualFunctionProvider"/> class.
    /// </summary>
    /// <param name="vectorStore">An instance of a vector store.</param>
    /// <param name="vectorDimensions">The number of dimensions to use for the memory embeddings.</param>
    /// <param name="functions">The functions to vectorize and store for searching related functions.</param>
    /// <param name="maxNumberOfFunctions">The maximum number of relevant functions to retrieve from the vector store.</param>
    /// <param name="loggerFactory">The logger factory to use for logging. If not provided, no logging will be performed.</param>
    /// <param name="options">The provider options.</param>
    /// <param name="collectionName">The collection name to use for storing and retrieving functions.</param>
    public ContextualFunctionProvider(
        VectorStore vectorStore,
        int vectorDimensions,
        IEnumerable<AIFunction> functions,
        int maxNumberOfFunctions,
        ILoggerFactory? loggerFactory = null,
        ContextualFunctionProviderOptions? options = null,
        string collectionName = "functions")
    {
        Verify.NotNull(vectorStore);
        Verify.True(vectorDimensions > 0, "Vector dimensions must be greater than 0");
        Verify.NotNull(functions);
        Verify.True(maxNumberOfFunctions > 0, "Max number of functions must be greater than 0");
        Verify.NotNullOrWhiteSpace(collectionName);

        this._options = options ?? new ContextualFunctionProviderOptions();
        Verify.True(this._options.NumberOfRecentMessagesInContext > 0, "Number of recent messages to include into context must be greater than 0");

        this._functionStore = new FunctionStore(
            vectorStore,
            collectionName,
            vectorDimensions,
            functions,
            maxNumberOfFunctions,
            loggerFactory,
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

        // Build the context
        var context = await this.BuildContextAsync(newMessages, cancellationToken).ConfigureAwait(false);

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

        // If there are more messages than the configured limit, remove the oldest ones
        for (int i = RecentMessagesBufferSize + this._options.NumberOfRecentMessagesInContext; i < this._recentMessages.Count; i++)
        {
            this._recentMessages.TryDequeue(out _);
        }

        return Task.CompletedTask;
    }

    /// <summary>
    /// Builds the context from chat messages.
    /// </summary>
    /// <param name="newMessages">The new messages.</param>
    /// <param name="cancellationToken">The cancellation token to use for cancellation.</param>
    private async Task<string> BuildContextAsync(ICollection<ChatMessage> newMessages, CancellationToken cancellationToken)
    {
        if (this._options.ContextEmbeddingValueProvider is not null)
        {
            var recentMessages = this._recentMessages
                .Except(newMessages) // Exclude the new messages from the recent messages
                .TakeLast(this._options.NumberOfRecentMessagesInContext); // Ensure we only take the recent messages up to the configured limit

            return await this._options.ContextEmbeddingValueProvider.Invoke(recentMessages, newMessages, cancellationToken).ConfigureAwait(false);
        }

        // Build context from the recent messages that already include the new messages
        return string.Join(
            Environment.NewLine,
            this._recentMessages.TakeLast(newMessages.Count + this._options.NumberOfRecentMessagesInContext)
                .Where(m => !string.IsNullOrWhiteSpace(m?.Text))
                .Select(m => m.Text));
    }
}
