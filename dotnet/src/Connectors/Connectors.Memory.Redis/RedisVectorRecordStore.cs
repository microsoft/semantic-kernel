// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Data;
using NRedisStack.Json.DataTypes;
using NRedisStack.RedisStackCommands;
using StackExchange.Redis;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Service for storing and retrieving vector records, that uses Redis as the underlying storage.
/// </summary>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
public sealed class RedisVectorRecordStore<TRecord> : IVectorRecordStore<string, TRecord>
    where TRecord : class
{
    /// <summary>The name of this database for telemetry purposes.</summary>
    private const string DatabaseName = "Redis";

    /// <summary>A set of types that a key on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedKeyTypes =
    [
        typeof(string)
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

    /// <summary>The name of the collection that this <see cref="RedisVectorRecordStore{TRecord}"/> will access.</summary>
    private readonly string _collectionName;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly RedisVectorRecordStoreOptions<TRecord> _options;

    /// <summary>A property info object that points at the key property for the current model, allowing easy reading and writing of this property.</summary>
    private readonly PropertyInfo _keyPropertyInfo;

    /// <summary>The name of the temporary JSON property that the key property will be serialized / parsed from.</summary>
    private readonly string _keyJsonPropertyName;

    /// <summary>An array of the names of all the data properties that are part of the Redis payload, i.e. all properties except the key and vector properties.</summary>
    private readonly string[] _dataPropertyNames;

    /// <summary>The mapper to use when mapping between the consumer data model and the Redis record.</summary>
    private readonly IVectorStoreRecordMapper<TRecord, (string Key, JsonNode Node)> _mapper;

    /// <summary>The JSON serializer options to use when converting between the data model and the Redis record.</summary>
    private readonly JsonSerializerOptions _jsonSerializerOptions;

    /// <summary>
    /// Initializes a new instance of the <see cref="RedisVectorRecordStore{TRecord}"/> class.
    /// </summary>
    /// <param name="database">The Redis database to read/write records from.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="RedisVectorRecordStore{TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    /// <exception cref="ArgumentNullException">Throw when parameters are invalid.</exception>
    public RedisVectorRecordStore(IDatabase database, string collectionName, RedisVectorRecordStoreOptions<TRecord>? options = null)
    {
        // Verify.
        Verify.NotNull(database);
        Verify.NotNullOrWhiteSpace(collectionName);

        // Assign.
        this._database = database;
        this._collectionName = collectionName;
        this._options = options ?? new RedisVectorRecordStoreOptions<TRecord>();
        this._jsonSerializerOptions = this._options.JsonSerializerOptions ?? JsonSerializerOptions.Default;

        // Enumerate public properties using configuration or attributes.
        (PropertyInfo keyProperty, List<PropertyInfo> dataProperties, List<PropertyInfo> vectorProperties) properties;
        if (this._options.VectorStoreRecordDefinition is not null)
        {
            properties = VectorStoreRecordPropertyReader.FindProperties(typeof(TRecord), this._options.VectorStoreRecordDefinition, supportsMultipleVectors: true);
        }
        else
        {
            properties = VectorStoreRecordPropertyReader.FindProperties(typeof(TRecord), supportsMultipleVectors: true);
        }

        // Validate property types and store for later use.
        VectorStoreRecordPropertyReader.VerifyPropertyTypes([properties.keyProperty], s_supportedKeyTypes, "Key");
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(properties.vectorProperties, s_supportedVectorTypes, "Vector");

        this._keyPropertyInfo = properties.keyProperty;
        this._keyJsonPropertyName = VectorStoreRecordPropertyReader.GetJsonPropertyName(this._jsonSerializerOptions, this._keyPropertyInfo);

        this._dataPropertyNames = properties
            .dataProperties
            .Select(x => VectorStoreRecordPropertyReader.GetJsonPropertyName(this._jsonSerializerOptions, x))
            .ToArray();

        // Assign Mapper.
        if (this._options.MapperType == RedisRecordMapperType.JsonNodeCustomMapper)
        {
            if (this._options.JsonNodeCustomMapper is null)
            {
                throw new ArgumentException($"The {nameof(RedisVectorRecordStoreOptions<TRecord>.JsonNodeCustomMapper)} option needs to be set if a {nameof(RedisVectorRecordStoreOptions<TRecord>.MapperType)} of {nameof(RedisRecordMapperType.JsonNodeCustomMapper)} has been chosen.", nameof(options));
            }

            this._mapper = this._options.JsonNodeCustomMapper;
        }
        else
        {
            this._mapper = new RedisVectorStoreRecordMapper<TRecord>(this._keyJsonPropertyName);
        }
    }

    /// <inheritdoc />
    public async Task<TRecord?> GetAsync(string key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(key);

        // Create Options
        var maybePrefixedKey = this.PrefixKeyIfNeeded(key);
        var includeVectors = options?.IncludeVectors ?? false;

        // Get the Redis value.
        var redisResult = await this.RunOperationAsync(
            "GET",
            () => options?.IncludeVectors is true ?
                this._database
                    .JSON()
                    .GetAsync(maybePrefixedKey) :
                this._database
                    .JSON()
                    .GetAsync(maybePrefixedKey, this._dataPropertyNames)).ConfigureAwait(false);

        // Check if the key was found before trying to parse the result.
        if (redisResult.IsNull || redisResult is null)
        {
            return null;
        }

        // Check if the value contained any JSON text before trying to parse the result.
        var redisResultString = redisResult.ToString();
        if (redisResultString is null)
        {
            throw new VectorStoreRecordMappingException($"Document with key '{key}' does not contain any json.");
        }

        // Convert to the caller's data model.
        return VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
            this._collectionName,
            "GET",
            () =>
            {
                var node = JsonSerializer.Deserialize<JsonNode>(redisResultString, this._jsonSerializerOptions)!;
                return this._mapper.MapFromStorageToDataModel((key, node), new() { IncludeVectors = includeVectors });
            });
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<string> keys, GetRecordOptions? options = default, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);
        var keysList = keys.ToList();

        // Create Options
        var maybePrefixedKeys = keysList.Select(key => this.PrefixKeyIfNeeded(key));
        var redisKeys = maybePrefixedKeys.Select(x => new RedisKey(x)).ToArray();
        var includeVectors = options?.IncludeVectors ?? false;

        // Get the list of Redis results.
        var redisResults = await this.RunOperationAsync(
            "MGET",
            () => this._database
                .JSON()
                .MGetAsync(redisKeys, "$")).ConfigureAwait(false);

        // Loop through each key and result and convert to the caller's data model.
        for (int i = 0; i < keysList.Count; i++)
        {
            var key = keysList[i];
            var redisResult = redisResults[i];

            // Check if the key was found before trying to parse the result.
            if (redisResult.IsNull || redisResult is null)
            {
                continue;
            }

            // Check if the value contained any JSON text before trying to parse the result.
            var redisResultString = redisResult.ToString();
            if (redisResultString is null)
            {
                throw new VectorStoreRecordMappingException($"Document with key '{key}' does not contain any json.");
            }

            // Convert to the caller's data model.
            yield return VectorStoreErrorHandler.RunModelConversion(
                DatabaseName,
                this._collectionName,
                "MGET",
                () =>
                {
                    var node = JsonSerializer.Deserialize<JsonNode>(redisResultString, this._jsonSerializerOptions)!;
                    return this._mapper.MapFromStorageToDataModel((key, node), new() { IncludeVectors = includeVectors });
                });
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
                .JSON()
                .DelAsync(maybePrefixedKey));
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
        var redisJsonRecord = VectorStoreErrorHandler.RunModelConversion(
            DatabaseName,
            this._collectionName,
            "SET",
                () =>
                {
                    var mapResult = this._mapper.MapFromDataToStorageModel(record);
                    var serializedRecord = JsonSerializer.Serialize(mapResult.Node, this._jsonSerializerOptions);
                    return new { Key = mapResult.Key, SerializedRecord = serializedRecord };
                });

        // Upsert.
        var maybePrefixedKey = this.PrefixKeyIfNeeded(redisJsonRecord.Key);
        await this.RunOperationAsync(
            "SET",
            () => this._database
                .JSON()
                .SetAsync(
                    maybePrefixedKey,
                    "$",
                    redisJsonRecord.SerializedRecord)).ConfigureAwait(false);

        return redisJsonRecord.Key;
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> UpsertBatchAsync(IEnumerable<TRecord> records, UpsertRecordOptions? options = default, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        // Map.
        var redisRecords = new List<(string maybePrefixedKey, string originalKey, string serializedRecord)>();
        foreach (var record in records)
        {
            var redisJsonRecord = VectorStoreErrorHandler.RunModelConversion(
                DatabaseName,
                this._collectionName,
                "MSET",
                () =>
                {
                    var mapResult = this._mapper.MapFromDataToStorageModel(record);
                    var serializedRecord = JsonSerializer.Serialize(mapResult.Node, this._jsonSerializerOptions);
                    return new { Key = mapResult.Key, SerializedRecord = serializedRecord };
                });

            var maybePrefixedKey = this.PrefixKeyIfNeeded(redisJsonRecord.Key);
            redisRecords.Add((maybePrefixedKey, redisJsonRecord.Key, redisJsonRecord.SerializedRecord));
        }

        // Upsert.
        var keyPathValues = redisRecords.Select(x => new KeyPathValue(x.maybePrefixedKey, "$", x.serializedRecord)).ToArray();
        await this.RunOperationAsync(
            "MSET",
            () => this._database
                .JSON()
                .MSetAsync(keyPathValues)).ConfigureAwait(false);

        // Return keys of upserted records.
        foreach (var record in redisRecords)
        {
            yield return record.originalKey;
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
}
