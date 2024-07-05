// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Service for storing and retrieving vector records, that uses an in memory dictionary as the underlying storage.
/// </summary>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
[Experimental("SKEXP0001")]
public class VolatileVectorRecordStore<TRecord> : IVectorRecordStore<string, TRecord>
    where TRecord : class
{
    /// <summary>Internal storage for the record store.</summary>
    private readonly ConcurrentDictionary<string, ConcurrentDictionary<string, TRecord>> _internalCollection;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly VolatileVectorRecordStoreOptions _options;

    /// <summary>A set of types that a key on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedKeyTypes =
    [
        typeof(string)
    ];

    /// <summary>A property info object that points at the key property for the current model, allowing easy reading and writing of this property.</summary>
    private readonly PropertyInfo _keyPropertyInfo;

    /// <summary>
    /// Initializes a new instance of the <see cref="VolatileVectorRecordStore{TRecord}"/> class.
    /// </summary>
    /// <param name="options">Optional configuration options for this class.</param>
    public VolatileVectorRecordStore(VolatileVectorRecordStoreOptions? options = default)
    {
        // Assign.
        this._internalCollection = new();
        this._options = options ?? new VolatileVectorRecordStoreOptions();

        // Enumerate public properties using configuration or attributes.
        (PropertyInfo keyProperty, List<PropertyInfo> dataProperties, List<PropertyInfo> vectorProperties) properties;
        if (this._options.VectorStoreRecordDefinition is not null)
        {
            properties = VectorStoreRecordPropertyReader.FindProperties(typeof(TRecord), this._options.VectorStoreRecordDefinition, supportsMultipleVectors: true);
        }
        else
        {
            properties = VectorStoreRecordPropertyReader.FindProperties(typeof(TRecord), supportsMultipleVectors: true);
        }

        // Validate property types and store for later use.
        VectorStoreRecordPropertyReader.VerifyPropertyTypes([properties.keyProperty], s_supportedKeyTypes, "Key");
        this._keyPropertyInfo = properties.keyProperty;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="VolatileVectorRecordStore{TRecord}"/> class.
    /// </summary>
    /// <param name="internalCollection">Allows passing in the dictionary used for storage, for testing purposes.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    internal VolatileVectorRecordStore(ConcurrentDictionary<string, ConcurrentDictionary<string, TRecord>> internalCollection, VolatileVectorRecordStoreOptions? options = default)
        : this(options)
    {
        this._internalCollection = internalCollection;
    }

    /// <inheritdoc />
    public Task<TRecord?> GetAsync(string key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        var collectionDictionary = this.GetCollectionDictionary(options?.CollectionName);

        if (collectionDictionary.TryGetValue(key, out var record))
        {
            return Task.FromResult<TRecord?>(record);
        }

        return Task.FromResult<TRecord?>(null);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<string> keys, GetRecordOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
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
    public Task DeleteAsync(string key, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        var collectionDictionary = this.GetCollectionDictionary(options?.CollectionName);

        collectionDictionary.TryRemove(key, out _);
        return Task.CompletedTask;
    }

    /// <inheritdoc />
    public Task DeleteBatchAsync(IEnumerable<string> keys, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        var collectionDictionary = this.GetCollectionDictionary(options?.CollectionName);

        foreach (var key in keys)
        {
            collectionDictionary.TryRemove(key, out _);
        }

        return Task.CompletedTask;
    }

    /// <inheritdoc />
    public Task<string> UpsertAsync(TRecord record, UpsertRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        var collectionDictionary = this.GetCollectionDictionary(options?.CollectionName);

        var key = this._keyPropertyInfo.GetValue(record) as string;
        collectionDictionary.AddOrUpdate(key!, record, (key, currentValue) => record);

        return Task.FromResult(key!);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> UpsertBatchAsync(IEnumerable<TRecord> records, UpsertRecordOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        foreach (var record in records)
        {
            yield return await this.UpsertAsync(record, options, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <summary>
    /// Get a collection dictionary from the internal storage, creating it if it does not exist.
    /// Use the provided collection name if not null, and fall back to the default collection name otherwise.
    /// </summary>
    /// <param name="collectionName">The collection name passed to the operation.</param>
    /// <returns>The retrieved collection dictionary.</returns>
    private ConcurrentDictionary<string, TRecord> GetCollectionDictionary(string? collectionName)
    {
        string? chosenCollectionName = null;

        if (collectionName is not null)
        {
            chosenCollectionName = collectionName;
        }
        else if (this._options.DefaultCollectionName is not null)
        {
            chosenCollectionName = this._options.DefaultCollectionName;
        }
        else
        {
#pragma warning disable CA2208 // Instantiate argument exceptions correctly
            throw new ArgumentException("Collection name must be provided in the operation options, since no default was provided at construction time.", "options");
#pragma warning restore CA2208 // Instantiate argument exceptions correctly
        }

        return this._internalCollection.GetOrAdd(chosenCollectionName, _ => new());
    }
}
