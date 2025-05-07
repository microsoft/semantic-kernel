// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Linq.Expressions;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.InMemory;

/// <summary>
/// Service for storing and retrieving vector records, that uses an in memory dictionary as the underlying storage.
/// </summary>
/// <typeparam name="TKey">The data type of the record key.</typeparam>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class InMemoryCollection<TKey, TRecord> : VectorStoreCollection<TKey, TRecord>
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
    where TKey : notnull
    where TRecord : class
{
    /// <summary>Metadata about vector store record collection.</summary>
    private readonly VectorStoreCollectionMetadata _collectionMetadata;

    /// <summary>The default options for vector search.</summary>
    private static readonly RecordSearchOptions<TRecord> s_defaultVectorSearchOptions = new();

    /// <summary>Internal storage for all of the record collections.</summary>
    private readonly ConcurrentDictionary<string, ConcurrentDictionary<object, object>> _internalCollections;

    /// <summary>The data type of each collection, to enforce a single type per collection.</summary>
    private readonly ConcurrentDictionary<string, Type> _internalCollectionTypes;

    /// <summary>The model for this collection.</summary>
    private readonly CollectionModel _model;

    /// <summary>
    /// Initializes a new instance of the <see cref="InMemoryCollection{TKey,TRecord}"/> class.
    /// </summary>
    /// <param name="name">The name of the collection that this <see cref="InMemoryCollection{TKey,TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public InMemoryCollection(string name, InMemoryCollectionOptions<TKey, TRecord>? options = default)
    {
        // Verify.
        Verify.NotNullOrWhiteSpace(name);

        // Assign.
        this.Name = name;
        this._internalCollections = new();
        this._internalCollectionTypes = new();
        options ??= new InMemoryCollectionOptions<TKey, TRecord>();

        this._model = new InMemoryModelBuilder()
            .Build(typeof(TRecord), options.VectorStoreRecordDefinition, options.EmbeddingGenerator);

        this._collectionMetadata = new()
        {
            VectorStoreSystemName = InMemoryConstants.VectorStoreSystemName,
            CollectionName = name
        };
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="InMemoryCollection{TKey,TRecord}"/> class.
    /// </summary>
    /// <param name="internalCollection">Internal storage for the record collection.</param>
    /// <param name="internalCollectionTypes">The data type of each collection, to enforce a single type per collection.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="InMemoryCollection{TKey,TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    internal InMemoryCollection(
        ConcurrentDictionary<string, ConcurrentDictionary<object, object>> internalCollection,
        ConcurrentDictionary<string, Type> internalCollectionTypes,
        string collectionName,
        InMemoryCollectionOptions<TKey, TRecord>? options = default)
        : this(collectionName, options)
    {
        this._internalCollections = internalCollection;
        this._internalCollectionTypes = internalCollectionTypes;
    }

    /// <inheritdoc />
    public override string Name { get; }

    /// <inheritdoc />
    public override Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        return this._internalCollections.ContainsKey(this.Name) ? Task.FromResult(true) : Task.FromResult(false);
    }

    /// <inheritdoc />
    public override Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        if (!this._internalCollections.ContainsKey(this.Name)
            && this._internalCollections.TryAdd(this.Name, new ConcurrentDictionary<object, object>())
            && this._internalCollectionTypes.TryAdd(this.Name, typeof(TRecord)))
        {
            return Task.CompletedTask;
        }

        return Task.FromException(new VectorStoreException("Collection already exists.")
        {
            VectorStoreSystemName = InMemoryConstants.VectorStoreSystemName,
            CollectionName = this.Name,
            OperationName = "CreateCollection"
        });
    }

    /// <inheritdoc />
    public override async Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
    {
        if (!await this.CollectionExistsAsync(cancellationToken).ConfigureAwait(false))
        {
            await this.CreateCollectionAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc />
    public override Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
    {
        this._internalCollections.TryRemove(this.Name, out _);
        this._internalCollectionTypes.TryRemove(this.Name, out _);
        return Task.CompletedTask;
    }

    /// <inheritdoc />
    public override Task<TRecord?> GetAsync(TKey key, RecordRetrievalOptions? options = null, CancellationToken cancellationToken = default)
    {
        if (options?.IncludeVectors == true && this._model.VectorProperties.Any(p => p.EmbeddingGenerator is not null))
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        var collectionDictionary = this.GetCollectionDictionary();

        if (collectionDictionary.TryGetValue(key, out var record))
        {
            return Task.FromResult<TRecord?>(((InMemoryRecordWrapper<TRecord>)record).Record);
        }

        return Task.FromResult<TRecord?>(default);
    }

    /// <inheritdoc />
    public override Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        var collectionDictionary = this.GetCollectionDictionary();

        collectionDictionary.TryRemove(key, out _);
        return Task.CompletedTask;
    }

    /// <inheritdoc />
    public override Task UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
        => this.UpsertAsync([record], cancellationToken);

    /// <inheritdoc />
    public override async Task UpsertAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        IReadOnlyList<TRecord>? recordsList = null;

        // If an embedding generator is defined, invoke it once per property for all records.
        IReadOnlyList<Embedding>?[]? generatedEmbeddings = null;

        var vectorPropertyCount = this._model.VectorProperties.Count;
        for (var i = 0; i < vectorPropertyCount; i++)
        {
            var vectorProperty = this._model.VectorProperties[i];

            if (vectorProperty.EmbeddingGenerator is null)
            {
                continue;
            }

            // We have a property with embedding generation; materialize the records' enumerable if needed, to
            // prevent multiple enumeration.
            if (recordsList is null)
            {
                recordsList = records is IReadOnlyList<TRecord> r ? r : records.ToList();

                if (recordsList.Count == 0)
                {
                    return;
                }

                records = recordsList;
            }

            // TODO: Ideally we'd group together vector properties using the same generator (and with the same input and output properties),
            // and generate embeddings for them in a single batch. That's some more complexity though.
            if (vectorProperty.TryGenerateEmbeddings<TRecord, Embedding<float>, ReadOnlyMemory<float>>(records, cancellationToken, out var floatTask))
            {
                generatedEmbeddings ??= new IReadOnlyList<Embedding>?[vectorPropertyCount];
                generatedEmbeddings[i] = (IReadOnlyList<Embedding<float>>)await floatTask.ConfigureAwait(false);
            }
            else
            {
                throw new InvalidOperationException(
                    $"The embedding generator configured on property '{vectorProperty.ModelName}' cannot produce an embedding of type '{typeof(Embedding<float>).Name}' for the given input type.");
            }
        }

        var collectionDictionary = this.GetCollectionDictionary();

        var recordIndex = 0;
        foreach (var record in records)
        {
            var key = (TKey)this._model.KeyProperty.GetValueAsObject(record)!;
            var wrappedRecord = new InMemoryRecordWrapper<TRecord>(record);

            if (generatedEmbeddings is not null)
            {
                for (var i = 0; i < this._model.VectorProperties.Count; i++)
                {
                    if (generatedEmbeddings![i] is IReadOnlyList<Embedding> propertyEmbeddings)
                    {
                        var property = this._model.VectorProperties[i];

                        wrappedRecord.EmbeddingGeneratedVectors[property.ModelName] = propertyEmbeddings[recordIndex] switch
                        {
                            Embedding<float> e => e.Vector,
                            _ => throw new UnreachableException()
                        };
                    }
                }
            }

            collectionDictionary.AddOrUpdate(key!, wrappedRecord, (key, currentValue) => wrappedRecord);

            recordIndex++;
        }
    }

    #region Search

    /// <inheritdoc />
    public override async IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TInput>(
        TInput value,
        int top,
        RecordSearchOptions<TRecord>? options = default,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        options ??= s_defaultVectorSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle(options);

        switch (vectorProperty.EmbeddingGenerator)
        {
            case IEmbeddingGenerator<TInput, Embedding<float>> generator:
            {
                var embedding = await generator.GenerateEmbeddingAsync(value, new() { Dimensions = vectorProperty.Dimensions }, cancellationToken).ConfigureAwait(false);

                await foreach (var record in this.SearchCoreAsync(embedding.Vector, top, vectorProperty, operationName: "Search", options, cancellationToken).ConfigureAwait(false))
                {
                    yield return record;
                }

                yield break;
            }

            case null:
                throw new InvalidOperationException(VectorDataStrings.NoEmbeddingGeneratorWasConfiguredForSearch);

            default:
                throw new InvalidOperationException(
                    InMemoryModelBuilder.ValidationOptions.SupportedVectorPropertyTypes.Contains(typeof(TInput))
                        ? VectorDataStrings.EmbeddingTypePassedToSearchAsync
                        : VectorDataStrings.IncompatibleEmbeddingGeneratorWasConfiguredForInputType(typeof(TInput), vectorProperty.EmbeddingGenerator.GetType()));
        }
    }

    /// <inheritdoc />
    public override IAsyncEnumerable<VectorSearchResult<TRecord>> SearchEmbeddingAsync<TVector>(
        TVector vector,
        int top,
        RecordSearchOptions<TRecord>? options = null,
        CancellationToken cancellationToken = default)
    {
        options ??= s_defaultVectorSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle(options);

        return this.SearchCoreAsync(vector, top, vectorProperty, operationName: "SearchEmbedding", options, cancellationToken);
    }

    private IAsyncEnumerable<VectorSearchResult<TRecord>> SearchCoreAsync<TVector>(
        TVector vector,
        int top,
        VectorPropertyModel vectorProperty,
        string operationName,
        RecordSearchOptions<TRecord> options,
        CancellationToken cancellationToken = default)
        where TVector : notnull
    {
        Verify.NotNull(vector);
        Verify.NotLessThan(top, 1);

        if (vector is not ReadOnlyMemory<float> floatVector)
        {
            throw new NotSupportedException($"The provided vector type {vector.GetType().FullName} is not supported by the InMemory Vector Store.");
        }

        if (options.IncludeVectors && this._model.VectorProperties.Any(p => p.EmbeddingGenerator is not null))
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
        // Filter records using the provided filter before doing the vector comparison.
        var allValues = this.GetCollectionDictionary().Values.Cast<InMemoryRecordWrapper<TRecord>>();
        var filteredRecords = options switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => InMemoryCollectionSearchMapping.FilterRecords(legacyFilter, allValues),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => allValues.AsQueryable().Where(this.ConvertFilter(newFilter)),
            _ => allValues
        };
#pragma warning restore CS0618 // VectorSearchFilter is obsolete

        // Compare each vector in the filtered results with the provided vector.
        var results = filteredRecords.Select<InMemoryRecordWrapper<TRecord>, (TRecord record, float score)?>(wrapper =>
        {
            ReadOnlyMemory<float> vector;

            if (vectorProperty.EmbeddingGenerator is null)
            {
                if (vectorProperty.GetValueAsObject(wrapper.Record) is not ReadOnlyMemory<float> dbVector)
                {
                    return null;
                }
                vector = dbVector;
            }
            else
            {
                vector = wrapper.EmbeddingGeneratedVectors[vectorProperty.ModelName];
            }

            var score = InMemoryCollectionSearchMapping.CompareVectors(floatVector.Span, vector.Span, vectorProperty.DistanceFunction);
            var convertedscore = InMemoryCollectionSearchMapping.ConvertScore(score, vectorProperty.DistanceFunction);
            return (wrapper.Record, convertedscore);
        });

        // Get the non-null results since any record with a null vector results in a null result.
        var nonNullResults = results.Where(x => x.HasValue).Select(x => x!.Value);

        // Sort the results appropriately for the selected distance function and get the right page of results .
        var sortedScoredResults = InMemoryCollectionSearchMapping.ShouldSortDescending(vectorProperty.DistanceFunction) ?
            nonNullResults.OrderByDescending(x => x.score) :
            nonNullResults.OrderBy(x => x.score);
        var resultsPage = sortedScoredResults.Skip(options.Skip).Take(top);

        // Build the response.
        return resultsPage.Select(x => new VectorSearchResult<TRecord>((TRecord)x.record, x.score)).ToAsyncEnumerable();
    }

    #endregion Search

    /// <inheritdoc />
    public override object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreCollectionMetadata) ? this._collectionMetadata :
            serviceType == typeof(ConcurrentDictionary<string, ConcurrentDictionary<object, object>>) ? this._internalCollections :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }

    /// <inheritdoc />
    public override IAsyncEnumerable<TRecord> GetAsync(Expression<Func<TRecord, bool>> filter, int top,
        FilteredRecordRetrievalOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(filter);
        Verify.NotLessThan(top, 1);

        options ??= new();

        if (options.IncludeVectors && this._model.VectorProperties.Any(p => p.EmbeddingGenerator is not null))
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        var records = this.GetCollectionDictionary()
            .Values
            .Cast<InMemoryRecordWrapper<TRecord>>()
            .Select(x => x.Record)
            .AsQueryable()
            .Where(filter);

        var orderBy = options.OrderBy?.Invoke(new()).Values;
        if (orderBy is { Count: > 0 })
        {
            var first = orderBy[0];
            var sorted = first.Ascending
                    ? records.OrderBy(first.PropertySelector)
                    : records.OrderByDescending(first.PropertySelector);

            for (int i = 1; i < orderBy.Count; i++)
            {
                var next = orderBy[i];
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
        if (!this._internalCollections.TryGetValue(this.Name, out var collectionDictionary))
        {
            throw new VectorStoreException($"Call to vector store failed. Collection '{this.Name}' does not exist.");
        }

        return collectionDictionary;
    }

    /// <summary>
    /// The user provides a filter expression accepting a Record, but we internally store it wrapped in an InMemoryVectorRecordWrapper.
    /// This method converts a filter expression accepting a Record to one accepting an InMemoryVectorRecordWrapper.
    /// </summary>
    private Expression<Func<InMemoryRecordWrapper<TRecord>, bool>> ConvertFilter(Expression<Func<TRecord, bool>> recordFilter)
    {
        var wrapperParameter = Expression.Parameter(typeof(InMemoryRecordWrapper<TRecord>), "w");
        var replacement = Expression.Property(wrapperParameter, nameof(InMemoryRecordWrapper<TRecord>.Record));

        return Expression.Lambda<Func<InMemoryRecordWrapper<TRecord>, bool>>(
            new ParameterReplacer(recordFilter.Parameters.Single(), replacement).Visit(recordFilter.Body),
            wrapperParameter);
    }

    private sealed class ParameterReplacer(ParameterExpression originalRecordParameter, Expression replacementExpression) : ExpressionVisitor
    {
        protected override Expression VisitParameter(ParameterExpression node)
            => node == originalRecordParameter ? replacementExpression : base.VisitParameter(node);
    }
}
