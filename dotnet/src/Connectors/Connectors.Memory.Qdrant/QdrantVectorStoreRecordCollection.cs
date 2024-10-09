﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Grpc.Core;
using Microsoft.SemanticKernel.Data;
using Qdrant.Client;
using Qdrant.Client.Grpc;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// Service for storing and retrieving vector records, that uses Qdrant as the underlying storage.
/// </summary>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class QdrantVectorStoreRecordCollection<TRecord> : IVectorStoreRecordCollection<ulong, TRecord>, IVectorStoreRecordCollection<Guid, TRecord>
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
    where TRecord : class
{
    /// <summary>A set of types that a key on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedKeyTypes =
    [
        typeof(ulong),
        typeof(Guid)
    ];

    /// <summary>The default options for vector search.</summary>
    private static readonly VectorSearchOptions s_defaultVectorSearchOptions = new();

    /// <summary>The name of this database for telemetry purposes.</summary>
    private const string DatabaseName = "Qdrant";

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

    /// <summary>A helper to access property information for the current data model and record definition.</summary>
    private readonly VectorStoreRecordPropertyReader _propertyReader;

    /// <summary>A mapper to use for converting between qdrant point and consumer models.</summary>
    private readonly IVectorStoreRecordMapper<TRecord, PointStruct> _mapper;

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
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelKeyType(typeof(TRecord), options?.PointStructCustomMapper is not null, s_supportedKeyTypes);
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelDefinitionSupplied(typeof(TRecord), options?.VectorStoreRecordDefinition is not null);

        // Assign.
        this._qdrantClient = qdrantClient;
        this._collectionName = collectionName;
        this._options = options ?? new QdrantVectorStoreRecordCollectionOptions<TRecord>();
        this._propertyReader = new VectorStoreRecordPropertyReader(
            typeof(TRecord),
            this._options.VectorStoreRecordDefinition,
            new()
            {
                RequiresAtLeastOneVector = !this._options.HasNamedVectors,
                SupportsMultipleKeys = false,
                SupportsMultipleVectors = this._options.HasNamedVectors
            });

        // Validate property types.
        this._propertyReader.VerifyKeyProperties(s_supportedKeyTypes);

        // Assign Mapper.
        if (this._options.PointStructCustomMapper is not null)
        {
            // Custom Mapper.
            this._mapper = this._options.PointStructCustomMapper;
        }
        else if (typeof(TRecord) == typeof(VectorStoreGenericDataModel<ulong>) || typeof(TRecord) == typeof(VectorStoreGenericDataModel<Guid>))
        {
            // Generic data model mapper.
            this._mapper = (IVectorStoreRecordMapper<TRecord, PointStruct>)new QdrantGenericDataModelMapper(
                this._propertyReader,
                this._options.HasNamedVectors);
        }
        else
        {
            // Default Mapper.
            this._mapper = new QdrantVectorStoreRecordMapper<TRecord>(
                this._propertyReader,
                this._options.HasNamedVectors);
        }
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
            var singleVectorProperty = this._propertyReader.VectorProperty;

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
            var vectorProperties = this._propertyReader.VectorProperties;

            // Map the named vectors to the qdrant config.
            var vectorParamsMap = QdrantVectorStoreCollectionCreateMapping.MapNamedVectors(vectorProperties, this._propertyReader.StoragePropertyNamesMap);

            // Create the collection with named vectors.
            await this.RunOperationAsync(
                "CreateCollection",
                () => this._qdrantClient.CreateCollectionAsync(
                    this._collectionName,
                    vectorParamsMap,
                    cancellationToken: cancellationToken)).ConfigureAwait(false);
        }

        // Add indexes for each of the data properties that require filtering.
        var dataProperties = this._propertyReader.DataProperties.Where(x => x.IsFilterable);
        foreach (var dataProperty in dataProperties)
        {
            var storageFieldName = this._propertyReader.GetStoragePropertyName(dataProperty.DataModelPropertyName);
            var schemaType = QdrantVectorStoreCollectionCreateMapping.s_schemaTypeMap[dataProperty.PropertyType!];

            await this.RunOperationAsync(
                "CreatePayloadIndex",
                () => this._qdrantClient.CreatePayloadIndexAsync(
                    this._collectionName,
                    storageFieldName,
                    schemaType,
                    cancellationToken: cancellationToken)).ConfigureAwait(false);
        }

        // Add indexes for each of the data properties that require full text search.
        dataProperties = this._propertyReader.DataProperties.Where(x => x.IsFullTextSearchable);
        foreach (var dataProperty in dataProperties)
        {
            if (dataProperty.PropertyType != typeof(string))
            {
                throw new InvalidOperationException($"Property {nameof(dataProperty.IsFullTextSearchable)} on {nameof(VectorStoreRecordDataProperty)} '{dataProperty.DataModelPropertyName}' is set to true, but the property type is not a string. The Qdrant VectorStore supports {nameof(dataProperty.IsFullTextSearchable)} on string properties only.");
            }

            var storageFieldName = this._propertyReader.GetStoragePropertyName(dataProperty.DataModelPropertyName);

            await this.RunOperationAsync(
                "CreatePayloadIndex",
                () => this._qdrantClient.CreatePayloadIndexAsync(
                    this._collectionName,
                    storageFieldName,
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
    {
        return this.RunOperationAsync(
            "DeleteCollection",
            () => this._qdrantClient.DeleteCollectionAsync(this._collectionName, null, cancellationToken));
    }

    /// <inheritdoc />
    public async Task<TRecord?> GetAsync(ulong key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        var retrievedPoints = await this.GetBatchAsync([key], options, cancellationToken).ToListAsync(cancellationToken).ConfigureAwait(false);
        return retrievedPoints.FirstOrDefault();
    }

    /// <inheritdoc />
    public async Task<TRecord?> GetAsync(Guid key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        var retrievedPoints = await this.GetBatchAsync([key], options, cancellationToken).ToListAsync(cancellationToken).ConfigureAwait(false);
        return retrievedPoints.FirstOrDefault();
    }

    /// <inheritdoc />
    public IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<ulong> keys, GetRecordOptions? options = default, CancellationToken cancellationToken = default)
    {
        return this.GetBatchByPointIdAsync(keys, key => new PointId { Num = key }, options, cancellationToken);
    }

    /// <inheritdoc />
    public IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<Guid> keys, GetRecordOptions? options = default, CancellationToken cancellationToken = default)
    {
        return this.GetBatchByPointIdAsync(keys, key => new PointId { Uuid = key.ToString("D") }, options, cancellationToken);
    }

    /// <inheritdoc />
    public Task DeleteAsync(ulong key, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
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
    public Task DeleteAsync(Guid key, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
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
    public Task DeleteBatchAsync(IEnumerable<ulong> keys, DeleteRecordOptions? options = default, CancellationToken cancellationToken = default)
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
    public Task DeleteBatchAsync(IEnumerable<Guid> keys, DeleteRecordOptions? options = default, CancellationToken cancellationToken = default)
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
    public async Task<ulong> UpsertAsync(TRecord record, UpsertRecordOptions? options = default, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        // Create point from record.
        var pointStruct = VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
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
    async Task<Guid> IVectorStoreRecordCollection<Guid, TRecord>.UpsertAsync(TRecord record, UpsertRecordOptions? options, CancellationToken cancellationToken)
    {
        Verify.NotNull(record);

        // Create point from record.
        var pointStruct = VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
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
    public async IAsyncEnumerable<ulong> UpsertBatchAsync(IEnumerable<TRecord> records, UpsertRecordOptions? options = default, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        // Create points from records.
        var pointStructs = VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
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
    async IAsyncEnumerable<Guid> IVectorStoreRecordCollection<Guid, TRecord>.UpsertBatchAsync(IEnumerable<TRecord> records, UpsertRecordOptions? options, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        Verify.NotNull(records);

        // Create points from records.
        var pointStructs = VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
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
                DatabaseName,
                this._collectionName,
                OperationName,
                () => this._mapper.MapFromStorageToDataModel(pointStruct, new() { IncludeVectors = includeVectors }));
        }
    }

    /// <inheritdoc />
    public async Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, VectorSearchOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(vector);

        if (this._propertyReader.FirstVectorPropertyName is null)
        {
            throw new InvalidOperationException("The collection does not have any vector fields, so vector search is not possible.");
        }

        if (vector is not ReadOnlyMemory<float> floatVector)
        {
            throw new NotSupportedException($"The provided vector type {vector.GetType().FullName} is not supported by the Qdrant connector.");
        }

        var internalOptions = options ?? s_defaultVectorSearchOptions;

        // Build filter object.
        var filter = QdrantVectorStoreCollectionSearchMapping.BuildFilter(internalOptions.Filter, this._propertyReader.StoragePropertyNamesMap);

        // Specify the vector name if named vectors are used.
        string? vectorName = null;
        if (this._options.HasNamedVectors)
        {
            vectorName = this.ResolveVectorFieldName(internalOptions.VectorPropertyName);
        }

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
                usingVector: vectorName,
                filter: filter,
                limit: (ulong)internalOptions.Top,
                offset: (ulong)internalOptions.Skip,
                vectorsSelector: vectorsSelector,
                cancellationToken: cancellationToken)).ConfigureAwait(false);

        // Map to data model.
        var mappedResults = points.Select(point => QdrantVectorStoreCollectionSearchMapping.MapScoredPointToVectorSearchResult(
                point,
                this._mapper,
                internalOptions.IncludeVectors,
                DatabaseName,
                this._collectionName,
                "Query"));

        return new VectorSearchResults<TRecord>(mappedResults.ToAsyncEnumerable());
    }

    /// <summary>
    /// Resolve the vector field name to use for a search by using the storage name for the field name from options
    /// if available, and falling back to the first vector field name if not.
    /// </summary>
    /// <param name="optionsVectorFieldName">The vector field name provided via options.</param>
    /// <returns>The resolved vector field name.</returns>
    /// <exception cref="InvalidOperationException">Thrown if the provided field name is not a valid field name.</exception>
    private string ResolveVectorFieldName(string? optionsVectorFieldName)
    {
        string? vectorFieldName;
        if (!string.IsNullOrWhiteSpace(optionsVectorFieldName))
        {
            if (!this._propertyReader.StoragePropertyNamesMap.TryGetValue(optionsVectorFieldName!, out vectorFieldName))
            {
                throw new InvalidOperationException($"The collection does not have a vector field named '{optionsVectorFieldName}'.");
            }
        }
        else
        {
            vectorFieldName = this._propertyReader.FirstVectorPropertyStoragePropertyName;
        }

        return vectorFieldName!;
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
                VectorStoreType = DatabaseName,
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
                VectorStoreType = DatabaseName,
                CollectionName = this._collectionName,
                OperationName = operationName
            };
        }
    }
}
