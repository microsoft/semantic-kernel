// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.InMemory;

/// <summary>
/// Service for storing and retrieving vector records, and managing vector record collections, that uses an in memory dictionary as the underlying storage.
/// </summary>
public sealed class InMemoryVectorStore : IVectorStore
{
    /// <summary>Internal storage for the record collection.</summary>
    private readonly ConcurrentDictionary<string, ConcurrentDictionary<object, object>> _internalCollection;

    /// <summary>The data type of each collection, to enforce a single type per collection.</summary>
    private readonly ConcurrentDictionary<string, Type> _internalCollectionTypes = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="InMemoryVectorStore"/> class.
    /// </summary>
    public InMemoryVectorStore()
    {
        this._internalCollection = new();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="InMemoryVectorStore"/> class.
    /// </summary>
    /// <param name="internalCollection">Allows passing in the dictionary used for storage, for testing purposes.</param>
    internal InMemoryVectorStore(ConcurrentDictionary<string, ConcurrentDictionary<object, object>> internalCollection)
    {
        this._internalCollection = internalCollection;
    }

    /// <inheritdoc />
    public IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, [DynamicallyAccessedMembers(DynamicallyAccessedMemberTypes.PublicProperties | DynamicallyAccessedMemberTypes.PublicConstructors)] TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
        where TKey : notnull
    {
        if (this._internalCollectionTypes.TryGetValue(name, out var existingCollectionDataType) && existingCollectionDataType != typeof(TRecord))
        {
            throw new InvalidOperationException($"Collection '{name}' already exists and with data type '{existingCollectionDataType.Name}' so cannot be re-created with data type '{typeof(TRecord).Name}'.");
        }

        var collection = new InMemoryVectorStoreRecordCollection<TKey, TRecord>(
            this._internalCollection,
            this._internalCollectionTypes,
            name,
            new() { VectorStoreRecordDefinition = vectorStoreRecordDefinition }) as IVectorStoreRecordCollection<TKey, TRecord>;
        return collection!;
    }

    /// <inheritdoc />
    public IAsyncEnumerable<string> ListCollectionNamesAsync(CancellationToken cancellationToken = default)
    {
        return this._internalCollection.Keys.ToAsyncEnumerable();
    }
}
