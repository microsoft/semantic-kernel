// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Grpc.Core;
using Microsoft.SemanticKernel.Memory;
using Qdrant.Client;
using Qdrant.Client.Grpc;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// Service for storing and retrieving vector records, that uses Qdrant as the underlying storage.
/// </summary>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
public sealed class QdrantVectorRecordStore<TRecord> : IVectorRecordStore<ulong, TRecord>, IVectorRecordStore<Guid, TRecord>
    where TRecord : class
{
    /// <summary>The name of this database for telemetry purposes.</summary>
    private const string DatabaseName = "Qdrant";

    /// <summary>The name of the upsert operation for telemetry purposes.</summary>
    private const string UpsertName = "Upsert";

    /// <summary>The name of the Delete operation for telemetry purposes.</summary>
    private const string DeleteName = "Delete";

    /// <summary>Qdrant client that can be used to manage the collections and points in a Qdrant store.</summary>
    private readonly QdrantClient _qdrantClient;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly QdrantVectorRecordStoreOptions<TRecord> _options;

    /// <summary>A mapper to use for converting between qdrant point and consumer models.</summary>
    private readonly IVectorStoreRecordMapper<TRecord, PointStruct> _mapper;

    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantVectorRecordStore{TRecord}"/> class.
    /// </summary>
    /// <param name="qdrantClient">Qdrant client that can be used to manage the collections and points in a Qdrant store.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    /// <exception cref="ArgumentNullException"></exception>
    /// <exception cref="ArgumentException"></exception>
    public QdrantVectorRecordStore(QdrantClient qdrantClient, QdrantVectorRecordStoreOptions<TRecord>? options = null)
    {
        // Verify.
        Verify.NotNull(qdrantClient);

        // Assign.
        this._qdrantClient = qdrantClient;
        this._options = options ?? new QdrantVectorRecordStoreOptions<TRecord>();

        // Assign Mapper.
        if (this._options.MapperType == QdrantRecordMapperType.QdrantPointStructCustomMapper)
        {
            // Custom Mapper.
            if (this._options.PointStructCustomMapper is null)
            {
                throw new ArgumentException($"The {nameof(QdrantVectorRecordStoreOptions<TRecord>.PointStructCustomMapper)} option needs to be set if a {nameof(QdrantVectorRecordStoreOptions<TRecord>.MapperType)} of {nameof(QdrantRecordMapperType.QdrantPointStructCustomMapper)} has been chosen.", nameof(options));
            }

            this._mapper = this._options.PointStructCustomMapper;
        }
        else
        {
            // Default Mapper.
            this._mapper = new QdrantVectorStoreRecordMapper<TRecord>(new QdrantVectorStoreRecordMapperOptions
            {
                HasNamedVectors = this._options.HasNamedVectors,
                VectorStoreRecordDefinition = this._options.VectorStoreRecordDefinition
            });
        }
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

        var collectionName = this.ChooseCollectionName(options?.CollectionName);
        return RunOperationAsync(
            collectionName,
            DeleteName,
            () => this._qdrantClient.DeleteAsync(
                collectionName,
                key,
                wait: true,
                cancellationToken: cancellationToken));
    }

    /// <inheritdoc />
    public Task DeleteAsync(Guid key, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        var collectionName = this.ChooseCollectionName(options?.CollectionName);
        return RunOperationAsync(
            collectionName,
            DeleteName,
            () => this._qdrantClient.DeleteAsync(
                collectionName,
                key,
                wait: true,
                cancellationToken: cancellationToken));
    }

    /// <inheritdoc />
    public Task DeleteBatchAsync(IEnumerable<ulong> keys, DeleteRecordOptions? options = default, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        var collectionName = this.ChooseCollectionName(options?.CollectionName);
        return RunOperationAsync(
            collectionName,
            DeleteName,
            () => this._qdrantClient.DeleteAsync(
                collectionName,
                keys.ToList(),
                wait: true,
                cancellationToken: cancellationToken));
    }

    /// <inheritdoc />
    public Task DeleteBatchAsync(IEnumerable<Guid> keys, DeleteRecordOptions? options = default, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        var collectionName = this.ChooseCollectionName(options?.CollectionName);
        return RunOperationAsync(
            collectionName,
            DeleteName,
            () => this._qdrantClient.DeleteAsync(
                collectionName,
                keys.ToList(),
                wait: true,
                cancellationToken: cancellationToken));
    }

    /// <inheritdoc />
    public async Task<ulong> UpsertAsync(TRecord record, UpsertRecordOptions? options = default, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        // Create options.
        var collectionName = this.ChooseCollectionName(options?.CollectionName);

        // Create point from record.
        var pointStruct = VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
            collectionName,
            UpsertName,
            () => this._mapper.MapFromDataToStorageModel(record));

        // Upsert.
        await RunOperationAsync(
            collectionName,
            UpsertName,
            () => this._qdrantClient.UpsertAsync(collectionName, [pointStruct], true, cancellationToken: cancellationToken)).ConfigureAwait(false);
        return pointStruct.Id.Num;
    }

    /// <inheritdoc />
    async Task<Guid> IVectorRecordStore<Guid, TRecord>.UpsertAsync(TRecord record, UpsertRecordOptions? options, CancellationToken cancellationToken)
    {
        Verify.NotNull(record);

        // Create options.
        var collectionName = this.ChooseCollectionName(options?.CollectionName);

        // Create point from record.
        var pointStruct = VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
            collectionName,
            UpsertName,
            () => this._mapper.MapFromDataToStorageModel(record));

        // Upsert.
        await RunOperationAsync(
            collectionName,
            UpsertName,
            () => this._qdrantClient.UpsertAsync(collectionName, [pointStruct], true, cancellationToken: cancellationToken)).ConfigureAwait(false);
        return Guid.Parse(pointStruct.Id.Uuid);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<ulong> UpsertBatchAsync(IEnumerable<TRecord> records, UpsertRecordOptions? options = default, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        // Create Options
        var collectionName = this.ChooseCollectionName(options?.CollectionName);

        // Create points from records.
        var pointStructs = VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
            collectionName,
            UpsertName,
            () => records.Select(this._mapper.MapFromDataToStorageModel).ToList());

        // Upsert.
        await RunOperationAsync(
            collectionName,
            UpsertName,
            () => this._qdrantClient.UpsertAsync(collectionName, pointStructs, true, cancellationToken: cancellationToken)).ConfigureAwait(false);

        foreach (var pointStruct in pointStructs)
        {
            yield return pointStruct.Id.Num;
        }
    }

    /// <inheritdoc />
    async IAsyncEnumerable<Guid> IVectorRecordStore<Guid, TRecord>.UpsertBatchAsync(IEnumerable<TRecord> records, UpsertRecordOptions? options, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        Verify.NotNull(records);

        // Create Options
        var collectionName = this.ChooseCollectionName(options?.CollectionName);

        // Create points from records.
        var pointStructs = VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
            collectionName,
            UpsertName,
            () => records.Select(this._mapper.MapFromDataToStorageModel).ToList());

        // Upsert.
        await RunOperationAsync(
            collectionName,
            UpsertName,
            () => this._qdrantClient.UpsertAsync(collectionName, pointStructs, true, cancellationToken: cancellationToken)).ConfigureAwait(false);

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
        var collectionName = this.ChooseCollectionName(options?.CollectionName);
        var pointsIds = keys.Select(key => keyConverter(key)).ToArray();
        var includeVectors = options?.IncludeVectors ?? false;

        // Retrieve data points.
        var retrievedPoints = await RunOperationAsync(
            collectionName,
            OperationName,
            () => this._qdrantClient.RetrieveAsync(collectionName, pointsIds, true, includeVectors, cancellationToken: cancellationToken)).ConfigureAwait(false);

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
                collectionName,
                OperationName,
                () => this._mapper.MapFromStorageToDataModel(pointStruct, new() { IncludeVectors = includeVectors }));
        }
    }

    /// <summary>
    /// Choose the right collection name to use for the operation by using the one provided
    /// as part of the operation options, or the default one provided at construction time.
    /// </summary>
    /// <param name="operationCollectionName">The collection name provided on the operation options.</param>
    /// <returns>The collection name to use.</returns>
    private string ChooseCollectionName(string? operationCollectionName)
    {
        var collectionName = operationCollectionName ?? this._options.DefaultCollectionName;
        if (collectionName is null)
        {
#pragma warning disable CA2208 // Instantiate argument exceptions correctly
            throw new ArgumentException("Collection name must be provided in the operation options, since no default was provided at construction time.", "options");
#pragma warning restore CA2208 // Instantiate argument exceptions correctly
        }

        return collectionName;
    }

    /// <summary>
    /// Run the given operation and wrap any <see cref="RpcException"/> with <see cref="VectorStoreOperationException"/>."/>
    /// </summary>
    /// <typeparam name="T">The response type of the operation.</typeparam>
    /// <param name="collectionName">The name of the collection the operation is being run on.</param>
    /// <param name="operationName">The type of database operation being run.</param>
    /// <param name="operation">The operation to run.</param>
    /// <returns>The result of the operation.</returns>
    private static async Task<T> RunOperationAsync<T>(string collectionName, string operationName, Func<Task<T>> operation)
    {
        try
        {
            return await operation.Invoke().ConfigureAwait(false);
        }
        catch (RpcException ex)
        {
            var wrapperException = new VectorStoreOperationException("Call to vector store failed.", ex);

            // Using Open Telemetry standard for naming of these entries.
            // https://opentelemetry.io/docs/specs/semconv/attributes-registry/db/
            wrapperException.Data.Add("db.system", DatabaseName);
            wrapperException.Data.Add("db.collection.name", collectionName);
            wrapperException.Data.Add("db.operation.name", operationName);

            throw wrapperException;
        }
    }
}
