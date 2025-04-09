// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Grpc.Core;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Qdrant.Client;
using Qdrant.Client.Grpc;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// Service for storing and retrieving vector records, that uses Qdrant as the underlying storage.
/// </summary>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class QdrantVectorStoreRecordCollection<TRecord> :
    IVectorStoreRecordCollection<ulong, TRecord>,
    IVectorStoreRecordCollection<Guid, TRecord>,
    IKeywordHybridSearch<TRecord>
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
    where TRecord : notnull
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

    /// <summary>The name of the collection that this <see cref="QdrantVectorStoreRecordCollection{TRecord}"/> will access.</summary>
    private readonly string _collectionName;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly QdrantVectorStoreRecordCollectionOptions<TRecord> _options;

    /// <summary>The model for this collection.</summary>
    private readonly VectorStoreRecordModel _model;

    /// <summary>A mapper to use for converting between qdrant point and consumer models.</summary>
#pragma warning disable CS0618 // IVectorStoreRecordMapper is obsolete
    private readonly IVectorStoreRecordMapper<TRecord, PointStruct> _mapper;
#pragma warning restore CS0618

    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantVectorStoreRecordCollection{TRecord}"/> class.
    /// </summary>
    /// <param name="qdrantClient">Qdrant client that can be used to manage the collections and points in a Qdrant store.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="QdrantVectorStoreRecordCollection{TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    /// <exception cref="ArgumentNullException">Thrown if the <paramref name="qdrantClient"/> is null.</exception>
    /// <exception cref="ArgumentException">Thrown for any misconfigured options.</exception>
    public QdrantVectorStoreRecordCollection(QdrantClient qdrantClient, string collectionName, QdrantVectorStoreRecordCollectionOptions<TRecord>? options = null)
        : this(new MockableQdrantClient(qdrantClient), collectionName, options)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantVectorStoreRecordCollection{TRecord}"/> class.
    /// </summary>
    /// <param name="qdrantClient">Qdrant client that can be used to manage the collections and points in a Qdrant store.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="QdrantVectorStoreRecordCollection{TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    /// <exception cref="ArgumentNullException">Thrown if the <paramref name="qdrantClient"/> is null.</exception>
    /// <exception cref="ArgumentException">Thrown for any misconfigured options.</exception>
    internal QdrantVectorStoreRecordCollection(MockableQdrantClient qdrantClient, string collectionName, QdrantVectorStoreRecordCollectionOptions<TRecord>? options = null)
    {
        // Verify.
        Verify.NotNull(qdrantClient);
        Verify.NotNullOrWhiteSpace(collectionName);

        // Assign.
        this._qdrantClient = qdrantClient;
        this._collectionName = collectionName;
        this._options = options ?? new QdrantVectorStoreRecordCollectionOptions<TRecord>();

        this._model = new VectorStoreRecordModelBuilder(QdrantVectorStoreRecordFieldMapping.GetModelBuildOptions(this._options.HasNamedVectors))
            .Build(typeof(TRecord), this._options.VectorStoreRecordDefinition);

#pragma warning disable CS0618 // IVectorStoreRecordMapper is obsolete
        this._mapper = this._options.PointStructCustomMapper ?? new QdrantVectorStoreRecordMapper<TRecord>(this._model, this._options.HasNamedVectors);
#pragma warning restore CS0618

        this._collectionMetadata = new()
        {
            VectorStoreSystemName = QdrantConstants.VectorStoreSystemName,
            CollectionName = collectionName
        };
    }

    /// <inheritdoc />
    public string CollectionName => this._collectionName;

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
    public async Task<TRecord?> GetAsync(ulong key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        var retrievedPoints = await this.GetAsync([key], options, cancellationToken).ToListAsync(cancellationToken).ConfigureAwait(false);
        return retrievedPoints.FirstOrDefault();
    }

    /// <inheritdoc />
    public async Task<TRecord?> GetAsync(Guid key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        var retrievedPoints = await this.GetAsync([key], options, cancellationToken).ToListAsync(cancellationToken).ConfigureAwait(false);
        return retrievedPoints.FirstOrDefault();
    }

    /// <inheritdoc />
    public IAsyncEnumerable<TRecord> GetAsync(IEnumerable<ulong> keys, GetRecordOptions? options = default, CancellationToken cancellationToken = default)
    {
        return this.GetBatchByPointIdAsync(keys, key => new PointId { Num = key }, options, cancellationToken);
    }

    /// <inheritdoc />
    public IAsyncEnumerable<TRecord> GetAsync(IEnumerable<Guid> keys, GetRecordOptions? options = default, CancellationToken cancellationToken = default)
    {
        return this.GetBatchByPointIdAsync(keys, key => new PointId { Uuid = key.ToString("D") }, options, cancellationToken);
    }

    /// <inheritdoc />
    public Task DeleteAsync(ulong key, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        return this.RunOperationAsync(
            DeleteName,
            () => this._qdrantClient.DeleteAsync(
                this._collectionName,
                key,
                wait: true,
                cancellationToken: cancellationToken));
    }

    /// <inheritdoc />
    public Task DeleteAsync(Guid key, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        return this.RunOperationAsync(
            DeleteName,
            () => this._qdrantClient.DeleteAsync(
                this._collectionName,
                key,
                wait: true,
                cancellationToken: cancellationToken));
    }

    /// <inheritdoc />
    public Task DeleteAsync(IEnumerable<ulong> keys, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        return this.RunOperationAsync(
            DeleteName,
            () => this._qdrantClient.DeleteAsync(
                this._collectionName,
                keys.ToList(),
                wait: true,
                cancellationToken: cancellationToken));
    }

    /// <inheritdoc />
    public Task DeleteAsync(IEnumerable<Guid> keys, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        return this.RunOperationAsync(
            DeleteName,
            () => this._qdrantClient.DeleteAsync(
                this._collectionName,
                keys.ToList(),
                wait: true,
                cancellationToken: cancellationToken));
    }

    /// <inheritdoc />
    public async Task<ulong> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        // Create point from record.
        var pointStruct = VectorStoreErrorHandler.RunModelConversion(
            QdrantConstants.VectorStoreSystemName,
            this._collectionMetadata.VectorStoreName,
            this._collectionName,
            UpsertName,
            () => this._mapper.MapFromDataToStorageModel(record));

        // Upsert.
        await this.RunOperationAsync(
            UpsertName,
            () => this._qdrantClient.UpsertAsync(this._collectionName, [pointStruct], true, cancellationToken: cancellationToken)).ConfigureAwait(false);
        return pointStruct.Id.Num;
    }

    /// <inheritdoc />
    async Task<Guid> IVectorStoreRecordCollection<Guid, TRecord>.UpsertAsync(TRecord record, CancellationToken cancellationToken)
    {
        Verify.NotNull(record);

        // Create point from record.
        var pointStruct = VectorStoreErrorHandler.RunModelConversion(
            QdrantConstants.VectorStoreSystemName,
            this._collectionMetadata.VectorStoreName,
            this._collectionName,
            UpsertName,
            () => this._mapper.MapFromDataToStorageModel(record));

        // Upsert.
        await this.RunOperationAsync(
            UpsertName,
            () => this._qdrantClient.UpsertAsync(this._collectionName, [pointStruct], true, cancellationToken: cancellationToken)).ConfigureAwait(false);
        return Guid.Parse(pointStruct.Id.Uuid);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<ulong> UpsertAsync(IEnumerable<TRecord> records, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        // Create points from records.
        var pointStructs = VectorStoreErrorHandler.RunModelConversion(
            QdrantConstants.VectorStoreSystemName,
            this._collectionMetadata.VectorStoreName,
            this._collectionName,
            UpsertName,
            () => records.Select(this._mapper.MapFromDataToStorageModel).ToList());

        // Upsert.
        await this.RunOperationAsync(
            UpsertName,
            () => this._qdrantClient.UpsertAsync(this._collectionName, pointStructs, true, cancellationToken: cancellationToken)).ConfigureAwait(false);

        foreach (var pointStruct in pointStructs)
        {
            yield return pointStruct.Id.Num;
        }
    }

    /// <inheritdoc />
    async IAsyncEnumerable<Guid> IVectorStoreRecordCollection<Guid, TRecord>.UpsertAsync(IEnumerable<TRecord> records, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        Verify.NotNull(records);

        // Create points from records.
        var pointStructs = VectorStoreErrorHandler.RunModelConversion(
            QdrantConstants.VectorStoreSystemName,
            this._collectionMetadata.VectorStoreName,
            this._collectionName,
            UpsertName,
            () => records.Select(this._mapper.MapFromDataToStorageModel).ToList());

        // Upsert.
        await this.RunOperationAsync(
            UpsertName,
            () => this._qdrantClient.UpsertAsync(this._collectionName, pointStructs, true, cancellationToken: cancellationToken)).ConfigureAwait(false);

        foreach (var pointStruct in pointStructs)
        {
            yield return Guid.Parse(pointStruct.Id.Uuid);
        }
    }

    /// <summary>
    /// Get the requested records from the Qdrant store using the provided keys.
    /// </summary>
    /// <param name="keys">The keys of the points to retrieve.</param>
    /// <param name="keyConverter">Function to convert the provided keys to point ids.</param>
    /// <param name="options">The retrieval options.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The retrieved points.</returns>
    private async IAsyncEnumerable<TRecord> GetBatchByPointIdAsync<TKey>(
        IEnumerable<TKey> keys,
        Func<TKey, PointId> keyConverter,
        GetRecordOptions? options,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        const string OperationName = "Retrieve";
        Verify.NotNull(keys);

        // Create options.
        var pointsIds = keys.Select(key => keyConverter(key)).ToArray();
        var includeVectors = options?.IncludeVectors ?? false;

        // Retrieve data points.
        var retrievedPoints = await this.RunOperationAsync(
            OperationName,
            () => this._qdrantClient.RetrieveAsync(this._collectionName, pointsIds, true, includeVectors, cancellationToken: cancellationToken)).ConfigureAwait(false);

        // Convert the retrieved points to the target data model.
        foreach (var retrievedPoint in retrievedPoints)
        {
            var pointStruct = new PointStruct
            {
                Id = retrievedPoint.Id,
                Vectors = retrievedPoint.Vectors,
                Payload = { }
            };

            foreach (KeyValuePair<string, Value> payloadEntry in retrievedPoint.Payload)
            {
                pointStruct.Payload.Add(payloadEntry.Key, payloadEntry.Value);
            }

            yield return VectorStoreErrorHandler.RunModelConversion(
                QdrantConstants.VectorStoreSystemName,
                this._collectionMetadata.VectorStoreName,
                this._collectionName,
                OperationName,
                () => this._mapper.MapFromStorageToDataModel(pointStruct, new() { IncludeVectors = includeVectors }));
        }
    }

    /// <inheritdoc />
    public async Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, int top, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        var floatVector = VerifyVectorParam(vector);
        Verify.NotLessThan(top, 1);

        // Resolve options.
        var internalOptions = options ?? s_defaultVectorSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle(internalOptions);

#pragma warning disable CS0618 // Type or member is obsolete
        // Build filter object.
        var filter = internalOptions switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => QdrantVectorStoreCollectionSearchMapping.BuildFromLegacyFilter(legacyFilter, this._model),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => new QdrantFilterTranslator().Translate(newFilter, this._model),
            _ => new Filter()
        };
#pragma warning restore CS0618 // Type or member is obsolete

        // Specify whether to include vectors in the search results.
        var vectorsSelector = new WithVectorsSelector();
        vectorsSelector.Enable = internalOptions.IncludeVectors;

        var query = new Query
        {
            Nearest = new VectorInput(floatVector.ToArray()),
        };

        // Execute Search.
        var points = await this.RunOperationAsync(
            "Query",
            () => this._qdrantClient.QueryAsync(
                this.CollectionName,
                query: query,
                usingVector: this._options.HasNamedVectors ? vectorProperty.StorageName : null,
                filter: filter,
                limit: (ulong)top,
                offset: (ulong)internalOptions.Skip,
                vectorsSelector: vectorsSelector,
                cancellationToken: cancellationToken)).ConfigureAwait(false);

        // Map to data model.
        var mappedResults = points.Select(point => QdrantVectorStoreCollectionSearchMapping.MapScoredPointToVectorSearchResult(
                point,
                this._mapper,
                internalOptions.IncludeVectors,
                QdrantConstants.VectorStoreSystemName,
                this._collectionMetadata.VectorStoreName,
                this._collectionName,
                "Query"));

        return new VectorSearchResults<TRecord>(mappedResults.ToAsyncEnumerable());
    }

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
                this.CollectionName,
                translatedFilter,
                vectorsSelector,
                limit: (uint)(top + options.Skip),
                orderBy,
                cancellationToken: cancellationToken)).ConfigureAwait(false);

        var mappedResults = scrollResponse.Result.Skip(options.Skip).Select(point => QdrantVectorStoreCollectionSearchMapping.MapRetrievedPointToVectorSearchResult(
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
    public async Task<VectorSearchResults<TRecord>> HybridSearchAsync<TVector>(TVector vector, ICollection<string> keywords, int top, HybridSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        var floatVector = VerifyVectorParam(vector);
        Verify.NotLessThan(top, 1);

        // Resolve options.
        var internalOptions = options ?? s_defaultKeywordVectorizedHybridSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle<TRecord>(new() { VectorProperty = internalOptions.VectorProperty });
        var textDataProperty = this._model.GetFullTextDataPropertyOrSingle(internalOptions.AdditionalProperty);

        // Build filter object.
#pragma warning disable CS0618 // Type or member is obsolete
        // Build filter object.
        var filter = internalOptions switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => QdrantVectorStoreCollectionSearchMapping.BuildFromLegacyFilter(legacyFilter, this._model),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => new QdrantFilterTranslator().Translate(newFilter, this._model),
            _ => new Filter()
        };
#pragma warning restore CS0618 // Type or member is obsolete

        // Specify whether to include vectors in the search results.
        var vectorsSelector = new WithVectorsSelector();
        vectorsSelector.Enable = internalOptions.IncludeVectors;

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
                this.CollectionName,
                prefetch: new List<PrefetchQuery>() { vectorQuery, keywordQuery },
                query: fusionQuery,
                limit: (ulong)top,
                offset: (ulong)internalOptions.Skip,
                vectorsSelector: vectorsSelector,
                cancellationToken: cancellationToken)).ConfigureAwait(false);

        // Map to data model.
        var mappedResults = points.Select(point => QdrantVectorStoreCollectionSearchMapping.MapScoredPointToVectorSearchResult(
                point,
                this._mapper,
                internalOptions.IncludeVectors,
                QdrantConstants.VectorStoreSystemName,
                this._collectionMetadata.VectorStoreName,
                this._collectionName,
                "Query"));

        return new VectorSearchResults<TRecord>(mappedResults.ToAsyncEnumerable());
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
