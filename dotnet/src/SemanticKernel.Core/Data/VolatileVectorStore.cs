// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Service for storing and retrieving vector records, and managing vector record collections, that uses an in memory dictionary as the underlying storage.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class VolatileVectorStore : IVectorStore
{
    /// <summary>Internal storage for the record collection.</summary>
    private readonly ConcurrentDictionary<string, ConcurrentDictionary<string, object>> _internalCollection;

    /// <summary>
    /// Initializes a new instance of the <see cref="VolatileVectorStore"/> class.
    /// </summary>
    public VolatileVectorStore()
    {
        this._internalCollection = new();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="VolatileVectorStore"/> class.
    /// </summary>
    /// <param name="internalCollection">Allows passing in the dictionary used for storage, for testing purposes.</param>
    internal VolatileVectorStore(ConcurrentDictionary<string, ConcurrentDictionary<string, object>> internalCollection)
    {
        this._internalCollection = internalCollection;
    }

    /// <inheritdoc />
    public IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null) where TRecord : class
    {
        if (typeof(TKey) != typeof(string))
        {
            throw new NotSupportedException("Only string keys are supported.");
        }

        var typedInternalCollection = this._internalCollection as ConcurrentDictionary<string, ConcurrentDictionary<string, TRecord>>;
        var collection = new VolatileVectorStoreRecordCollection<TRecord>(typedInternalCollection!, name, new() { VectorStoreRecordDefinition = vectorStoreRecordDefinition }) as IVectorStoreRecordCollection<TKey, TRecord>;
        return collection!;
    }

    /// <inheritdoc />
    public IAsyncEnumerable<string> ListCollectionNamesAsync(CancellationToken cancellationToken = default)
    {
        return this._internalCollection.Keys.ToAsyncEnumerable();
    }
}
