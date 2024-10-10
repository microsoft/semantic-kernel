<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
﻿// Copyright (c) Microsoft. All rights reserved.

using System;
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
﻿// Copyright (c) Microsoft. All rights reserved.

using System;
=======
// Copyright (c) Microsoft. All rights reserved.

>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.

>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
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
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
    /// <summary>A set of types that vectors on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedVectorTypes =
    [
        typeof(ReadOnlyMemory<float>),
        typeof(ReadOnlyMemory<float>?),
    ];

    /// <summary>The default options for vector search.</summary>
    private static readonly VectorSearchOptions s_defaultVectorSearchOptions = new();

    /// <summary>Internal storage for all of the record collections.</summary>
    private readonly ConcurrentDictionary<string, ConcurrentDictionary<object, object>> _internalCollections;

    /// <summary>The data type of each collection, to enforce a single type per collection.</summary>
    private readonly ConcurrentDictionary<string, Type> _internalCollectionTypes;
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
    /// <summary>Internal storage for the record collection.</summary>
    private readonly ConcurrentDictionary<string, ConcurrentDictionary<object, object>> _internalCollection;

    /// <summary>Optional configuration options for this class.</summary>
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    private readonly VolatileVectorStoreRecordCollectionOptions _options;
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
    private readonly VolatileVectorStoreRecordCollectionOptions _options;
=======
    private readonly VolatileVectorStoreRecordCollectionOptions<TKey, TRecord> _options;
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    private readonly VolatileVectorStoreRecordCollectionOptions<TKey, TRecord> _options;
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes

    /// <summary>The name of the collection that this <see cref="VolatileVectorStoreRecordCollection{TKey,TRecord}"/> will access.</summary>
    private readonly string _collectionName;

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
    /// <summary>A helper to access property information for the current data model and record definition.</summary>
    private readonly VectorStoreRecordPropertyReader _propertyReader;

    /// <summary>A dictionary of vector properties on the provided model, keyed by the property name.</summary>
    private readonly Dictionary<string, VectorStoreRecordVectorProperty> _vectorProperties;

    /// <summary>An function to look up vectors from the records.</summary>
    private readonly VolatileVectorStoreVectorResolver<TRecord> _vectorResolver;

    /// <summary>An function to look up keys from the records.</summary>
    private readonly VolatileVectorStoreKeyResolver<TKey, TRecord> _keyResolver;

<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
    /// <summary>A property info object that points at the key property for the current model, allowing easy reading and writing of this property.</summary>
    private readonly PropertyInfo _keyPropertyInfo;

    /// <summary>
    /// Initializes a new instance of the <see cref="VolatileVectorStoreRecordCollection{TKey,TRecord}"/> class.
    /// </summary>
    /// <param name="collectionName">The name of the collection that this <see cref="VolatileVectorStoreRecordCollection{TKey,TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    public VolatileVectorStoreRecordCollection(string collectionName, VolatileVectorStoreRecordCollectionOptions? options = default)
    {
        // Verify.
        Verify.NotNullOrWhiteSpace(collectionName);

        // Assign.
        this._collectionName = collectionName;
        this._internalCollection = new();
        this._options = options ?? new VolatileVectorStoreRecordCollectionOptions();
        var vectorStoreRecordDefinition = this._options.VectorStoreRecordDefinition ?? VectorStoreRecordPropertyReader.CreateVectorStoreRecordDefinitionFromType(typeof(TRecord), true);
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
    public VolatileVectorStoreRecordCollection(string collectionName, VolatileVectorStoreRecordCollectionOptions<TKey, TRecord>? options = default)
    {
        // Verify.
        Verify.NotNullOrWhiteSpace(collectionName);
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelDefinitionSupplied(typeof(TRecord), options?.VectorStoreRecordDefinition is not null);

        // Assign.
        this._collectionName = collectionName;
        this._internalCollections = new();
        this._internalCollectionTypes = new();
        this._options = options ?? new VolatileVectorStoreRecordCollectionOptions<TKey, TRecord>();
        this._propertyReader = new VectorStoreRecordPropertyReader(typeof(TRecord), this._options.VectorStoreRecordDefinition, new() { RequiresAtLeastOneVector = false, SupportsMultipleKeys = false, SupportsMultipleVectors = true });

        // Validate property types.
        var properties = VectorStoreRecordPropertyReader.SplitDefinitionAndVerify(typeof(TRecord).Name, vectorStoreRecordDefinition, supportsMultipleVectors: true, requiresAtLeastOneVector: false);
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(properties.VectorProperties, s_supportedVectorTypes, "Vector");
        this._vectorProperties = properties.VectorProperties.ToDictionary(x => x.DataModelPropertyName);
        if (properties.VectorProperties.Count > 0)
        {
            this._firstVectorPropertyName = properties.VectorProperties.First().DataModelPropertyName;
        }
        this._internalCollection = new();
        this._options = options ?? new VolatileVectorStoreRecordCollectionOptions();
        var vectorStorePropertyReader = new VectorStoreRecordPropertyReader(typeof(TRecord), this._options.VectorStoreRecordDefinition, new() { RequiresAtLeastOneVector = false, SupportsMultipleKeys = false, SupportsMultipleVectors = true });
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes

        // Get the key property info.
        var keyProperty = vectorStoreRecordDefinition.Properties.OfType<VectorStoreRecordKeyProperty>().FirstOrDefault();
        if (keyProperty is null)
        {
            throw new ArgumentException($"No Key property found on {typeof(TRecord).Name} or provided via {nameof(VectorStoreRecordDefinition)}");
        }

        this._keyPropertyInfo = typeof(TRecord).GetProperty(keyProperty.DataModelPropertyName) ?? throw new ArgumentException($"Key property {keyProperty.DataModelPropertyName} not found on {typeof(TRecord).Name}");
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes

        // Assign resolvers.
        this._vectorResolver = CreateVectorResolver(this._options.VectorResolver, this._vectorProperties);
        this._keyResolver = CreateKeyResolver(this._options.KeyResolver, properties.KeyProperty);
        this._keyPropertyInfo = vectorStorePropertyReader.KeyPropertyInfo;
        this._propertyReader.VerifyVectorProperties(s_supportedVectorTypes);
        this._vectorProperties = this._propertyReader.VectorProperties.ToDictionary(x => x.DataModelPropertyName);

        // Assign resolvers.
        this._vectorResolver = CreateVectorResolver(this._options.VectorResolver, this._vectorProperties);
        this._keyResolver = CreateKeyResolver(this._options.KeyResolver, this._propertyReader.KeyProperty);
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="VolatileVectorStoreRecordCollection{TKey,TRecord}"/> class.
    /// </summary>
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
    /// <param name="internalCollection">Internal storage for the record collection.</param>
    /// <param name="internalCollectionTypes">The data type of each collection, to enforce a single type per collection.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="VolatileVectorStoreRecordCollection{TKey,TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    internal VolatileVectorStoreRecordCollection(
        ConcurrentDictionary<string, ConcurrentDictionary<object, object>> internalCollection,
        ConcurrentDictionary<string, Type> internalCollectionTypes,
        string collectionName,
        VolatileVectorStoreRecordCollectionOptions<TKey, TRecord>? options = default)
        : this(collectionName, options)
    {
        this._internalCollections = internalCollection;
        this._internalCollectionTypes = internalCollectionTypes;
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
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
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
        return this._internalCollections.ContainsKey(this._collectionName) ? Task.FromResult(true) : Task.FromResult(false);
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        return this._internalCollections.ContainsKey(this._collectionName) ? Task.FromResult(true) : Task.FromResult(false);
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
        return this._internalCollections.ContainsKey(this._collectionName) ? Task.FromResult(true) : Task.FromResult(false);
>>>>>>> main
>>>>>>> Stashed changes
        return this._internalCollection.ContainsKey(this._collectionName) ? Task.FromResult(true) : Task.FromResult(false);
    }

    /// <inheritdoc />
    public Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
        if (!this._internalCollections.ContainsKey(this._collectionName))
        {
            this._internalCollections.TryAdd(this._collectionName, new ConcurrentDictionary<object, object>());
            this._internalCollectionTypes.TryAdd(this._collectionName, typeof(TRecord));
        }

<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
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
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        this._internalCollection.TryRemove(this._collectionName, out _);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
        this._internalCollection.TryRemove(this._collectionName, out _);
=======
        this._internalCollections.TryRemove(this._collectionName, out _);
        this._internalCollection.TryRemove(this._collectionName, out _)
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        this._internalCollections.TryRemove(this._collectionName, out _);
        this._internalCollection.TryRemove(this._collectionName, out _)
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
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

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        var key = (TKey)this._keyPropertyInfo.GetValue(record)!;
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
        var key = (TKey)this._keyPropertyInfo.GetValue(record)!;
=======
        var key = (TKey)this._keyResolver(record)!;
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        var key = (TKey)this._keyResolver(record)!;
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
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

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
    /// <inheritdoc />
#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously - Need to satisfy the interface which returns IAsyncEnumerable
    public async IAsyncEnumerable<VectorSearchResult<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, VectorSearchOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
#pragma warning restore CS1998
    {
        Verify.NotNull(vector);

        if (this._propertyReader.FirstVectorPropertyName is null)
        {
            throw new InvalidOperationException("The collection does not have any vector fields, so vector search is not possible.");
        }

        if (vector is not ReadOnlyMemory<float> floatVector)
        {
            throw new NotSupportedException($"The provided vector type {vector.GetType().FullName} is not supported by the Volatile Vector Store.");
        }

        // Resolve options and get requested vector property or first as default.
        var internalOptions = options ?? s_defaultVectorSearchOptions;

        var vectorPropertyName = string.IsNullOrWhiteSpace(internalOptions.VectorPropertyName) ? this._propertyReader.FirstVectorPropertyName : internalOptions.VectorPropertyName;
        if (!this._vectorProperties.TryGetValue(vectorPropertyName!, out var vectorProperty))
        {
            throw new InvalidOperationException($"The collection does not have a vector field named '{internalOptions.VectorPropertyName}', so vector search is not possible.");
        }

        // Filter records using the provided filter before doing the vector comparison.
        var filteredRecords = VolatileVectorStoreCollectionSearchMapping.FilterRecords(internalOptions.Filter, this.GetCollectionDictionary().Values);

        // Compare each vector in the filtered results with the provided vector.
        var results = filteredRecords.Select<object, (object record, float score)?>((record) =>
        {
            var vectorObject = this._vectorResolver(vectorPropertyName!, (TRecord)record);
            if (vectorObject is not ReadOnlyMemory<float> dbVector)
            {
                return null;
            }

            var score = VolatileVectorStoreCollectionSearchMapping.CompareVectors(floatVector.Span, dbVector.Span, vectorProperty.DistanceFunction);
            var convertedscore = VolatileVectorStoreCollectionSearchMapping.ConvertScore(score, vectorProperty.DistanceFunction);
            return (record, convertedscore);
        });

        // Get the non-null results, sort them appropriately for the selected distance function and return the requested page.
        var nonNullResults = results.Where(x => x.HasValue).Select(x => x!.Value);
        var sortedScoredResults = VolatileVectorStoreCollectionSearchMapping.ShouldSortDescending(vectorProperty.DistanceFunction) ?
            nonNullResults.OrderByDescending(x => x.score) :
            nonNullResults.OrderBy(x => x.score);

        foreach (var scoredResult in sortedScoredResults.Skip(internalOptions.Skip).Take(internalOptions.Top))
        {
            yield return new VectorSearchResult<TRecord>((TRecord)scoredResult.record, scoredResult.score);
        }
    }

<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
    /// <summary>
    /// Get the collection dictionary from the internal storage, throws if it does not exist.
    /// </summary>
    /// <returns>The retrieved collection dictionary.</returns>
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
    internal ConcurrentDictionary<object, object> GetCollectionDictionary()
    {
        if (!this._internalCollections.TryGetValue(this._collectionName, out var collectionDictionary))
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    internal ConcurrentDictionary<object, object> GetCollectionDictionary()
    {
        if (!this._internalCollections.TryGetValue(this._collectionName, out var collectionDictionary))
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
    private ConcurrentDictionary<object, object> GetCollectionDictionary()
    {
        if (!this._internalCollection.TryGetValue(this._collectionName, out var collectionDictionary))
        {
            throw new VectorStoreOperationException($"Call to vector store failed. Collection '{this._collectionName}' does not exist.");
        }

        return collectionDictionary;
    }
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes

    /// <summary>
    /// Pick / create a vector resolver that will read a vector from a record in the store based on the vector name.
    /// 1. If an override resolver is provided, use that.
    /// 2. If the record type is <see cref="VectorStoreGenericDataModel{TKey}"/> create a resolver that looks up the vector in its <see cref="VectorStoreGenericDataModel{TKey}.Vectors"/> dictionary.
    /// 3. Otherwise, create a resolver that assumes the vector is a property directly on the record and use the record definition to determine the name.
    /// </summary>
    /// <param name="overrideVectorResolver">The override vector resolver if one was provided.</param>
    /// <param name="vectorProperties">A dictionary of vector properties from the record definition.</param>
    /// <returns>The <see cref="VolatileVectorStoreVectorResolver{TRecord}"/>.</returns>
    private static VolatileVectorStoreVectorResolver<TRecord> CreateVectorResolver(VolatileVectorStoreVectorResolver<TRecord>? overrideVectorResolver, Dictionary<string, VectorStoreRecordVectorProperty> vectorProperties)
    {
        // Custom resolver.
        if (overrideVectorResolver is not null)
        {
            return overrideVectorResolver;
        }

        // Generic data model resolver.
        if (typeof(TRecord).IsGenericType && typeof(TRecord).GetGenericTypeDefinition() == typeof(VectorStoreGenericDataModel<>))
        {
            return (vectorName, record) =>
            {
                var genericDataModelRecord = record as VectorStoreGenericDataModel<TKey>;
                var vectorsDictionary = genericDataModelRecord!.Vectors;
                if (vectorsDictionary != null && vectorsDictionary.TryGetValue(vectorName, out var vector))
                {
                    return vector;
                }

                throw new InvalidOperationException($"The collection does not have a vector field named '{vectorName}', so vector search is not possible.");
            };
        }

        // Default resolver.
        var vectorPropertiesInfo = vectorProperties.Values
            .Select(x => x.DataModelPropertyName)
            .Select(x => typeof(TRecord).GetProperty(x) ?? throw new ArgumentException($"Vector property '{x}' was not found on {typeof(TRecord).Name}"))
            .ToDictionary(x => x.Name);

        return (vectorName, record) =>
        {
            if (vectorPropertiesInfo.TryGetValue(vectorName, out var vectorPropertyInfo))
            {
                return vectorPropertyInfo.GetValue(record);
            }

            throw new InvalidOperationException($"The collection does not have a vector field named '{vectorName}', so vector search is not possible.");
        };
    }

    /// <summary>
    /// Pick / create a key resolver that will read a key from a record in the store.
    /// 1. If an override resolver is provided, use that.
    /// 2. If the record type is <see cref="VectorStoreGenericDataModel{TKey}"/> create a resolver that reads the Key property from it.
    /// 3. Otherwise, create a resolver that assumes the key is a property directly on the record and use the record definition to determine the name.
    /// </summary>
    /// <param name="overrideKeyResolver">The override key resolver if one was provided.</param>
    /// <param name="keyProperty">They key property from the record definition.</param>
    /// <returns>The <see cref="VolatileVectorStoreKeyResolver{TKey, TRecord}"/>.</returns>
    private static VolatileVectorStoreKeyResolver<TKey, TRecord> CreateKeyResolver(VolatileVectorStoreKeyResolver<TKey, TRecord>? overrideKeyResolver, VectorStoreRecordKeyProperty keyProperty)
    {
        // Custom resolver.
        if (overrideKeyResolver is not null)
        {
            return overrideKeyResolver;
        }

        // Generic data model resolver.
        if (typeof(TRecord).IsGenericType && typeof(TRecord).GetGenericTypeDefinition() == typeof(VectorStoreGenericDataModel<>))
        {
            return (record) =>
            {
                var genericDataModelRecord = record as VectorStoreGenericDataModel<TKey>;
                return genericDataModelRecord!.Key;
            };
        }

        // Default resolver.
        var keyPropertyInfo = typeof(TRecord).GetProperty(keyProperty.DataModelPropertyName) ?? throw new ArgumentException($"Key property {keyProperty.DataModelPropertyName} not found on {typeof(TRecord).Name}");
        return (record) => (TKey)keyPropertyInfo.GetValue(record)!;
    }
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
}
