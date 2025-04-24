// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.InMemory;

/// <summary>
/// Service for storing and retrieving vector records, and managing vector record collections, that uses an in memory dictionary as the underlying storage.
/// </summary>
public sealed class InMemoryVectorStore : IVectorStore
{
    private readonly InMemoryVectorStoreOptions _options;

    /// <summary>Metadata about vector store.</summary>
    private readonly VectorStoreMetadata _metadata;

    /// <summary>Internal storage for the record collection.</summary>
    private readonly ConcurrentDictionary<string, ConcurrentDictionary<object, object>> _internalCollections;

    /// <summary>The data type of each collection, to enforce a single type per collection.</summary>
    private readonly ConcurrentDictionary<string, Type> _internalCollectionTypes = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="InMemoryVectorStore"/> class.
    /// </summary>
    /// <param name="options">Optional configuration options for this class</param>
    public InMemoryVectorStore(InMemoryVectorStoreOptions? options = default)
    {
        this._options = options ?? new InMemoryVectorStoreOptions();
        this._internalCollections = new();

        this._metadata = new()
        {
            VectorStoreSystemName = InMemoryConstants.VectorStoreSystemName,
        };
    }

    /// <inheritdoc />
    public IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
        where TKey : notnull
        where TRecord : notnull
    {
        if (this._internalCollectionTypes.TryGetValue(name, out var existingCollectionDataType) && existingCollectionDataType != typeof(TRecord))
        {
            throw new InvalidOperationException($"Collection '{name}' already exists and with data type '{existingCollectionDataType.Name}' so cannot be re-created with data type '{typeof(TRecord).Name}'.");
        }

        var collection = new InMemoryVectorStoreRecordCollection<TKey, TRecord>(
            this._internalCollections,
            this._internalCollectionTypes,
            name,
            new()
            {
                VectorStoreRecordDefinition = vectorStoreRecordDefinition,
                EmbeddingGenerator = this._options.EmbeddingGenerator
            }) as IVectorStoreRecordCollection<TKey, TRecord>;
        return collection!;
    }

    /// <inheritdoc />
    public IAsyncEnumerable<string> ListCollectionNamesAsync(CancellationToken cancellationToken = default)
    {
        return this._internalCollections.Keys.ToAsyncEnumerable();
    }

    /// <inheritdoc />
    public Task<bool> CollectionExistsAsync(string name, CancellationToken cancellationToken = default)
    {
        return this._internalCollections.ContainsKey(name) ? Task.FromResult(true) : Task.FromResult(false);
    }

    /// <inheritdoc />
    public Task DeleteCollectionAsync(string name, CancellationToken cancellationToken = default)
    {
        this._internalCollections.TryRemove(name, out _);
        this._internalCollectionTypes.TryRemove(name, out _);
        return Task.CompletedTask;
    }

    /// <inheritdoc />
    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreMetadata) ? this._metadata :
            serviceType == typeof(ConcurrentDictionary<string, ConcurrentDictionary<object, object>>) ? this._internalCollections :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }
}
