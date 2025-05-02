// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Linq.Expressions;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Grpc.Core;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Microsoft.Extensions.VectorData.Properties;
using Qdrant.Client;
using Qdrant.Client.Grpc;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// Service for storing and retrieving vector records, that uses Qdrant as the underlying storage.
/// </summary>
/// <typeparam name="TKey">The data type of the record key. Can be either <see cref="Guid"/> or <see cref="ulong"/>, or <see cref="object"/> for dynamic mapping.</typeparam>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class QdrantVectorStoreRecordCollection<TKey, TRecord> : IVectorStoreRecordCollection<TKey, TRecord>, IKeywordHybridSearch<TRecord>
    where TKey : notnull
    where TRecord : notnull
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    /// <summary>Metadata about vector store record collection.</summary>
    private readonly VectorStoreRecordCollectionMetadata _collectionMetadata;

    /// <summary>The default options for vector search.</summary>
    private static readonly VectorSearchOptions<TRecord> s_defaultVectorSearchOptions = new();

    /// <summary>The default options for hybrid vector search.</summary>
    private static readonly HybridSearchOptions<TRecord> s_defaultKeywordVectorizedHybridSearchOptions = new();

    /// <summary>The name of the upsert operation for telemetry purposes.</summary>
    private const string UpsertName = "Upsert";

    /// <summary>The name of the Delete operation for telemetry purposes.</summary>
    private const string DeleteName = "Delete";

    /// <summary>Qdrant client that can be used to manage the collections and points in a Qdrant store.</summary>
    private readonly MockableQdrantClient _qdrantClient;

    /// <summary>The name of the collection that this <see cref="QdrantVectorStoreRecordCollection{TKey, TRecord}"/> will access.</summary>
    private readonly string _collectionName;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly QdrantVectorStoreRecordCollectionOptions<TRecord> _options;

    /// <summary>The model for this collection.</summary>
    private readonly VectorStoreRecordModel _model;

    /// <summary>A mapper to use for converting between qdrant point and consumer models.</summary>
    private readonly QdrantVectorStoreRecordMapper<TRecord> _mapper;

    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantVectorStoreRecordCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="qdrantClient">Qdrant client that can be used to manage the collections and points in a Qdrant store.</param>
    /// <param name="name">The name of the collection that this <see cref="QdrantVectorStoreRecordCollection{TKey, TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    /// <exception cref="ArgumentNullException">Thrown if the <paramref name="qdrantClient"/> is null.</exception>
    /// <exception cref="ArgumentException">Thrown for any misconfigured options.</exception>
    public QdrantVectorStoreRecordCollection(QdrantClient qdrantClient, string name, QdrantVectorStoreRecordCollectionOptions<TRecord>? options = null)
        : this(new MockableQdrantClient(qdrantClient), name, options)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantVectorStoreRecordCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="qdrantClient">Qdrant client that can be used to manage the collections and points in a Qdrant store.</param>
    /// <param name="name">The name of the collection that this <see cref="QdrantVectorStoreRecordCollection{TKey, TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    /// <exception cref="ArgumentNullException">Thrown if the <paramref name="qdrantClient"/> is null.</exception>
    /// <exception cref="ArgumentException">Thrown for any misconfigured options.</exception>
    internal QdrantVectorStoreRecordCollection(MockableQdrantClient qdrantClient, string name, QdrantVectorStoreRecordCollectionOptions<TRecord>? options = null)
    {
        // Verify.
        Verify.NotNull(qdrantClient);
        Verify.NotNullOrWhiteSpace(name);

        if (typeof(TKey) != typeof(ulong) && typeof(TKey) != typeof(Guid) && typeof(TKey) != typeof(object))
        {
            throw new NotSupportedException("Only ulong and Guid keys are supported (and object for dynamic mapping).");
        }

        // Assign.
        this._qdrantClient = qdrantClient;
        this._collectionName = name;
        this._options = options ?? new QdrantVectorStoreRecordCollectionOptions<TRecord>();

        this._model = new VectorStoreRecordModelBuilder(QdrantVectorStoreRecordFieldMapping.GetModelBuildOptions(this._options.HasNamedVectors))
            .Build(typeof(TRecord), this._options.VectorStoreRecordDefinition, options?.EmbeddingGenerator);

        this._mapper = new QdrantVectorStoreRecordMapper<TRecord>(this._model, this._options.HasNamedVectors);

        this._collectionMetadata = new()
        {
            VectorStoreSystemName = QdrantConstants.VectorStoreSystemName,
            CollectionName = name
        };
    }

    /// <inheritdoc />
    public string Name => this._collectionName;

    /// <inheritdoc />
    public Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        return this.RunOperationAsync(
            "CollectionExists",
            () => this._qdrantClient.CollectionExistsAsync(this._collectionName, cancellationToken));
    }

    /// <inheritdoc />
    public async Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        if (!this._options.HasNamedVectors)
        {
            // If we are not using named vectors, we can only have one vector property. We can assume we have exactly one, since this is already verified in the constructor.
            var singleVectorProperty = this._model.VectorProperty;

            // Map the single vector property to the qdrant config.
            var vectorParams = QdrantVectorStoreCollectionCreateMapping.MapSingleVector(singleVectorProperty!);

            // Create the collection with the single unnamed vector.
            await this.RunOperationAsync(
                "CreateCollection",
                () => this._qdrantClient.CreateCollectionAsync(
                    this._collectionName,
                    vectorParams,
                    cancellationToken: cancellationToken)).ConfigureAwait(false);
        }
        else
        {
            // Since we are using named vectors, iterate over all vector properties.
            var vectorProperties = this._model.VectorProperties;

            // Map the named vectors to the qdrant config.
            var vectorParamsMap = QdrantVectorStoreCollectionCreateMapping.MapNamedVectors(vectorProperties);

            // Create the collection with named vectors.
            await this.RunOperationAsync(
                "CreateCollection",
                () => this._qdrantClient.CreateCollectionAsync(
                    this._collectionName,
                    vectorParamsMap,
                    cancellationToken: cancellationToken)).ConfigureAwait(false);
        }

        // Add indexes for each of the data properties that require filtering.
        var dataProperties = this._model.DataProperties.Where(x => x.IsIndexed);
        foreach (var dataProperty in dataProperties)
        {
            if (QdrantVectorStoreCollectionCreateMapping.s_schemaTypeMap.TryGetValue(dataProperty.Type, out PayloadSchemaType schemaType))
            {
                // Do nothing since schemaType is already set.
            }
            else if (VectorStoreRecordPropertyVerification.IsSupportedEnumerableType(dataProperty.Type) && VectorStoreRecordPropertyVerification.GetCollectionElementType(dataProperty.Type) == typeof(string))
            {
                // For enumerable of strings, use keyword schema type, since this allows tag filtering.
                schemaType = PayloadSchemaType.Keyword;
            }
            else
            {
                // TODO: This should move to model validation
                throw new InvalidOperationException($"Property {nameof(VectorStoreRecordDataProperty.IsIndexed)} on {nameof(VectorStoreRecordDataProperty)} '{dataProperty.ModelName}' is set to true, but the property type is not supported for filtering. The Qdrant VectorStore supports filtering on {string.Join(", ", QdrantVectorStoreCollectionCreateMapping.s_schemaTypeMap.Keys.Select(x => x.Name))} properties only.");
            }

            await this.RunOperationAsync(
                "CreatePayloadIndex",
                () => this._qdrantClient.CreatePayloadIndexAsync(
                    this._collectionName,
                    dataProperty.StorageName,
                    schemaType,
                    cancellationToken: cancellationToken)).ConfigureAwait(false);
        }

        // Add indexes for each of the data properties that require full text search.
        dataProperties = this._model.DataProperties.Where(x => x.IsFullTextIndexed);
        foreach (var dataProperty in dataProperties)
        {
            // TODO: This should move to model validation
            if (dataProperty.Type != typeof(string))
            {
                throw new InvalidOperationException($"Property {nameof(dataProperty.IsFullTextIndexed)} on {nameof(VectorStoreRecordDataProperty)} '{dataProperty.ModelName}' is set to true, but the property type is not a string. The Qdrant VectorStore supports {nameof(dataProperty.IsFullTextIndexed)} on string properties only.");
            }

            await this.RunOperationAsync(
                "CreatePayloadIndex",
                () => this._qdrantClient.CreatePayloadIndexAsync(
                    this._collectionName,
                    dataProperty.StorageName,
                    PayloadSchemaType.Text,
                    cancellationToken: cancellationToken)).ConfigureAwait(false);
        }
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
        => this.RunOperationAsync("DeleteCollection",
            async () =>
            {
                try
                {
                    await this._qdrantClient.DeleteCollectionAsync(this._collectionName, null, cancellationToken).ConfigureAwait(false);
                }
                catch (QdrantException)
                {
                    // There is no reliable way to check if the operation failed because the
                    // collection does not exist based on the exception itself.
                    // So we just check here if it exists, and if not, ignore the exception.
                    if (!await this.CollectionExistsAsync(cancellationToken).ConfigureAwait(false))
                    {
                        return;
                    }

                    throw;
                }
            });

    /// <inheritdoc />
    public async Task<TRecord?> GetAsync(TKey key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        var retrievedPoints = await this.GetAsync([key], options, cancellationToken).ToListAsync(cancellationToken).ConfigureAwait(false);
        return retrievedPoints.FirstOrDefault();
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetAsync(
        IEnumerable<TKey> keys,
        GetRecordOptions? options = default,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        const string OperationName = "Retrieve";

        Verify.NotNull(keys);

        // Create options.
        var pointsIds = new List<PointId>();

        Type? keyType = null;

        foreach (var key in keys)
        {
            switch (key)
            {
                case ulong id:
                    if (keyType == typeof(Guid))
                    {
                        throw new NotSupportedException("Mixing ulong and Guid keys is not supported");
                    }

                    keyType = typeof(ulong);
                    pointsIds.Add(new PointId { Num = id });
                    break;

                case Guid id:
                    if (keyType == typeof(ulong))
                    {
                        throw new NotSupportedException("Mixing ulong and Guid keys is not supported");
                    }

                    pointsIds.Add(new PointId { Uuid = id.ToString("D") });
                    keyType = typeof(Guid);
                    break;

                default:
                    throw new NotSupportedException($"The provided key type '{key.GetType().Name}' is not supported by Qdrant.");
            }
        }

        var includeVectors = options?.IncludeVectors ?? false;
        if (includeVectors && this._model.VectorProperties.Any(p => p.EmbeddingGenerator is not null))
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        // Retrieve data points.
        var retrievedPoints = await this.RunOperationAsync(
            OperationName,
            () => this._qdrantClient.RetrieveAsync(this._collectionName, pointsIds, true, includeVectors, cancellationToken: cancellationToken)).ConfigureAwait(false);

        // Convert the retrieved points to the target data model.
        foreach (var retrievedPoint in retrievedPoints)
        {
            yield return VectorStoreErrorHandler.RunModelConversion(
                QdrantConstants.VectorStoreSystemName,
                this._collectionMetadata.VectorStoreName,
                this._collectionName,
                OperationName,
                () => this._mapper.MapFromStorageToDataModel(retrievedPoint.Id, retrievedPoint.Payload, retrievedPoint.Vectors, new() { IncludeVectors = includeVectors }));
        }
    }

    /// <inheritdoc />
    public Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        return this.RunOperationAsync(
            DeleteName,
            () => key switch
            {
                ulong id => this._qdrantClient.DeleteAsync(this._collectionName, id, wait: true, cancellationToken: cancellationToken),
                Guid id => this._qdrantClient.DeleteAsync(this._collectionName, id, wait: true, cancellationToken: cancellationToken),
                _ => throw new NotSupportedException($"The provided key type '{key.GetType().Name}' is not supported by Qdrant.")
            });
    }

    /// <inheritdoc />
    public Task DeleteAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        IList? keyList = null;

        switch (keys)
        {
            case IEnumerable<ulong> k:
                keyList = k.ToList();
                break;

            case IEnumerable<Guid> k:
                keyList = k.ToList();
                break;

            case IEnumerable<object> objectKeys:
            {
                // We need to cast the keys to a list of the same type as the first element.
                List<Guid>? guidKeys = null;
                List<ulong>? ulongKeys = null;

                var isFirst = true;
                foreach (var key in objectKeys)
                {
                    if (isFirst)
                    {
                        switch (key)
                        {
                            case ulong l:
                                ulongKeys = new List<ulong> { l };
                                keyList = ulongKeys;
                                break;

                            case Guid g:
                                guidKeys = new List<Guid> { g };
                                keyList = guidKeys;
                                break;

                            default:
                                throw new NotSupportedException($"The provided key type '{key.GetType().Name}' is not supported by Qdrant.");
                        }

                        isFirst = false;
                        continue;
                    }

                    switch (key)
                    {
                        case ulong u when ulongKeys is not null:
                            ulongKeys.Add(u);
                            continue;

                        case Guid g when guidKeys is not null:
                            guidKeys.Add(g);
                            continue;

                        case Guid or ulong:
                            throw new NotSupportedException("Mixing ulong and Guid keys is not supported");

                        default:
                            throw new NotSupportedException($"The provided key type '{key.GetType().Name}' is not supported by Qdrant.");
                    }
                }

                break;
            }
        }

        if (keyList is { Count: 0 })
        {
            return Task.CompletedTask;
        }

        return this.RunOperationAsync(
            DeleteName,
            () => keyList switch
            {
                List<ulong> keysList => this._qdrantClient.DeleteAsync(
                    this._collectionName,
                    keysList,
                    wait: true,
                    cancellationToken: cancellationToken),

                List<Guid> keysList => this._qdrantClient.DeleteAsync(
                    this._collectionName,
                    keysList,
                    wait: true,
                    cancellationToken: cancellationToken),

                _ => throw new UnreachableException()
            });
    }

    /// <inheritdoc />
    public async Task<TKey> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        var keys = await this.UpsertAsync([record], cancellationToken).ConfigureAwait(false);

        return keys.Single();
    }

    /// <inheritdoc />
    public async Task<IReadOnlyList<TKey>> UpsertAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        IReadOnlyList<TRecord>? recordsList = null;

        // If an embedding generator is defined, invoke it once per property for all records.
        GeneratedEmbeddings<Embedding<float>>?[]? generatedEmbeddings = null;

        var vectorPropertyCount = this._model.VectorProperties.Count;
        for (var i = 0; i < vectorPropertyCount; i++)
        {
            var vectorProperty = this._model.VectorProperties[i];

            if (vectorProperty.EmbeddingGenerator is null)
            {
                continue;
            }

            if (recordsList is null)
            {
                recordsList = records is IReadOnlyList<TRecord> r ? r : records.ToList();

                if (recordsList.Count == 0)
                {
                    return [];
                }

                records = recordsList;
            }

            // TODO: Ideally we'd group together vector properties using the same generator (and with the same input and output properties),
            // and generate embeddings for them in a single batch. That's some more complexity though.
            if (vectorProperty.TryGenerateEmbeddings<TRecord, Embedding<float>, ReadOnlyMemory<float>>(records, cancellationToken, out var task))
            {
                generatedEmbeddings ??= new GeneratedEmbeddings<Embedding<float>>?[vectorPropertyCount];
                generatedEmbeddings[i] = await task.ConfigureAwait(false);
            }
            else
            {
                throw new InvalidOperationException(
                    $"The embedding generator configured on property '{vectorProperty.ModelName}' cannot produce an embedding of type '{typeof(Embedding<float>).Name}' for the given input type.");
            }
        }

        // Create points from records.
        var pointStructs = VectorStoreErrorHandler.RunModelConversion(
            QdrantConstants.VectorStoreSystemName,
            this._collectionMetadata.VectorStoreName,
            this._collectionName,
            UpsertName,
            () => records.Select((r, i) => this._mapper.MapFromDataToStorageModel(r, i, generatedEmbeddings)).ToList());

        if (pointStructs is { Count: 0 })
        {
            return Array.Empty<TKey>();
        }

        // Upsert.
        await this.RunOperationAsync(
            UpsertName,
            () => this._qdrantClient.UpsertAsync(this._collectionName, pointStructs, true, cancellationToken: cancellationToken)).ConfigureAwait(false);

        return pointStructs.Count == 0
            ? []
            : pointStructs[0].Id switch
            {
                { HasNum: true } => pointStructs.Select(pointStruct => (TKey)(object)pointStruct.Id.Num).ToList(),
                { HasUuid: true } => pointStructs.Select(pointStruct => (TKey)(object)Guid.Parse(pointStruct.Id.Uuid)).ToList(),
                _ => throw new UnreachableException("The Qdrant point ID is neither a number nor a UUID.")
            };
    }

    #region Search

    /// <inheritdoc />
    public async IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TInput>(
        TInput value,
        int top,
        VectorSearchOptions<TRecord>? options = default,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
        where TInput : notnull
    {
        options ??= s_defaultVectorSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle(options);

        switch (vectorProperty.EmbeddingGenerator)
        {
            case IEmbeddingGenerator<TInput, Embedding<float>> generator:
                var embedding = await generator.GenerateAsync(value, new() { Dimensions = vectorProperty.Dimensions }, cancellationToken).ConfigureAwait(false);

                await foreach (var record in this.SearchCoreAsync(embedding.Vector, top, vectorProperty, operationName: "Search", options, cancellationToken).ConfigureAwait(false))
                {
                    yield return record;
                }

                yield break;

            case null:
                throw new InvalidOperationException(VectorDataStrings.NoEmbeddingGeneratorWasConfiguredForSearch);

            default:
                throw new InvalidOperationException(
                    QdrantVectorStoreRecordFieldMapping.s_supportedVectorTypes.Contains(typeof(TInput))
                        ? string.Format(VectorDataStrings.EmbeddingTypePassedToSearchAsync)
                        : string.Format(VectorDataStrings.IncompatibleEmbeddingGeneratorWasConfiguredForInputType, typeof(TInput).Name, vectorProperty.EmbeddingGenerator.GetType().Name));
        }
    }

    /// <inheritdoc />
    public IAsyncEnumerable<VectorSearchResult<TRecord>> SearchEmbeddingAsync<TVector>(
        TVector vector,
        int top,
        VectorSearchOptions<TRecord>? options = null,
        CancellationToken cancellationToken = default)
        where TVector : notnull
    {
        options ??= s_defaultVectorSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle(options);

        return this.SearchCoreAsync(vector, top, vectorProperty, operationName: "SearchEmbedding", options, cancellationToken);
    }

    private async IAsyncEnumerable<VectorSearchResult<TRecord>> SearchCoreAsync<TVector>(
        TVector vector,
        int top,
        VectorStoreRecordVectorPropertyModel vectorProperty,
        string operationName,
        VectorSearchOptions<TRecord> options,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
        where TVector : notnull
    {
        var floatVector = VerifyVectorParam(vector);
        Verify.NotLessThan(top, 1);

        if (options.IncludeVectors && this._model.VectorProperties.Any(p => p.EmbeddingGenerator is not null))
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

#pragma warning disable CS0618 // Type or member is obsolete
        // Build filter object.
        var filter = options switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => QdrantVectorStoreCollectionSearchMapping.BuildFromLegacyFilter(legacyFilter, this._model),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => new QdrantFilterTranslator().Translate(newFilter, this._model),
            _ => new Filter()
        };
#pragma warning restore CS0618 // Type or member is obsolete

        // Specify whether to include vectors in the search results.
        var vectorsSelector = new WithVectorsSelector();
        vectorsSelector.Enable = options.IncludeVectors;

        var query = new Query
        {
            Nearest = new VectorInput(floatVector.ToArray()),
        };

        // Execute Search.
        var points = await this.RunOperationAsync(
            operationName,
            () => this._qdrantClient.QueryAsync(
                this.Name,
                query: query,
                usingVector: this._options.HasNamedVectors ? vectorProperty.StorageName : null,
                filter: filter,
                limit: (ulong)top,
                offset: (ulong)options.Skip,
                vectorsSelector: vectorsSelector,
                cancellationToken: cancellationToken)).ConfigureAwait(false);

        // Map to data model.
        var mappedResults = points.Select(point => QdrantVectorStoreCollectionSearchMapping.MapScoredPointToVectorSearchResult(
                point,
                this._mapper,
                options.IncludeVectors,
                QdrantConstants.VectorStoreSystemName,
                this._collectionMetadata.VectorStoreName,
                this._collectionName,
                "Query"));

        foreach (var result in mappedResults)
        {
            yield return result;
        }
    }

    /// <inheritdoc />
    [Obsolete("Use either SearchEmbeddingAsync to search directly on embeddings, or SearchAsync to handle embedding generation internally as part of the call.")]
    public IAsyncEnumerable<VectorSearchResult<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, int top, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
        where TVector : notnull
        => this.SearchEmbeddingAsync(vector, top, options, cancellationToken);

    #endregion Search

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetAsync(Expression<Func<TRecord, bool>> filter, int top,
        GetFilteredRecordOptions<TRecord>? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(filter);
        Verify.NotLessThan(top, 1);

        options ??= new();

        var translatedFilter = new QdrantFilterTranslator().Translate(filter, this._model);

        // Specify whether to include vectors in the search results.
        WithVectorsSelector vectorsSelector = new() { Enable = options.IncludeVectors };

        var sortInfo = options.OrderBy.Values.Count switch
        {
            0 => null,
            1 => options.OrderBy.Values[0],
            _ => throw new NotSupportedException("Qdrant does not support ordering by more than one property.")
        };

        OrderBy? orderBy = null;
        if (sortInfo is not null)
        {
            var orderByName = this._model.GetDataOrKeyProperty(sortInfo.PropertySelector).StorageName;
            orderBy = new(orderByName)
            {
                Direction = sortInfo.Ascending ? global::Qdrant.Client.Grpc.Direction.Asc : global::Qdrant.Client.Grpc.Direction.Desc
            };
        }

        var scrollResponse = await this.RunOperationAsync(
            "Scroll",
            () => this._qdrantClient.ScrollAsync(
                this.Name,
                translatedFilter,
                vectorsSelector,
                limit: (uint)(top + options.Skip),
                orderBy,
                cancellationToken: cancellationToken)).ConfigureAwait(false);

        var mappedResults = scrollResponse.Result.Skip(options.Skip).Select(point => QdrantVectorStoreCollectionSearchMapping.MapRetrievedPointToRecord(
                point,
                this._mapper,
                options.IncludeVectors,
                QdrantConstants.VectorStoreSystemName,
                this._collectionMetadata.VectorStoreName,
                this._collectionName,
                "Scroll"));

        foreach (var mappedResult in mappedResults)
        {
            yield return mappedResult;
        }
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<VectorSearchResult<TRecord>> HybridSearchAsync<TVector>(TVector vector, ICollection<string> keywords, int top, HybridSearchOptions<TRecord>? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var floatVector = VerifyVectorParam(vector);
        Verify.NotLessThan(top, 1);

        // Resolve options.
        options ??= s_defaultKeywordVectorizedHybridSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle<TRecord>(new() { VectorProperty = options.VectorProperty });
        var textDataProperty = this._model.GetFullTextDataPropertyOrSingle(options.AdditionalProperty);

        // Build filter object.
#pragma warning disable CS0618 // Type or member is obsolete
        // Build filter object.
        var filter = options switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => QdrantVectorStoreCollectionSearchMapping.BuildFromLegacyFilter(legacyFilter, this._model),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => new QdrantFilterTranslator().Translate(newFilter, this._model),
            _ => new Filter()
        };
#pragma warning restore CS0618 // Type or member is obsolete

        // Specify whether to include vectors in the search results.
        var vectorsSelector = new WithVectorsSelector();
        vectorsSelector.Enable = options.IncludeVectors;

        // Build the vector query.
        var vectorQuery = new PrefetchQuery
        {
            Filter = filter,
            Query = new Query
            {
                Nearest = new VectorInput(floatVector.ToArray()),
            },
        };

        if (this._options.HasNamedVectors)
        {
            vectorQuery.Using = this._options.HasNamedVectors ? vectorProperty.StorageName : null;
        }

        // Build the keyword query.
        var keywordFilter = filter.Clone();
        var keywordSubFilter = new Filter();
        foreach (string keyword in keywords)
        {
            keywordSubFilter.Should.Add(new Condition() { Field = new FieldCondition() { Key = textDataProperty.StorageName, Match = new Match { Text = keyword } } });
        }
        keywordFilter.Must.Add(new Condition() { Filter = keywordSubFilter });
        var keywordQuery = new PrefetchQuery
        {
            Filter = keywordFilter,
        };

        // Build the fusion query.
        var fusionQuery = new Query
        {
            Fusion = Fusion.Rrf,
        };

        // Execute Search.
        var points = await this.RunOperationAsync(
            "Query",
            () => this._qdrantClient.QueryAsync(
                this.Name,
                prefetch: new List<PrefetchQuery>() { vectorQuery, keywordQuery },
                query: fusionQuery,
                limit: (ulong)top,
                offset: (ulong)options.Skip,
                vectorsSelector: vectorsSelector,
                cancellationToken: cancellationToken)).ConfigureAwait(false);

        // Map to data model.
        var mappedResults = points.Select(point => QdrantVectorStoreCollectionSearchMapping.MapScoredPointToVectorSearchResult(
                point,
                this._mapper,
                options.IncludeVectors,
                QdrantConstants.VectorStoreSystemName,
                this._collectionMetadata.VectorStoreName,
                this._collectionName,
                "Query"));

        foreach (var result in mappedResults)
        {
            yield return result;
        }
    }

    /// <inheritdoc />
    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreRecordCollectionMetadata) ? this._collectionMetadata :
            serviceType == typeof(QdrantClient) ? this._qdrantClient.QdrantClient :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }

    /// <summary>
    /// Run the given operation and wrap any <see cref="RpcException"/> with <see cref="VectorStoreOperationException"/>."/>
    /// </summary>
    /// <param name="operationName">The type of database operation being run.</param>
    /// <param name="operation">The operation to run.</param>
    /// <returns>The result of the operation.</returns>
    private async Task RunOperationAsync(string operationName, Func<Task> operation)
    {
        try
        {
            await operation.Invoke().ConfigureAwait(false);
        }
        catch (RpcException ex)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = QdrantConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this._collectionName,
                OperationName = operationName
            };
        }
    }

    /// <summary>
    /// Run the given operation and wrap any <see cref="RpcException"/> with <see cref="VectorStoreOperationException"/>."/>
    /// </summary>
    /// <typeparam name="T">The response type of the operation.</typeparam>
    /// <param name="operationName">The type of database operation being run.</param>
    /// <param name="operation">The operation to run.</param>
    /// <returns>The result of the operation.</returns>
    private async Task<T> RunOperationAsync<T>(string operationName, Func<Task<T>> operation)
    {
        try
        {
            return await operation.Invoke().ConfigureAwait(false);
        }
        catch (RpcException ex)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = QdrantConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this._collectionName,
                OperationName = operationName
            };
        }
    }

    private static ReadOnlyMemory<float> VerifyVectorParam<TVector>(TVector vector)
    {
        Verify.NotNull(vector);

        if (vector is not ReadOnlyMemory<float> floatVector)
        {
            throw new NotSupportedException($"The provided vector type {vector.GetType().FullName} is not supported by the Qdrant connector.");
        }

        return floatVector;
    }
}
