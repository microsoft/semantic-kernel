// Copyright (c) Microsoft. All rights reserved.

using System;
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
/// The provider is designed to work with `Connectors.Memory.InMemory` vector store. Using other
/// vector stores will require the data synchronization and data lifetime management to be done by the caller.
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
    private readonly ContextualFunctionProviderOptions _options;
    private bool _areFunctionsVectorized = false;

    /// <summary>
    /// Initializes a new instance of the <see cref="ContextualFunctionProvider"/> class.
    /// </summary>
    /// <param name="inMemoryVectorStore">An instance of the `Connectors.Memory.InMemory`
    /// in-memory vector store. Using other vector stores will require the data synchronization
    /// and data lifetime management to be done by the caller.</param>
    /// <param name="vectorDimensions">The number of dimensions to use for the memory embeddings.</param>
    /// <param name="functions">The functions to vectorize and store for searching related functions.</param>
    /// <param name="options">The provider options.</param>
    /// <param name="collectionName">The collection name to use for storing and retrieving functions.</param>
    public ContextualFunctionProvider(
        VectorStore inMemoryVectorStore,
        int vectorDimensions,
        IReadOnlyList<AIFunction> functions,
        ContextualFunctionProviderOptions? options = null,
        string collectionName = "functions")
    {
        Verify.NotNull(inMemoryVectorStore);
        Verify.True(vectorDimensions > 0, "Vector dimensions must be greater than 0");
        Verify.NotNull(functions);
        Verify.NotNullOrWhiteSpace(collectionName);

        this._options = options ?? new ContextualFunctionProviderOptions();

        this._functionStore = new FunctionStore(
            inMemoryVectorStore,
            collectionName,
            vectorDimensions,
            functions,
            options: new()
            {
                EmbeddingValueProvider = this._options.EmbeddingValueProvider,
                MaxNumberOfFunctions = this._options.MaxNumberOfFunctions,
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
        var context = await this.BuildContextAsync(newMessages, cancellationToken).ConfigureAwait(false);

        // Get the function relevant to the context
        var functions = await this._functionStore
                .SearchAsync(context, cancellationToken: cancellationToken)
                .ConfigureAwait(false);

        return new AIContext { AIFunctions = [.. functions] };
    }

    /// <summary>
    /// Builds the context from chat messages.
    /// </summary>
    /// <param name="messages">The messages to build the context from.</param>
    /// <param name="cancellationToken">The cancellation token to use for cancellation.</param>
    private async Task<string> BuildContextAsync(ICollection<ChatMessage> messages, CancellationToken cancellationToken)
    {
        if (this._options.ContextEmbeddingValueProvider is not null)
        {
            return await this._options.ContextEmbeddingValueProvider.Invoke(messages, cancellationToken).ConfigureAwait(false);
        }

        return string.Join(
            Environment.NewLine,
            messages.
                Where(m => !string.IsNullOrWhiteSpace(m?.Text)).
                Select(m => m.Text));
    }
}
