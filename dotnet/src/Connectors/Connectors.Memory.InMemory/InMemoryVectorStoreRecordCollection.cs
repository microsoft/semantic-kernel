// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;

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
{
    /// <summary>A set of types that vectors on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedVectorTypes =
    [
        typeof(ReadOnlyMemory<float>),
        typeof(ReadOnlyMemory<float>?),
    ];

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

    /// <summary>A helper to access property information for the current data model and record definition.</summary>
    private readonly VectorStoreRecordPropertyReader _propertyReader;

    /// <summary>A dictionary of vector properties on the provided model, keyed by the property name.</summary>
    private readonly Dictionary<string, VectorStoreRecordVectorProperty> _vectorProperties;

    /// <summary>An function to look up vectors from the records.</summary>
    private readonly InMemoryVectorStoreVectorResolver<TRecord> _vectorResolver;

    /// <summary>An function to look up keys from the records.</summary>
    private readonly InMemoryVectorStoreKeyResolver<TKey, TRecord> _keyResolver;

    /// <summary>
    /// Initializes a new instance of the <see cref="InMemoryVectorStoreRecordCollection{TKey,TRecord}"/> class.
    /// </summary>
    /// <param name="collectionName">The name of the collection that this <see cref="InMemoryVectorStoreRecordCollection{TKey,TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public InMemoryVectorStoreRecordCollection(string collectionName, InMemoryVectorStoreRecordCollectionOptions<TKey, TRecord>? options = default)
    {
        // Verify.
        Verify.NotNullOrWhiteSpace(collectionName);
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelDefinitionSupplied(typeof(TRecord), options?.VectorStoreRecordDefinition is not null);

        // Assign.
        this._collectionName = collectionName;
        this._internalCollections = new();
        this._internalCollectionTypes = new();
        this._options = options ?? new InMemoryVectorStoreRecordCollectionOptions<TKey, TRecord>();
        this._propertyReader = new VectorStoreRecordPropertyReader(typeof(TRecord), this._options.VectorStoreRecordDefinition, new() { RequiresAtLeastOneVector = false, SupportsMultipleKeys = false, SupportsMultipleVectors = true });

        // Validate property types.
        this._propertyReader.VerifyVectorProperties(s_supportedVectorTypes);
        this._vectorProperties = this._propertyReader.VectorProperties.ToDictionary(x => x.DataModelPropertyName);

        // Assign resolvers.
        this._vectorResolver = CreateVectorResolver(this._options.VectorResolver, this._vectorProperties);
        this._keyResolver = CreateKeyResolver(this._options.KeyResolver, this._propertyReader.KeyProperty);
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
    public string CollectionName => this._collectionName;

    /// <inheritdoc />
    public Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        return this._internalCollections.ContainsKey(this._collectionName) ? Task.FromResult(true) : Task.FromResult(false);
    }

    /// <inheritdoc />
    public Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        if (!this._internalCollections.ContainsKey(this._collectionName))
        {
            this._internalCollections.TryAdd(this._collectionName, new ConcurrentDictionary<object, object>());
            this._internalCollectionTypes.TryAdd(this._collectionName, typeof(TRecord));
        }

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
        this._internalCollections.TryRemove(this._collectionName, out _);
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
    public Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        var collectionDictionary = this.GetCollectionDictionary();

        collectionDictionary.TryRemove(key, out _);
        return Task.CompletedTask;
    }

    /// <inheritdoc />
    public Task DeleteBatchAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
    {
        var collectionDictionary = this.GetCollectionDictionary();

        foreach (var key in keys)
        {
            collectionDictionary.TryRemove(key, out _);
        }

        return Task.CompletedTask;
    }

    /// <inheritdoc />
    public Task<TKey> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        var collectionDictionary = this.GetCollectionDictionary();

        var key = (TKey)this._keyResolver(record)!;
        collectionDictionary.AddOrUpdate(key!, record, (key, currentValue) => record);

        return Task.FromResult(key!);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TKey> UpsertBatchAsync(IEnumerable<TRecord> records, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        foreach (var record in records)
        {
            yield return await this.UpsertAsync(record, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc />
#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously - Need to satisfy the interface which returns IAsyncEnumerable
    public async Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
#pragma warning restore CS1998
    {
        Verify.NotNull(vector);

        if (vector is not ReadOnlyMemory<float> floatVector)
        {
            throw new NotSupportedException($"The provided vector type {vector.GetType().FullName} is not supported by the InMemory Vector Store.");
        }

        // Resolve options and get requested vector property or first as default.
        var internalOptions = options ?? s_defaultVectorSearchOptions;
        var vectorProperty = this._propertyReader.GetVectorPropertyOrSingle(internalOptions);

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
            var vectorObject = this._vectorResolver(vectorProperty.DataModelPropertyName!, record);
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

        // Calculate the total results count if requested.
        long? count = null;
        if (internalOptions.IncludeTotalCount)
        {
            count = nonNullResults.Count();
        }

        // Sort the results appropriately for the selected distance function and get the right page of results .
        var sortedScoredResults = InMemoryVectorStoreCollectionSearchMapping.ShouldSortDescending(vectorProperty.DistanceFunction) ?
            nonNullResults.OrderByDescending(x => x.score) :
            nonNullResults.OrderBy(x => x.score);
        var resultsPage = sortedScoredResults.Skip(internalOptions.Skip).Take(internalOptions.Top);

        // Build the response.
        var vectorSearchResultList = resultsPage.Select(x => new VectorSearchResult<TRecord>((TRecord)x.record, x.score)).ToAsyncEnumerable();
        return new VectorSearchResults<TRecord>(vectorSearchResultList) { TotalCount = count };
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

    /// <summary>
    /// Pick / create a vector resolver that will read a vector from a record in the store based on the vector name.
    /// 1. If an override resolver is provided, use that.
    /// 2. If the record type is <see cref="VectorStoreGenericDataModel{TKey}"/> create a resolver that looks up the vector in its <see cref="VectorStoreGenericDataModel{TKey}.Vectors"/> dictionary.
    /// 3. Otherwise, create a resolver that assumes the vector is a property directly on the record and use the record definition to determine the name.
    /// </summary>
    /// <param name="overrideVectorResolver">The override vector resolver if one was provided.</param>
    /// <param name="vectorProperties">A dictionary of vector properties from the record definition.</param>
    /// <returns>The <see cref="InMemoryVectorStoreVectorResolver{TRecord}"/>.</returns>
    private static InMemoryVectorStoreVectorResolver<TRecord> CreateVectorResolver(InMemoryVectorStoreVectorResolver<TRecord>? overrideVectorResolver, Dictionary<string, VectorStoreRecordVectorProperty> vectorProperties)
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
    /// <returns>The <see cref="InMemoryVectorStoreKeyResolver{TKey, TRecord}"/>.</returns>
    private static InMemoryVectorStoreKeyResolver<TKey, TRecord> CreateKeyResolver(InMemoryVectorStoreKeyResolver<TKey, TRecord>? overrideKeyResolver, VectorStoreRecordKeyProperty keyProperty)
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
}
