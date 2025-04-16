﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.InMemory;

/// <summary>
/// Service for storing and retrieving vector records, that uses an in memory dictionary as the underlying storage.
/// </summary>
/// <typeparam name="TKey">The data type of the record key.</typeparam>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class InMemoryVectorStoreRecordCollection<TKey, TRecord> : IVectorStoreRecordCollection<TKey, TRecord>
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
    where TKey : notnull
    where TRecord : notnull
{
    /// <summary>Metadata about vector store record collection.</summary>
    private readonly VectorStoreRecordCollectionMetadata _collectionMetadata;

    /// <summary>The default options for vector search.</summary>
    private static readonly VectorSearchOptions<TRecord> s_defaultVectorSearchOptions = new();

    /// <summary>Internal storage for all of the record collections.</summary>
    private readonly ConcurrentDictionary<string, ConcurrentDictionary<object, object>> _internalCollections;

    /// <summary>The data type of each collection, to enforce a single type per collection.</summary>
    private readonly ConcurrentDictionary<string, Type> _internalCollectionTypes;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly InMemoryVectorStoreRecordCollectionOptions<TKey, TRecord> _options;

    /// <summary>The name of the collection that this <see cref="InMemoryVectorStoreRecordCollection{TKey,TRecord}"/> will access.</summary>
    private readonly string _collectionName;

    /// <summary>The model for this collection.</summary>
    private readonly VectorStoreRecordModel _model;

    /// <summary>An function to look up vectors from the records.</summary>
    private readonly InMemoryVectorStoreVectorResolver<TRecord> _vectorResolver;

    /// <summary>An function to look up keys from the records.</summary>
    private readonly InMemoryVectorStoreKeyResolver<TKey, TRecord> _keyResolver;

    private static readonly VectorStoreRecordModelBuildingOptions s_validationOptions = new()
    {
        RequiresAtLeastOneVector = false,
        SupportsMultipleKeys = false,
        SupportsMultipleVectors = true,

        // Disable property type validation
        SupportedKeyPropertyTypes = null,
        SupportedDataPropertyTypes = null,
        SupportedEnumerableDataPropertyElementTypes = null,
        SupportedVectorPropertyTypes = [typeof(ReadOnlyMemory<float>)]
    };

    /// <summary>
    /// Initializes a new instance of the <see cref="InMemoryVectorStoreRecordCollection{TKey,TRecord}"/> class.
    /// </summary>
    /// <param name="name">The name of the collection that this <see cref="InMemoryVectorStoreRecordCollection{TKey,TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public InMemoryVectorStoreRecordCollection(string name, InMemoryVectorStoreRecordCollectionOptions<TKey, TRecord>? options = default)
    {
        // Verify.
        Verify.NotNullOrWhiteSpace(name);

        // Assign.
        this._collectionName = name;
        this._internalCollections = new();
        this._internalCollectionTypes = new();
        this._options = options ?? new InMemoryVectorStoreRecordCollectionOptions<TKey, TRecord>();

        this._model = new VectorStoreRecordModelBuilder(s_validationOptions)
            .Build(typeof(TRecord), this._options.VectorStoreRecordDefinition);

        // Assign resolvers.
        // TODO: Make generic to avoid boxing
#pragma warning disable MEVD9000 // KeyResolver and VectorResolver are experimental
        this._keyResolver = this._options.KeyResolver is null
            ? record => (TKey)this._model.KeyProperty.GetValueAsObject(record)!
            : this._options.KeyResolver;

        this._vectorResolver = this._options.VectorResolver is not null
            ? this._options.VectorResolver
            : (vectorPropertyName, record) =>
            {
                if (!this._model.PropertyMap.TryGetValue(vectorPropertyName, out var property))
                {
                    throw new InvalidOperationException($"The collection does not have a vector field named '{vectorPropertyName}', so vector search is not possible.");
                }

                if (property is not VectorStoreRecordVectorPropertyModel vectorProperty)
                {
                    throw new InvalidOperationException($"The property '{vectorPropertyName}' isn't a vector property.");
                }

                return property.GetValueAsObject(record);
            };
#pragma warning restore MEVD9000 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

        this._collectionMetadata = new()
        {
            VectorStoreSystemName = InMemoryConstants.VectorStoreSystemName,
            CollectionName = name
        };
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="InMemoryVectorStoreRecordCollection{TKey,TRecord}"/> class.
    /// </summary>
    /// <param name="internalCollection">Internal storage for the record collection.</param>
    /// <param name="internalCollectionTypes">The data type of each collection, to enforce a single type per collection.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="InMemoryVectorStoreRecordCollection{TKey,TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    internal InMemoryVectorStoreRecordCollection(
        ConcurrentDictionary<string, ConcurrentDictionary<object, object>> internalCollection,
        ConcurrentDictionary<string, Type> internalCollectionTypes,
        string collectionName,
        InMemoryVectorStoreRecordCollectionOptions<TKey, TRecord>? options = default)
        : this(collectionName, options)
    {
        this._internalCollections = internalCollection;
        this._internalCollectionTypes = internalCollectionTypes;
    }

    /// <inheritdoc />
    public string Name => this._collectionName;

    /// <inheritdoc />
    public Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        return this._internalCollections.ContainsKey(this._collectionName) ? Task.FromResult(true) : Task.FromResult(false);
    }

    /// <inheritdoc />
    public Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        if (!this._internalCollections.ContainsKey(this._collectionName)
            && this._internalCollections.TryAdd(this._collectionName, new ConcurrentDictionary<object, object>())
            && this._internalCollectionTypes.TryAdd(this._collectionName, typeof(TRecord)))
        {
            return Task.CompletedTask;
        }

        return Task.FromException(new VectorStoreOperationException("Collection already exists.")
        {
            VectorStoreSystemName = InMemoryConstants.VectorStoreSystemName,
            CollectionName = this.Name,
            OperationName = "CreateCollection"
        });
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
        this._internalCollections.TryRemove(this._collectionName, out _);
        this._internalCollectionTypes.TryRemove(this._collectionName, out _);
        return Task.CompletedTask;
    }

    /// <inheritdoc />
    public Task<TRecord?> GetAsync(TKey key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        var collectionDictionary = this.GetCollectionDictionary();

        if (collectionDictionary.TryGetValue(key, out var record))
        {
            return Task.FromResult<TRecord?>((TRecord?)record);
        }

        return Task.FromResult<TRecord?>(default);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetAsync(IEnumerable<TKey> keys, GetRecordOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

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
    public Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        var collectionDictionary = this.GetCollectionDictionary();

        collectionDictionary.TryRemove(key, out _);
        return Task.CompletedTask;
    }

    /// <inheritdoc />
    public Task DeleteAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        var collectionDictionary = this.GetCollectionDictionary();

        foreach (var key in keys)
        {
            collectionDictionary.TryRemove(key, out _);
        }

        return Task.CompletedTask;
    }

    /// <inheritdoc />
    public Task<TKey> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
        => Task.FromResult(this.Upsert(record));

    /// <inheritdoc />
    public Task<IReadOnlyList<TKey>> UpsertAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        return Task.FromResult<IReadOnlyList<TKey>>(records.Select(this.Upsert).ToList());
    }

    private TKey Upsert(TRecord record)
    {
        Verify.NotNull(record);

        var collectionDictionary = this.GetCollectionDictionary();

        var key = (TKey)this._keyResolver(record)!;
        collectionDictionary.AddOrUpdate(key!, record, (key, currentValue) => record);

        return key!;
    }

    /// <inheritdoc />
    public IAsyncEnumerable<VectorSearchResult<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, int top, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(vector);
        Verify.NotLessThan(top, 1);

        if (vector is not ReadOnlyMemory<float> floatVector)
        {
            throw new NotSupportedException($"The provided vector type {vector.GetType().FullName} is not supported by the InMemory Vector Store.");
        }

        // Resolve options and get requested vector property or first as default.
        var internalOptions = options ?? s_defaultVectorSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle(internalOptions);

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
        // Filter records using the provided filter before doing the vector comparison.
        var allValues = this.GetCollectionDictionary().Values.Cast<TRecord>();
        var filteredRecords = internalOptions switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => InMemoryVectorStoreCollectionSearchMapping.FilterRecords(legacyFilter, allValues),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => allValues.AsQueryable().Where(newFilter),
            _ => allValues
        };
#pragma warning restore CS0618 // VectorSearchFilter is obsolete

        // Compare each vector in the filtered results with the provided vector.
        var results = filteredRecords.Select<TRecord, (TRecord record, float score)?>(record =>
        {
            var vectorObject = this._vectorResolver(vectorProperty.ModelName!, record);
            if (vectorObject is not ReadOnlyMemory<float> dbVector)
            {
                return null;
            }

            var score = InMemoryVectorStoreCollectionSearchMapping.CompareVectors(floatVector.Span, dbVector.Span, vectorProperty.DistanceFunction);
            var convertedscore = InMemoryVectorStoreCollectionSearchMapping.ConvertScore(score, vectorProperty.DistanceFunction);
            return (record, convertedscore);
        });

        // Get the non-null results since any record with a null vector results in a null result.
        var nonNullResults = results.Where(x => x.HasValue).Select(x => x!.Value);

        // Sort the results appropriately for the selected distance function and get the right page of results .
        var sortedScoredResults = InMemoryVectorStoreCollectionSearchMapping.ShouldSortDescending(vectorProperty.DistanceFunction) ?
            nonNullResults.OrderByDescending(x => x.score) :
            nonNullResults.OrderBy(x => x.score);
        var resultsPage = sortedScoredResults.Skip(internalOptions.Skip).Take(top);

        // Build the response.
        return resultsPage.Select(x => new VectorSearchResult<TRecord>((TRecord)x.record, x.score)).ToAsyncEnumerable();
    }

    /// <inheritdoc />
    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreRecordCollectionMetadata) ? this._collectionMetadata :
            serviceType == typeof(ConcurrentDictionary<string, ConcurrentDictionary<object, object>>) ? this._internalCollections :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }

    /// <inheritdoc />
    public IAsyncEnumerable<TRecord> GetAsync(Expression<Func<TRecord, bool>> filter, int top,
        GetFilteredRecordOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(filter);
        Verify.NotLessThan(top, 1);

        options ??= new();

        var records = this.GetCollectionDictionary().Values.Cast<TRecord>()
            .AsQueryable()
            .Where(filter);

        if (options.OrderBy.Values.Count > 0)
        {
            var first = options.OrderBy.Values[0];
            var sorted = first.Ascending
                    ? records.OrderBy(first.PropertySelector)
                    : records.OrderByDescending(first.PropertySelector);

            for (int i = 1; i < options.OrderBy.Values.Count; i++)
            {
                var next = options.OrderBy.Values[i];
                sorted = next.Ascending
                    ? sorted.ThenBy(next.PropertySelector)
                    : sorted.ThenByDescending(next.PropertySelector);
            }

            records = sorted;
        }

        return records
            .Skip(options.Skip)
            .Take(top)
            .ToAsyncEnumerable();
    }

    /// <summary>
    /// Get the collection dictionary from the internal storage, throws if it does not exist.
    /// </summary>
    /// <returns>The retrieved collection dictionary.</returns>
    internal ConcurrentDictionary<object, object> GetCollectionDictionary()
    {
        if (!this._internalCollections.TryGetValue(this._collectionName, out var collectionDictionary))
        {
            throw new VectorStoreOperationException($"Call to vector store failed. Collection '{this._collectionName}' does not exist.");
        }

        return collectionDictionary;
    }
}
