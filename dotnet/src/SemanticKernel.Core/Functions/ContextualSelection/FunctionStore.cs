// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Functions;

/// <summary>
/// Represents a vector store for <see cref="AIFunction"/> objects where the function name and description can be used for similarity searches.
/// </summary>
internal sealed class FunctionStore
{
    private readonly VectorStore _vectorStore;
    private readonly Dictionary<string, AIFunction> _functionByName;
    private readonly IEmbeddingGenerator<string, Embedding<float>> _embeddingGenerator;
    private readonly string _collectionName;
    private readonly FunctionStoreOptions _options;
    private readonly VectorStoreCollection<object, Dictionary<string, object?>> _collection;

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionStore"/> class.
    /// </summary>
    /// <param name="inMemoryVectorStore">The vector store to use for storing functions.</param>
    /// <param name="collectionName">The name of the collection to use for storing and retrieving functions.</param>
    /// <param name="embeddingGenerator">The embedding generator to use for generating embeddings.</param>
    /// <param name="vectorDimensions">The number of dimensions to use for the memory embeddings.</param>
    /// <param name="functions">The functions to vectorize and store for searching related functions.</param>
    /// <param name="options">The options to use for the function store.</param>
    public FunctionStore(
        VectorStore inMemoryVectorStore,
        string collectionName,
        IEmbeddingGenerator<string, Embedding<float>> embeddingGenerator,
        int vectorDimensions,
        IReadOnlyList<AIFunction> functions,
        FunctionStoreOptions? options = null)
    {
        Verify.NotNull(inMemoryVectorStore);
        Verify.NotNullOrWhiteSpace(collectionName);
        Verify.NotNull(embeddingGenerator);
        Verify.True(vectorDimensions > 0, "Vector dimensions must be greater than 0");
        Verify.NotNull(functions);

        this._vectorStore = inMemoryVectorStore;
        this._collectionName = collectionName;
        this._embeddingGenerator = embeddingGenerator;
        this._functionByName = functions.ToDictionary(function => function.Name);

        this._options = options ?? new FunctionStoreOptions();

        // Create and assert the collection support record keys of string type
        this._collection = this._vectorStore.GetDynamicCollection(collectionName, new VectorStoreCollectionDefinition()
        {
            Properties = [
                new VectorStoreKeyProperty("Name", typeof(string)),
                new VectorStoreVectorProperty("Embedding", typeof(ReadOnlyMemory<float>), dimensions: vectorDimensions)
            ]
        });
    }

    /// <summary>
    /// Saves the functions to the vector store.
    /// </summary>
    /// <param name="cancellationToken">The cancellation token to use for cancellation.</param>
    public async Task SaveAsync(CancellationToken cancellationToken = default)
    {
        // Get function data to vectorize
        var nameSourcePairs = await this.GetFunctionVectorizationSourcesAsync(cancellationToken).ConfigureAwait(false);

        // Generate embeddings
        var embeddings = await this._embeddingGenerator
            .GenerateAsync([.. nameSourcePairs.Select(l => l.VectorizationSource)], cancellationToken: cancellationToken)
            .ConfigureAwait(false);

        var functionRecords = new List<Dictionary<string, object?>>(nameSourcePairs.Count);

        // Create vector store records
        for (var i = 0; i < nameSourcePairs.Count; i++)
        {
            var (name, data) = nameSourcePairs[i];

            functionRecords.Add(new Dictionary<string, object?>()
            {
                ["Name"] = name,
                ["Embedding"] = embeddings[i].Vector
            });
        }

        // Create collection and upsert all vector store records
        await this._collection.EnsureCollectionExistsAsync(cancellationToken).ConfigureAwait(false);

        await this._collection.UpsertAsync(functionRecords, cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Searches for functions based on the provided context.
    /// </summary>
    /// <param name="context">The context to search for functions.</param>
    /// <param name="cancellationToken">The cancellation token to use for cancellation.</param>
    public async Task<IEnumerable<AIFunction>> SearchAsync(string context, CancellationToken cancellationToken = default)
    {
        if (!await this._collection.CollectionExistsAsync(cancellationToken).ConfigureAwait(false))
        {
            throw new InvalidOperationException($"Collection '{this._collectionName}' does not exist.");
        }

        var requestEmbedding = await this._embeddingGenerator.GenerateAsync(context, cancellationToken: cancellationToken).ConfigureAwait(false);

        var results = await this._collection
            .SearchAsync(requestEmbedding, top: this._options.MaxNumberOfFunctions, cancellationToken: cancellationToken)
            .ToListAsync(cancellationToken)
            .ConfigureAwait(false);

        if (this._options.MinimumRelevanceScore is { } minScore)
        {
            results = [.. results.Where(result => result.Score >= minScore)];
        }

        return results.Select(result => this._functionByName[(string)result.Record["Name"]!]);
    }

    /// <summary>
    /// Get the function vectorization sources.
    /// </summary>
    /// <param name="cancellationToken">The cancellation token to use for cancellation.</param>
    /// <returns>The function name and vectorization source pairs.</returns>
    private async Task<List<(string Name, string VectorizationSource)>> GetFunctionVectorizationSourcesAsync(CancellationToken cancellationToken)
    {
        List<(string, string)> nameSourcePairs = new(this._functionByName.Count);

        var provider = (Func<AIFunction, CancellationToken, Task<string>>?)this._options.FunctionEmbeddingValueProvider ?? ((function, _) =>
        {
            return Task.FromResult($"Function name: {function.Name}. Description: {function.Description}");
        });

        foreach (KeyValuePair<string, AIFunction> pair in this._functionByName)
        {
            var vectorizationSource = await provider.Invoke(pair.Value, cancellationToken).ConfigureAwait(false);

            nameSourcePairs.Add((pair.Key, vectorizationSource));
        }

        return nameSourcePairs;
    }
}
