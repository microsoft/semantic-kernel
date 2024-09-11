// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Service for storing and retrieving vector records, that uses an in memory dictionary as the underlying storage.
/// </summary>
/// <typeparam name="TKey">The data type of the record key.</typeparam>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
[Experimental("SKEXP0001")]
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class VolatileVectorStoreRecordCollection<TKey, TRecord> : IVectorStoreRecordCollection<TKey, TRecord>
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
    where TKey : notnull
    where TRecord : class
{
    /// <summary>Internal storage for the record collection.</summary>
    private readonly ConcurrentDictionary<string, ConcurrentDictionary<object, object>> _internalCollection;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly VolatileVectorStoreRecordCollectionOptions _options;

    /// <summary>The name of the collection that this <see cref="VolatileVectorStoreRecordCollection{TKey,TRecord}"/> will access.</summary>
    private readonly string _collectionName;

    /// <summary>A property info object that points at the key property for the current model, allowing easy reading and writing of this property.</summary>
    private readonly PropertyInfo _keyPropertyInfo;

    /// <summary>
    /// Initializes a new instance of the <see cref="VolatileVectorStoreRecordCollection{TKey,TRecord}"/> class.
    /// </summary>
    /// <param name="collectionName">The name of the collection that this <see cref="VolatileVectorStoreRecordCollection{TKey,TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public VolatileVectorStoreRecordCollection(string collectionName, VolatileVectorStoreRecordCollectionOptions? options = default)
    {
        // Verify.
        Verify.NotNullOrWhiteSpace(collectionName);

        // Assign.
        this._collectionName = collectionName;
        this._internalCollection = new();
        this._options = options ?? new VolatileVectorStoreRecordCollectionOptions();
        var vectorStoreRecordDefinition = this._options.VectorStoreRecordDefinition ?? VectorStoreRecordPropertyReader.CreateVectorStoreRecordDefinitionFromType(typeof(TRecord), true);

        // Get the key property info.
        var keyProperty = vectorStoreRecordDefinition.Properties.OfType<VectorStoreRecordKeyProperty>().FirstOrDefault();
        if (keyProperty is null)
        {
            throw new ArgumentException($"No Key property found on {typeof(TRecord).Name} or provided via {nameof(VectorStoreRecordDefinition)}");
        }

        this._keyPropertyInfo = typeof(TRecord).GetProperty(keyProperty.DataModelPropertyName) ?? throw new ArgumentException($"Key property {keyProperty.DataModelPropertyName} not found on {typeof(TRecord).Name}");
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="VolatileVectorStoreRecordCollection{TKey,TRecord}"/> class.
    /// </summary>
    /// <param name="internalCollection">Allows passing in the dictionary used for storage, for testing purposes.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="VolatileVectorStoreRecordCollection{TKey,TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    internal VolatileVectorStoreRecordCollection(ConcurrentDictionary<string, ConcurrentDictionary<object, object>> internalCollection, string collectionName, VolatileVectorStoreRecordCollectionOptions? options = default)
        : this(collectionName, options)
    {
        this._internalCollection = internalCollection;
    }

    /// <inheritdoc />
    public string CollectionName => this._collectionName;

    /// <inheritdoc />
    public Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        return this._internalCollection.ContainsKey(this._collectionName) ? Task.FromResult(true) : Task.FromResult(false);
    }

    /// <inheritdoc />
    public Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        this._internalCollection.TryAdd(this._collectionName, new ConcurrentDictionary<object, object>());
        return Task.CompletedTask;
    }

    /// <inheritdoc />
    public async Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
    {
        if (!await this.CollectionExistsAsync(cancellationToken).ConfigureAwait(false))
        {
            await this.CreateCollectionAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc />
    public Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
    {
        this._internalCollection.TryRemove(this._collectionName, out _);
        return Task.CompletedTask;
    }

    /// <inheritdoc />
    public Task<TRecord?> GetAsync(TKey key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        var collectionDictionary = this.GetCollectionDictionary();

        if (collectionDictionary.TryGetValue(key, out var record))
        {
            return Task.FromResult<TRecord?>(record as TRecord);
        }

        return Task.FromResult<TRecord?>(null);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<TKey> keys, GetRecordOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        foreach (var key in keys)
        {
            var record = await this.GetAsync(key, options, cancellationToken).ConfigureAwait(false);

            if (record is not null)
            {
                yield return record;
            }
        }
    }

    /// <inheritdoc />
    public Task DeleteAsync(TKey key, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        var collectionDictionary = this.GetCollectionDictionary();

        collectionDictionary.TryRemove(key, out _);
        return Task.CompletedTask;
    }

    /// <inheritdoc />
    public Task DeleteBatchAsync(IEnumerable<TKey> keys, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        var collectionDictionary = this.GetCollectionDictionary();

        foreach (var key in keys)
        {
            collectionDictionary.TryRemove(key, out _);
        }

        return Task.CompletedTask;
    }

    /// <inheritdoc />
    public Task<TKey> UpsertAsync(TRecord record, UpsertRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        var collectionDictionary = this.GetCollectionDictionary();

        var key = (TKey)this._keyPropertyInfo.GetValue(record)!;
        collectionDictionary.AddOrUpdate(key!, record, (key, currentValue) => record);

        return Task.FromResult(key!);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TKey> UpsertBatchAsync(IEnumerable<TRecord> records, UpsertRecordOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        foreach (var record in records)
        {
            yield return await this.UpsertAsync(record, options, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <summary>
    /// Get the collection dictionary from the internal storage, throws if it does not exist.
    /// </summary>
    /// <returns>The retrieved collection dictionary.</returns>
    private ConcurrentDictionary<object, object> GetCollectionDictionary()
    {
        if (!this._internalCollection.TryGetValue(this._collectionName, out var collectionDictionary))
        {
            throw new VectorStoreOperationException($"Call to vector store failed. Collection '{this._collectionName}' does not exist.");
        }

        return collectionDictionary;
    }
}
