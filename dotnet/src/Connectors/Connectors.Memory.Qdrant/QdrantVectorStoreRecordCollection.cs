// Copyright (c) Microsoft. All rights reserved.

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

    /// <summary>A definition of the current storage model.</summary>
    private readonly VectorStoreRecordDefinition _vectorStoreRecordDefinition;

    /// <summary>A mapper to use for converting between qdrant point and consumer models.</summary>
    private readonly IVectorStoreRecordMapper<TRecord, PointStruct> _mapper;

    /// <summary>A dictionary that maps from a property name to the configured name that should be used when storing it.</summary>
    private readonly Dictionary<string, string> _storagePropertyNames = new();

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
        this._vectorStoreRecordDefinition = this._options.VectorStoreRecordDefinition ?? VectorStoreRecordPropertyReader.CreateVectorStoreRecordDefinitionFromType(typeof(TRecord), true);

        // Validate property types.
        var properties = VectorStoreRecordPropertyReader.SplitDefinitionAndVerify(typeof(TRecord).Name, this._vectorStoreRecordDefinition, supportsMultipleVectors: this._options.HasNamedVectors, requiresAtLeastOneVector: !this._options.HasNamedVectors);
        VectorStoreRecordPropertyReader.VerifyPropertyTypes([properties.KeyProperty], s_supportedKeyTypes, "Key");

        // Build a map of property names to storage names.
        this._storagePropertyNames = VectorStoreRecordPropertyReader.BuildPropertyNameToStorageNameMap(properties);

        // Assign Mapper.
        if (this._options.PointStructCustomMapper is not null)
        {
            // Custom Mapper.
            this._mapper = this._options.PointStructCustomMapper;
        }
        else
        {
            // Default Mapper.
            this._mapper = new QdrantVectorStoreRecordMapper<TRecord>(
                this._vectorStoreRecordDefinition,
                this._options.HasNamedVectors,
                this._storagePropertyNames);
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
            var singleVectorProperty = this._vectorStoreRecordDefinition.Properties.OfType<VectorStoreRecordVectorProperty>().First();

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
            var vectorProperties = this._vectorStoreRecordDefinition.Properties.OfType<VectorStoreRecordVectorProperty>();

            // Map the named vectors to the qdrant config.
            var vectorParamsMap = QdrantVectorStoreCollectionCreateMapping.MapNamedVectors(vectorProperties, this._storagePropertyNames);

            // Create the collection with named vectors.
            await this.RunOperationAsync(
                "CreateCollection",
                () => this._qdrantClient.CreateCollectionAsync(
                    this._collectionName,
                    vectorParamsMap,
                    cancellationToken: cancellationToken)).ConfigureAwait(false);
        }

        // Add indexes for each of the data properties that require filtering.
        var dataProperties = this._vectorStoreRecordDefinition.Properties.OfType<VectorStoreRecordDataProperty>().Where(x => x.IsFilterable);
        foreach (var dataProperty in dataProperties)
        {
            var storageFieldName = this._storagePropertyNames[dataProperty.DataModelPropertyName];
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
        dataProperties = this._vectorStoreRecordDefinition.Properties.OfType<VectorStoreRecordDataProperty>().Where(x => x.IsFullTextSearchable);
        foreach (var dataProperty in dataProperties)
        {
            if (dataProperty.PropertyType != typeof(string))
            {
                throw new InvalidOperationException($"Property {nameof(dataProperty.IsFullTextSearchable)} on {nameof(VectorStoreRecordDataProperty)} '{dataProperty.DataModelPropertyName}' is set to true, but the property type is not a string. The Qdrant VectorStore supports {nameof(dataProperty.IsFullTextSearchable)} on string properties only.");
            }

            var storageFieldName = this._storagePropertyNames[dataProperty.DataModelPropertyName];

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
