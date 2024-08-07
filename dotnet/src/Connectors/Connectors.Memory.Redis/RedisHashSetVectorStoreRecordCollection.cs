// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Data;
using NRedisStack.RedisStackCommands;
using NRedisStack.Search;
using NRedisStack.Search.Literals.Enums;
using StackExchange.Redis;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Service for storing and retrieving vector records, that uses Redis HashSets as the underlying storage.
/// </summary>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class RedisHashSetVectorStoreRecordCollection<TRecord> : IVectorStoreRecordCollection<string, TRecord>
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
    where TRecord : class
{
    /// <summary>The name of this database for telemetry purposes.</summary>
    private const string DatabaseName = "Redis";

    /// <summary>A set of types that a key on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedKeyTypes =
    [
        typeof(string)
    ];

    /// <summary>A set of types that data properties on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedDataTypes =
    [
        typeof(string),
        typeof(int),
        typeof(uint),
        typeof(long),
        typeof(ulong),
        typeof(double),
        typeof(float),
        typeof(bool),
        typeof(int?),
        typeof(uint?),
        typeof(long?),
        typeof(ulong?),
        typeof(double?),
        typeof(float?),
        typeof(bool?)
    ];

    /// <summary>A set of types that vectors on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedVectorTypes =
    [
        typeof(ReadOnlyMemory<float>),
        typeof(ReadOnlyMemory<double>),
        typeof(ReadOnlyMemory<float>?),
        typeof(ReadOnlyMemory<double>?)
    ];

    /// <summary>The Redis database to read/write records from.</summary>
    private readonly IDatabase _database;

    /// <summary>The name of the collection that this <see cref="RedisHashSetVectorStoreRecordCollection{TRecord}"/> will access.</summary>
    private readonly string _collectionName;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly RedisHashSetVectorStoreRecordCollectionOptions<TRecord> _options;

    /// <summary>A definition of the current storage model.</summary>
    private readonly VectorStoreRecordDefinition _vectorStoreRecordDefinition;

    /// <summary>An array of the names of all the data properties that are part of the Redis payload, i.e. all properties except the key and vector properties.</summary>
    private readonly RedisValue[] _dataStoragePropertyNames;

    /// <summary>A dictionary that maps from a property name to the storage name that should be used when serializing it to json for data and vector properties.</summary>
    private readonly Dictionary<string, string> _storagePropertyNames = new();

    /// <summary>The mapper to use when mapping between the consumer data model and the Redis record.</summary>
    private readonly IVectorStoreRecordMapper<TRecord, (string Key, HashEntry[] HashEntries)> _mapper;

    /// <summary>
    /// Initializes a new instance of the <see cref="RedisHashSetVectorStoreRecordCollection{TRecord}"/> class.
    /// </summary>
    /// <param name="database">The Redis database to read/write records from.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="RedisHashSetVectorStoreRecordCollectionOptions{TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    /// <exception cref="ArgumentNullException">Throw when parameters are invalid.</exception>
    public RedisHashSetVectorStoreRecordCollection(IDatabase database, string collectionName, RedisHashSetVectorStoreRecordCollectionOptions<TRecord>? options = null)
    {
        // Verify.
        Verify.NotNull(database);
        Verify.NotNullOrWhiteSpace(collectionName);

        // Assign.
        this._database = database;
        this._collectionName = collectionName;
        this._options = options ?? new RedisHashSetVectorStoreRecordCollectionOptions<TRecord>();
        this._vectorStoreRecordDefinition = this._options.VectorStoreRecordDefinition ?? VectorStoreRecordPropertyReader.CreateVectorStoreRecordDefinitionFromType(typeof(TRecord), true);

        // Validate property types.
        var properties = VectorStoreRecordPropertyReader.SplitDefinitionAndVerify(typeof(TRecord).Name, this._vectorStoreRecordDefinition, supportsMultipleVectors: true, requiresAtLeastOneVector: false);
        VectorStoreRecordPropertyReader.VerifyPropertyTypes([properties.KeyProperty], s_supportedKeyTypes, "Key");
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(properties.DataProperties, s_supportedDataTypes, "Data");
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(properties.VectorProperties, s_supportedVectorTypes, "Vector");

        // Lookup storage property names.
        this._storagePropertyNames = VectorStoreRecordPropertyReader.BuildPropertyNameToStorageNameMap(properties);
        this._dataStoragePropertyNames = properties
            .DataProperties
            .Select(x => this._storagePropertyNames[x.DataModelPropertyName])
            .Select(RedisValue.Unbox)
            .ToArray();

        // Assign Mapper.
        if (this._options.HashEntriesCustomMapper is not null)
        {
            this._mapper = this._options.HashEntriesCustomMapper;
        }
        else
        {
            this._mapper = new RedisHashSetVectorStoreRecordMapper<TRecord>(this._vectorStoreRecordDefinition, this._storagePropertyNames);
        }
    }

    /// <inheritdoc />
    public string CollectionName => this._collectionName;

    /// <inheritdoc />
    public async Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            await this._database.FT().InfoAsync(this._collectionName).ConfigureAwait(false);
            return true;
        }
        catch (RedisServerException ex) when (ex.Message.Contains("Unknown index name"))
        {
            return false;
        }
        catch (RedisConnectionException ex)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreType = DatabaseName,
                CollectionName = this._collectionName,
                OperationName = "FT.INFO"
            };
        }
    }

    /// <inheritdoc />
    public Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        // Map the record definition to a schema.
        var schema = RedisVectorStoreCollectionCreateMapping.MapToSchema(this._vectorStoreRecordDefinition.Properties, this._storagePropertyNames);

        // Create the index creation params.
        // Add the collection name and colon as the index prefix, which means that any record where the key is prefixed with this text will be indexed by this index
        var createParams = new FTCreateParams()
            .AddPrefix($"{this._collectionName}:")
            .On(IndexDataType.HASH);

        // Create the index.
        return this.RunOperationAsync("FT.CREATE", () => this._database.FT().CreateAsync(this._collectionName, createParams, schema));
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
        return this.RunOperationAsync("FT.DROPINDEX", () => this._database.FT().DropIndexAsync(this._collectionName));
    }

    /// <inheritdoc />
    public async Task<TRecord?> GetAsync(string key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(key);

        // Create Options
        var maybePrefixedKey = this.PrefixKeyIfNeeded(key);
        var includeVectors = options?.IncludeVectors ?? false;
        var operationName = includeVectors ? "HGETALL" : "HMGET";

        // Get the Redis value.
        HashEntry[] retrievedHashEntries;
        if (includeVectors)
        {
            retrievedHashEntries = await this.RunOperationAsync(
                operationName,
                () => this._database.HashGetAllAsync(maybePrefixedKey)).ConfigureAwait(false);
        }
        else
        {
            var fieldKeys = this._dataStoragePropertyNames;
            var retrievedValues = await this.RunOperationAsync(
                operationName,
                () => this._database.HashGetAsync(maybePrefixedKey, fieldKeys)).ConfigureAwait(false);
            retrievedHashEntries = fieldKeys.Zip(retrievedValues, (field, value) => new HashEntry(field, value)).Where(x => x.Value.HasValue).ToArray();
        }

        // Return null if we found nothing.
        if (retrievedHashEntries == null || retrievedHashEntries.Length == 0)
        {
            return null;
        }

        // Convert to the caller's data model.
        return VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
            this._collectionName,
            operationName,
            () =>
            {
                return this._mapper.MapFromStorageToDataModel((key, retrievedHashEntries), new() { IncludeVectors = includeVectors });
            });
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<string> keys, GetRecordOptions? options = default, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        // Get records in parallel.
        var tasks = keys.Select(x => this.GetAsync(x, options, cancellationToken));
        var results = await Task.WhenAll(tasks).ConfigureAwait(false);
        foreach (var result in results)
        {
            if (result is not null)
            {
                yield return result;
            }
        }
    }

    /// <inheritdoc />
    public Task DeleteAsync(string key, DeleteRecordOptions? options = default, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(key);

        // Create Options
        var maybePrefixedKey = this.PrefixKeyIfNeeded(key);

        // Remove.
        return this.RunOperationAsync(
            "DEL",
            () => this._database
                .KeyDeleteAsync(maybePrefixedKey));
    }

    /// <inheritdoc />
    public Task DeleteBatchAsync(IEnumerable<string> keys, DeleteRecordOptions? options = default, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        // Remove records in parallel.
        var tasks = keys.Select(key => this.DeleteAsync(key, options, cancellationToken));
        return Task.WhenAll(tasks);
    }

    /// <inheritdoc />
    public async Task<string> UpsertAsync(TRecord record, UpsertRecordOptions? options = default, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        // Map.
        var redisHashSetRecord = VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
            this._collectionName,
            "HSET",
            () => this._mapper.MapFromDataToStorageModel(record));

        // Upsert.
        var maybePrefixedKey = this.PrefixKeyIfNeeded(redisHashSetRecord.Key);
        await this.RunOperationAsync(
            "HSET",
            () => this._database
                .HashSetAsync(
                    maybePrefixedKey,
                    redisHashSetRecord.HashEntries)).ConfigureAwait(false);

        return redisHashSetRecord.Key;
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> UpsertBatchAsync(IEnumerable<TRecord> records, UpsertRecordOptions? options = default, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        // Upsert records in parallel.
        var tasks = records.Select(x => this.UpsertAsync(x, options, cancellationToken));
        var results = await Task.WhenAll(tasks).ConfigureAwait(false);
        foreach (var result in results)
        {
            if (result is not null)
            {
                yield return result;
            }
        }
    }

    /// <summary>
    /// Prefix the key with the collection name if the option is set.
    /// </summary>
    /// <param name="key">The key to prefix.</param>
    /// <returns>The updated key if updating is required, otherwise the input key.</returns>
    private string PrefixKeyIfNeeded(string key)
    {
        if (this._options.PrefixCollectionNameToKeyNames)
        {
            return $"{this._collectionName}:{key}";
        }

        return key;
    }

    /// <summary>
    /// Run the given operation and wrap any Redis exceptions with <see cref="VectorStoreOperationException"/>."/>
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
        catch (RedisConnectionException ex)
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
    /// Run the given operation and wrap any Redis exceptions with <see cref="VectorStoreOperationException"/>."/>
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
        catch (RedisConnectionException ex)
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
