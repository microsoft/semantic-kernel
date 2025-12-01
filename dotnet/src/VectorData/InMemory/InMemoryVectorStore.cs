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
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.InMemory;

/// <summary>
/// Service for storing and retrieving vector records, and managing vector record collections, that uses an in memory dictionary as the underlying storage.
/// </summary>
public sealed class InMemoryVectorStore : VectorStore
{
    /// <summary>Metadata about vector store.</summary>
    private readonly VectorStoreMetadata _metadata;

    /// <summary>Internal storage for the record collection.</summary>
    private readonly ConcurrentDictionary<string, ConcurrentDictionary<object, object>> _internalCollections;

    /// <summary>The data type of each collection, to enforce a single type per collection.</summary>
    private readonly ConcurrentDictionary<string, Type> _internalCollectionTypes = new();

    private readonly IEmbeddingGenerator? _embeddingGenerator;

    /// <summary>
    /// Initializes a new instance of the <see cref="InMemoryVectorStore"/> class.
    /// </summary>
    /// <param name="options">Optional configuration options for this class</param>
    public InMemoryVectorStore(InMemoryVectorStoreOptions? options = default)
    {
        this._internalCollections = new();
        this._embeddingGenerator = options?.EmbeddingGenerator;

        this._metadata = new()
        {
            VectorStoreSystemName = InMemoryConstants.VectorStoreSystemName,
        };
    }

#pragma warning disable IDE0090 // Use 'new(...)'
    /// <inheritdoc />
    [RequiresUnreferencedCode("The InMemory provider is incompatible with trimming.")]
    [RequiresDynamicCode("The InMemory provider is incompatible with NativeAOT.")]
#if NET
    public override InMemoryCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreCollectionDefinition? definition = null)
#else
    public override VectorStoreCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreCollectionDefinition? definition = null)
#endif
    {
        if (typeof(TRecord) == typeof(Dictionary<string, object?>))
        {
            throw new ArgumentException(VectorDataStrings.GetCollectionWithDictionaryNotSupported);
        }

        if (this._internalCollectionTypes.TryGetValue(name, out var existingCollectionDataType) && existingCollectionDataType != typeof(TRecord))
        {
            throw new InvalidOperationException($"Collection '{name}' already exists and with data type '{existingCollectionDataType.Name}' so cannot be re-created with data type '{typeof(TRecord).Name}'.");
        }

        var collection = new InMemoryCollection<TKey, TRecord>(
            this._internalCollections,
            this._internalCollectionTypes,
            name,
            new()
            {
                Definition = definition,
                EmbeddingGenerator = this._embeddingGenerator
            });
        return collection!;
    }

    /// <inheritdoc />
    [RequiresUnreferencedCode("The InMemory provider is incompatible with trimming.")]
    [RequiresDynamicCode("The InMemory provider is incompatible with NativeAOT.")]
#if NET
    public override InMemoryDynamicCollection GetDynamicCollection(string name, VectorStoreCollectionDefinition definition)
#else
    public override VectorStoreCollection<object, Dictionary<string, object?>> GetDynamicCollection(string name, VectorStoreCollectionDefinition definition)
#endif
        => new InMemoryDynamicCollection(
            this._internalCollections,
            this._internalCollectionTypes,
            name,
            new()
            {
                Definition = definition,
                EmbeddingGenerator = this._embeddingGenerator,
            }
        );
#pragma warning restore IDE0090

    /// <inheritdoc />
    public override IAsyncEnumerable<string> ListCollectionNamesAsync(CancellationToken cancellationToken = default)
    {
        return this._internalCollections.Keys.ToAsyncEnumerable();
    }

    /// <inheritdoc />
    public override Task<bool> CollectionExistsAsync(string name, CancellationToken cancellationToken = default)
    {
        return this._internalCollections.ContainsKey(name) ? Task.FromResult(true) : Task.FromResult(false);
    }

    /// <inheritdoc />
    public override Task EnsureCollectionDeletedAsync(string name, CancellationToken cancellationToken = default)
    {
        this._internalCollections.TryRemove(name, out _);
        this._internalCollectionTypes.TryRemove(name, out _);
        return Task.CompletedTask;
    }

    /// <inheritdoc />
    public override object? GetService(Type serviceType, object? serviceKey = null)
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
