// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Linq.Expressions;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;
using Grpc.Core;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using Qdrant.Client;
using Qdrant.Client.Grpc;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// Service for storing and retrieving vector records, that uses Qdrant as the underlying storage.
/// </summary>
/// <typeparam name="TKey">The data type of the record key. Can be either <see cref="Guid"/> or <see cref="ulong"/>.</typeparam>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public class QdrantCollection<TKey, TRecord> : VectorStoreCollection<TKey, TRecord>, IKeywordHybridSearchable<TRecord>
    where TKey : notnull
    where TRecord : class
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    /// <summary>Metadata about vector store record collection.</summary>
    private readonly VectorStoreCollectionMetadata _collectionMetadata;

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

    /// <summary>The model for this collection.</summary>
    private readonly CollectionModel _model;

    /// <summary>A mapper to use for converting between qdrant point and consumer models.</summary>
    private readonly QdrantMapper<TRecord> _mapper;

    /// <summary>Whether the vectors in the store are named and multiple vectors are supported, or whether there is just a single unnamed vector per qdrant point.</summary>
    private readonly bool _hasNamedVectors;

    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="qdrantClient">Qdrant client that can be used to manage the collections and points in a Qdrant store.</param>
    /// <param name="name">The name of the collection that this <see cref="QdrantCollection{TKey, TRecord}"/> will access.</param>
    /// <param name="ownsClient">A value indicating whether <paramref name="qdrantClient"/> is disposed when the collection is disposed.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    /// <exception cref="ArgumentNullException">Thrown if the <paramref name="qdrantClient"/> is null.</exception>
    /// <exception cref="ArgumentException">Thrown for any misconfigured options.</exception>
    [RequiresDynamicCode("This constructor is incompatible with NativeAOT. For dynamic mapping via Dictionary<string, object?>, instantiate QdrantDynamicCollection instead.")]
    [RequiresUnreferencedCode("This constructor is incompatible with trimming. For dynamic mapping via Dictionary<string, object?>, instantiate QdrantDynamicCollection instead")]
    public QdrantCollection(QdrantClient qdrantClient, string name, bool ownsClient, QdrantCollectionOptions? options = null)
        : this(() => new MockableQdrantClient(qdrantClient, ownsClient), name, options)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="clientFactory">Qdrant client factory.</param>
    /// <param name="name">The name of the collection that this <see cref="QdrantCollection{TKey, TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    /// <exception cref="ArgumentNullException">Thrown if the <paramref name="clientFactory"/> is null.</exception>
    /// <exception cref="ArgumentException">Thrown for any misconfigured options.</exception>
    [RequiresDynamicCode("This constructor is incompatible with NativeAOT. For dynamic mapping via Dictionary<string, object?>, instantiate QdrantDynamicCollection instead.")]
    [RequiresUnreferencedCode("This constructor is incompatible with trimming. For dynamic mapping via Dictionary<string, object?>, instantiate QdrantDynamicCollection instead")]
    internal QdrantCollection(Func<MockableQdrantClient> clientFactory, string name, QdrantCollectionOptions? options = null)
        : this(
            clientFactory,
            name,
            static options => typeof(TRecord) == typeof(Dictionary<string, object?>)
                ? throw new NotSupportedException(VectorDataStrings.NonDynamicCollectionWithDictionaryNotSupported(typeof(QdrantDynamicCollection)))
                : new QdrantModelBuilder(options.HasNamedVectors).Build(typeof(TRecord), options.Definition, options.EmbeddingGenerator),
            options)
    {
    }

    internal QdrantCollection(Func<MockableQdrantClient> clientFactory, string name, Func<QdrantCollectionOptions, CollectionModel> modelFactory, QdrantCollectionOptions? options)
    {
        // Verify.
        Verify.NotNull(clientFactory);
        Verify.NotNullOrWhiteSpace(name);

        if (typeof(TKey) != typeof(ulong) && typeof(TKey) != typeof(Guid) && typeof(TKey) != typeof(object))
        {
            throw new NotSupportedException("Only ulong and Guid keys are supported.");
        }

        options ??= QdrantCollectionOptions.Default;

        // Assign.
        this.Name = name;
        this._model = modelFactory(options);

        this._hasNamedVectors = options.HasNamedVectors;
        this._mapper = new QdrantMapper<TRecord>(this._model, options.HasNamedVectors);

        this._collectionMetadata = new()
        {
            VectorStoreSystemName = QdrantConstants.VectorStoreSystemName,
            CollectionName = name
        };

        // The code above can throw, so we need to create the client after the model is built and verified.
        // In case an exception is thrown, we don't need to dispose any resources.
        this._qdrantClient = clientFactory();
    }

    /// <inheritdoc />
    protected override void Dispose(bool disposing)
    {
        this._qdrantClient.Dispose();
        base.Dispose(disposing);
    }

    /// <inheritdoc />
    public override string Name { get; }

    /// <inheritdoc />
    public override Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        return this.RunOperationAsync(
            "CollectionExists",
            () => this._qdrantClient.CollectionExistsAsync(this.Name, cancellationToken));
    }

    /// <inheritdoc />
    public override async Task EnsureCollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        // Don't even try to create if the collection already exists.
        if (await this.CollectionExistsAsync(cancellationToken).ConfigureAwait(false))
        {
            return;
        }

        try
        {
            if (!this._hasNamedVectors)
            {
                // If we are not using named vectors, we can only have one vector property. We can assume we have exactly one, since this is already verified in the constructor.
                var singleVectorProperty = this._model.VectorProperty;

                // Map the single vector property to the qdrant config.
                var vectorParams = QdrantCollectionCreateMapping.MapSingleVector(singleVectorProperty!);

                // Create the collection with the single unnamed vector.
                await this._qdrantClient.CreateCollectionAsync(
                    this.Name,
                    vectorParams,
                    cancellationToken: cancellationToken).ConfigureAwait(false);
            }
            else
            {
                // Since we are using named vectors, iterate over all vector properties.
                var vectorProperties = this._model.VectorProperties;

                // Map the named vectors to the qdrant config.
                var vectorParamsMap = QdrantCollectionCreateMapping.MapNamedVectors(vectorProperties);

                // Create the collection with named vectors.
                await this._qdrantClient.CreateCollectionAsync(
                    this.Name,
                    vectorParamsMap,
                    cancellationToken: cancellationToken).ConfigureAwait(false);
            }

            // Add indexes for each of the data properties that require filtering.
            var dataProperties = this._model.DataProperties.Where(x => x.IsIndexed);
            foreach (var dataProperty in dataProperties)
            {
                // Note that the schema type doesn't distinguish between array and scalar type (so PayloadSchemaType.Integer is used for both integer and array of integers)
                if (QdrantCollectionCreateMapping.s_schemaTypeMap.TryGetValue(dataProperty.Type, out PayloadSchemaType schemaType)
                    || dataProperty.Type.IsArray
                        && QdrantCollectionCreateMapping.s_schemaTypeMap.TryGetValue(dataProperty.Type.GetElementType()!, out schemaType)
                    || dataProperty.Type.IsGenericType
                        && dataProperty.Type.GetGenericTypeDefinition() == typeof(List<>)
                        && QdrantCollectionCreateMapping.s_schemaTypeMap.TryGetValue(dataProperty.Type.GenericTypeArguments[0], out schemaType))
                {
                    await this._qdrantClient.CreatePayloadIndexAsync(
                        this.Name,
                        dataProperty.StorageName,
                        schemaType,
                        cancellationToken: cancellationToken).ConfigureAwait(false);
                }
                else
                {
                    // TODO: This should move to model validation
                    throw new InvalidOperationException($"Property {nameof(VectorStoreDataProperty.IsIndexed)} on {nameof(VectorStoreDataProperty)} '{dataProperty.ModelName}' is set to true, but the property type {dataProperty.Type.Name} is not supported for filtering. The Qdrant VectorStore supports filtering on {string.Join(", ", QdrantCollectionCreateMapping.s_schemaTypeMap.Keys.Select(x => x.Name))} properties only.");
                }
            }

            // Add indexes for each of the data properties that require full text search.
            dataProperties = this._model.DataProperties.Where(x => x.IsFullTextIndexed);
            foreach (var dataProperty in dataProperties)
            {
                // TODO: This should move to model validation
                if (dataProperty.Type != typeof(string))
                {
                    throw new InvalidOperationException($"Property {nameof(dataProperty.IsFullTextIndexed)} on {nameof(VectorStoreDataProperty)} '{dataProperty.ModelName}' is set to true, but the property type is not a string. The Qdrant VectorStore supports {nameof(dataProperty.IsFullTextIndexed)} on string properties only.");
                }

                await this._qdrantClient.CreatePayloadIndexAsync(
                    this.Name,
                    dataProperty.StorageName,
                    PayloadSchemaType.Text,
                    cancellationToken: cancellationToken).ConfigureAwait(false);
            }
        }
        catch (RpcException ex) when (ex.StatusCode == StatusCode.AlreadyExists)
        {
            // Do nothing, since the collection is already created.
        }
        catch (RpcException ex)
        {
            throw new VectorStoreException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = QdrantConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this.Name,
                OperationName = "EnsureCollectionExists"
            };
        }
    }

    /// <inheritdoc />
    public override Task EnsureCollectionDeletedAsync(CancellationToken cancellationToken = default)
        => this.RunOperationAsync("DeleteCollection",
            async () =>
            {
                try
                {
                    await this._qdrantClient.DeleteCollectionAsync(this.Name, null, cancellationToken).ConfigureAwait(false);
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
    public override async Task<TRecord?> GetAsync(TKey key, RecordRetrievalOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        var retrievedPoints = await this.GetAsync([key], options, cancellationToken).ToListAsync(cancellationToken).ConfigureAwait(false);
        return retrievedPoints.FirstOrDefault();
    }

    /// <inheritdoc />
    public override async IAsyncEnumerable<TRecord> GetAsync(
        IEnumerable<TKey> keys,
        RecordRetrievalOptions? options = default,
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
        if (includeVectors && this._model.EmbeddingGenerationRequired)
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        // Retrieve data points.
        var retrievedPoints = await this.RunOperationAsync(
            OperationName,
            () => this._qdrantClient.RetrieveAsync(this.Name, pointsIds, true, includeVectors, cancellationToken: cancellationToken)).ConfigureAwait(false);

        // Convert the retrieved points to the target data model.
        foreach (var retrievedPoint in retrievedPoints)
        {
            yield return this._mapper.MapFromStorageToDataModel(retrievedPoint.Id, retrievedPoint.Payload, retrievedPoint.Vectors, includeVectors);
        }
    }

    /// <inheritdoc />
    public override Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        return this.RunOperationAsync(
            DeleteName,
            () => key switch
            {
                ulong id => this._qdrantClient.DeleteAsync(this.Name, id, wait: true, cancellationToken: cancellationToken),
                Guid id => this._qdrantClient.DeleteAsync(this.Name, id, wait: true, cancellationToken: cancellationToken),
                _ => throw new NotSupportedException($"The provided key type '{key.GetType().Name}' is not supported by Qdrant.")
            });
    }

    /// <inheritdoc />
    public override Task DeleteAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
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
                    this.Name,
                    keysList,
                    wait: true,
                    cancellationToken: cancellationToken),

                List<Guid> keysList => this._qdrantClient.DeleteAsync(
                    this.Name,
                    keysList,
                    wait: true,
                    cancellationToken: cancellationToken),

                _ => throw new UnreachableException()
            });
    }

    /// <inheritdoc />
    public override async Task UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        await this.UpsertAsync([record], cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public override async Task UpsertAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        IReadOnlyList<TRecord>? recordsList = null;

        // If an embedding generator is defined, invoke it once per property for all records.
        GeneratedEmbeddings<Embedding<float>>?[]? generatedEmbeddings = null;

        var vectorPropertyCount = this._model.VectorProperties.Count;
        for (var i = 0; i < vectorPropertyCount; i++)
        {
            var vectorProperty = this._model.VectorProperties[i];

            if (QdrantModelBuilder.IsVectorPropertyTypeValidCore(vectorProperty.Type, out _))
            {
                continue;
            }

            // We have a vector property whose type isn't natively supported - we need to generate embeddings.
            Debug.Assert(vectorProperty.EmbeddingGenerator is not null);

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
            if (vectorProperty.TryGenerateEmbeddings<TRecord, Embedding<float>>(records, cancellationToken, out var task))
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
        var pointStructs = records.Select((r, i) => this._mapper.MapFromDataToStorageModel(r, i, generatedEmbeddings)).ToList();

        if (pointStructs is { Count: 0 })
        {
            return;
        }

        // Upsert.
        await this.RunOperationAsync(
            UpsertName,
            () => this._qdrantClient.UpsertAsync(this.Name, pointStructs, true, cancellationToken: cancellationToken)).ConfigureAwait(false);
    }

    #region Search

    /// <inheritdoc />
    public override async IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TInput>(
        TInput searchValue,
        int top,
        VectorSearchOptions<TRecord>? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(searchValue);
        Verify.NotLessThan(top, 1);

        options ??= s_defaultVectorSearchOptions;
        if (options.IncludeVectors && this._model.EmbeddingGenerationRequired)
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        var vectorProperty = this._model.GetVectorPropertyOrSingle(options);
        var vectorArray = await GetSearchVectorArrayAsync(searchValue, vectorProperty, cancellationToken).ConfigureAwait(false);

#pragma warning disable CS0618 // Type or member is obsolete
        // Build filter object.
        var filter = options switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => QdrantCollectionSearchMapping.BuildFromLegacyFilter(legacyFilter, this._model),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => new QdrantFilterTranslator().Translate(newFilter, this._model),
            _ => new Filter()
        };
#pragma warning restore CS0618 // Type or member is obsolete

        // Specify whether to include vectors in the search results.
        var vectorsSelector = new WithVectorsSelector { Enable = options.IncludeVectors };
        var query = new Query { Nearest = new VectorInput(vectorArray) };

        // Execute Search.
        var points = await this.RunOperationAsync(
            "Query",
            () => this._qdrantClient.QueryAsync(
                this.Name,
                query: query,
                usingVector: this._hasNamedVectors ? vectorProperty.StorageName : null,
                filter: filter,
                limit: (ulong)top,
                offset: (ulong)options.Skip,
                vectorsSelector: vectorsSelector,
                cancellationToken: cancellationToken)).ConfigureAwait(false);

        // Map to data model.
        var mappedResults = points.Select(point => QdrantCollectionSearchMapping.MapScoredPointToVectorSearchResult(
                point,
                this._mapper,
                options.IncludeVectors,
                QdrantConstants.VectorStoreSystemName,
                this._collectionMetadata.VectorStoreName,
                this.Name,
                "Query"));

        foreach (var result in mappedResults)
        {
            yield return result;
        }
    }

    private static async ValueTask<float[]> GetSearchVectorArrayAsync<TInput>(TInput searchValue, VectorPropertyModel vectorProperty, CancellationToken cancellationToken)
        where TInput : notnull
    {
        if (searchValue is float[] array)
        {
            return array;
        }

        var memory = searchValue switch
        {
            ReadOnlyMemory<float> r => r,
            Embedding<float> e => e.Vector,
            _ when vectorProperty.EmbeddingGenerator is IEmbeddingGenerator<TInput, Embedding<float>> generator
                => await generator.GenerateVectorAsync(searchValue, cancellationToken: cancellationToken).ConfigureAwait(false),

            _ => vectorProperty.EmbeddingGenerator is null
                ? throw new NotSupportedException(VectorDataStrings.InvalidSearchInputAndNoEmbeddingGeneratorWasConfigured(searchValue.GetType(), QdrantModelBuilder.SupportedVectorTypes))
                : throw new InvalidOperationException(VectorDataStrings.IncompatibleEmbeddingGeneratorWasConfiguredForInputType(typeof(TInput), vectorProperty.EmbeddingGenerator.GetType()))
        };

        return MemoryMarshal.TryGetArray(memory, out ArraySegment<float> segment) && segment.Count == segment.Array!.Length
                ? segment.Array
                : memory.ToArray();
    }

    #endregion Search

    /// <inheritdoc />
    public async override IAsyncEnumerable<TRecord> GetAsync(Expression<Func<TRecord, bool>> filter, int top,
        FilteredRecordRetrievalOptions<TRecord>? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(filter);
        Verify.NotLessThan(top, 1);

        options ??= new();

        var translatedFilter = new QdrantFilterTranslator().Translate(filter, this._model);

        // Specify whether to include vectors in the search results.
        WithVectorsSelector vectorsSelector = new() { Enable = options.IncludeVectors };

        var orderByValues = options.OrderBy?.Invoke(new()).Values;
        var sortInfo = orderByValues switch
        {
            null => null,
            _ when orderByValues.Count == 1 => orderByValues[0],
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

        var mappedResults = scrollResponse.Result.Skip(options.Skip).Select(point => QdrantCollectionSearchMapping.MapRetrievedPointToRecord(
                point,
                this._mapper,
                options.IncludeVectors,
                QdrantConstants.VectorStoreSystemName,
                this._collectionMetadata.VectorStoreName,
                this.Name,
                "Scroll"));

        foreach (var mappedResult in mappedResults)
        {
            yield return mappedResult;
        }
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<VectorSearchResult<TRecord>> HybridSearchAsync<TInput>(TInput searchValue, ICollection<string> keywords, int top, HybridSearchOptions<TRecord>? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
        where TInput : notnull
    {
        Verify.NotLessThan(top, 1);

        // Resolve options.
        options ??= s_defaultKeywordVectorizedHybridSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle<TRecord>(new() { VectorProperty = options.VectorProperty });
        var vectorArray = await GetSearchVectorArrayAsync(searchValue, vectorProperty, cancellationToken).ConfigureAwait(false);
        var textDataProperty = this._model.GetFullTextDataPropertyOrSingle(options.AdditionalProperty);

        // Build filter object.
#pragma warning disable CS0618 // Type or member is obsolete
        // Build filter object.
        var filter = options switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => QdrantCollectionSearchMapping.BuildFromLegacyFilter(legacyFilter, this._model),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => new QdrantFilterTranslator().Translate(newFilter, this._model),
            _ => new Filter()
        };
#pragma warning restore CS0618 // Type or member is obsolete

        // Specify whether to include vectors in the search results.
        var vectorsSelector = new WithVectorsSelector { Enable = options.IncludeVectors };

        // Build the vector query.
        var vectorQuery = new PrefetchQuery
        {
            Filter = filter,
            Query = new Query { Nearest = new VectorInput(vectorArray) }
        };

        if (this._hasNamedVectors)
        {
            vectorQuery.Using = this._hasNamedVectors ? vectorProperty.StorageName : null;
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
        var mappedResults = points.Select(point => QdrantCollectionSearchMapping.MapScoredPointToVectorSearchResult(
                point,
                this._mapper,
                options.IncludeVectors,
                QdrantConstants.VectorStoreSystemName,
                this._collectionMetadata.VectorStoreName,
                this.Name,
                "Query"));

        foreach (var result in mappedResults)
        {
            yield return result;
        }
    }

    /// <inheritdoc />
    public override object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreCollectionMetadata) ? this._collectionMetadata :
            serviceType == typeof(QdrantClient) ? this._qdrantClient.QdrantClient :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }

    /// <summary>
    /// Run the given operation and wrap any <see cref="RpcException"/> with <see cref="VectorStoreException"/>."/>
    /// </summary>
    /// <param name="operationName">The type of database operation being run.</param>
    /// <param name="operation">The operation to run.</param>
    /// <returns>The result of the operation.</returns>
    private Task RunOperationAsync(string operationName, Func<Task> operation)
        => VectorStoreErrorHandler.RunOperationAsync<RpcException>(
            this._collectionMetadata,
            operationName,
            operation);

    /// <summary>
    /// Run the given operation and wrap any <see cref="RpcException"/> with <see cref="VectorStoreException"/>."/>
    /// </summary>
    /// <typeparam name="T">The response type of the operation.</typeparam>
    /// <param name="operationName">The type of database operation being run.</param>
    /// <param name="operation">The operation to run.</param>
    /// <returns>The result of the operation.</returns>
    private Task<T> RunOperationAsync<T>(string operationName, Func<Task<T>> operation)
        => VectorStoreErrorHandler.RunOperationAsync<T, RpcException>(
            this._collectionMetadata,
            operationName,
            operation);
}
