// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Functions;

/// <summary>
/// Represents a vector store for <see cref="AIFunction"/> objects where the function name and description can be used for similarity searches.
/// </summary>
internal sealed class FunctionStore
{
    private readonly VectorStore _vectorStore;
    private readonly Dictionary<string, AIFunction> _functionByName;
    private readonly string _collectionName;
    private readonly int _maxNumberOfFunctions;
    private readonly ILogger _logger;
    private readonly FunctionStoreOptions _options;
    private readonly VectorStoreCollection<object, Dictionary<string, object?>> _collection;
    private bool _isCollectionExistenceAsserted = false;

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionStore"/> class.
    /// </summary>
    /// <param name="vectorStore">The vector store to use for storing functions.</param>
    /// <param name="collectionName">The name of the collection to use for storing and retrieving functions.</param>
    /// <param name="vectorDimensions">The number of dimensions to use for the memory embeddings.</param>
    /// <param name="functions">The functions to vectorize and store for searching related functions.</param>
    /// <param name="maxNumberOfFunctions">The maximum number of relevant functions to retrieve from the vector store.</param>
    /// <param name="loggerFactory">The logger factory to use for logging. If not provided, no logging will be performed.</param>
    /// <param name="options">The options to use for the function store.</param>
    internal FunctionStore(
        VectorStore vectorStore,
        string collectionName,
        int vectorDimensions,
        IEnumerable<AIFunction> functions,
        int maxNumberOfFunctions,
        ILoggerFactory? loggerFactory = default,
        FunctionStoreOptions? options = null)
    {
        Verify.NotNull(vectorStore);
        Verify.NotNullOrWhiteSpace(collectionName);
        Verify.True(vectorDimensions > 0, "Vector dimensions must be greater than 0");
        Verify.NotNull(functions);
        Verify.True(maxNumberOfFunctions > 0, "Max number of functions must be greater than 0");

        this._vectorStore = vectorStore;
        this._collectionName = collectionName;
        this._functionByName = functions.ToDictionary(function => function.Name);
        this._maxNumberOfFunctions = maxNumberOfFunctions;
        this._logger = (loggerFactory ?? NullLoggerFactory.Instance).CreateLogger<FunctionStore>();
        this._options = options ?? new FunctionStoreOptions();

        // Create and assert the collection support record keys of string type
        this._collection = this._vectorStore.GetDynamicCollection(collectionName, new VectorStoreCollectionDefinition()
        {
            Properties = [
                new VectorStoreKeyProperty("Name", typeof(string)),
                new VectorStoreVectorProperty("Embedding", typeof(string), dimensions: vectorDimensions)
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
        var nameSourcePairs = await this.GetFunctionsVectorizationInfoAsync(cancellationToken).ConfigureAwait(false);

        var functionRecords = new List<Dictionary<string, object?>>(nameSourcePairs.Count);

        // Create vector store records
        for (var i = 0; i < nameSourcePairs.Count; i++)
        {
            var (name, vectorizationSource) = nameSourcePairs[i];

            functionRecords.Add(new Dictionary<string, object?>()
            {
                ["Name"] = name,
                ["Embedding"] = vectorizationSource
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
        await this.AssertCollectionExistsAsync(cancellationToken).ConfigureAwait(false);

        var results = await this._collection
            .SearchAsync(context, top: this._maxNumberOfFunctions, cancellationToken: cancellationToken)
            .ToListAsync(cancellationToken)
            .ConfigureAwait(false);

        this._logger.LogFunctionsSearchResults(context, this._maxNumberOfFunctions, results);

        return results.Select(result => this._functionByName[(string)result.Record["Name"]!]);
    }

    /// <summary>
    /// Get the function vectorization information, which includes the function name and the source used for vectorization.
    /// </summary>
    /// <param name="cancellationToken">The cancellation token to use for cancellation.</param>
    /// <returns>The function name and vectorization source pairs.</returns>
    private async Task<List<FunctionVectorizationInfo>> GetFunctionsVectorizationInfoAsync(CancellationToken cancellationToken)
    {
        List<FunctionVectorizationInfo> nameSourcePairs = new(this._functionByName.Count);

        var provider = (Func<AIFunction, CancellationToken, Task<string>>?)this._options.EmbeddingValueProvider ?? ((function, _) =>
        {
            string descriptionPart = string.IsNullOrEmpty(function.Description) ? string.Empty : $", description: {function.Description}";
            return Task.FromResult($"Function name: {function.Name}{descriptionPart}");
        });

        foreach (KeyValuePair<string, AIFunction> pair in this._functionByName)
        {
            var vectorizationSource = await provider.Invoke(pair.Value, cancellationToken).ConfigureAwait(false);

            nameSourcePairs.Add(new FunctionVectorizationInfo(pair.Key, vectorizationSource));
        }

        this._logger.LogFunctionsVectorizationInfo(nameSourcePairs);

        return nameSourcePairs;
    }

    /// <summary>
    /// Asserts that the collection exists in the vector store.
    /// </summary>
    /// <param name="cancellationToken">The cancellation token to use for cancellation.</param>
    private async Task AssertCollectionExistsAsync(CancellationToken cancellationToken)
    {
        if (!this._isCollectionExistenceAsserted)
        {
            if (!await this._collection.CollectionExistsAsync(cancellationToken).ConfigureAwait(false))
            {
                throw new InvalidOperationException($"Collection '{this._collectionName}' does not exist.");
            }

            this._isCollectionExistenceAsserted = true;
        }
    }

    internal readonly struct FunctionVectorizationInfo
    {
        public string Name { get; }

        public string VectorizationSource { get; }

        public FunctionVectorizationInfo(string name, string vectorizationSource)
        {
            this.Name = name;
            this.VectorizationSource = vectorizationSource;
        }

        public void Deconstruct(out string name, out string vectorizationSource)
        {
            name = this.Name;
            vectorizationSource = this.VectorizationSource;
        }
    }
}
