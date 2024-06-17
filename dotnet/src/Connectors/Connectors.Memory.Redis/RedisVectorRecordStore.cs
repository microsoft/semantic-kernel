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
using Microsoft.SemanticKernel.Memory;
using NRedisStack.Json.DataTypes;
using NRedisStack.RedisStackCommands;
using StackExchange.Redis;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Service for storing and retrieving records, that uses Redis as the underlying storage.
/// </summary>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
public sealed class RedisVectorRecordStore<TRecord> : IVectorRecordStore<string, TRecord>
    where TRecord : class
{
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

    /// <summary>The redis database to read/write records from.</summary>
    private readonly IDatabase _database;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly RedisVectorRecordStoreOptions<TRecord> _options;

    /// <summary>A property info object that points at the key property for the current model, allowing easy reading and writing of this property.</summary>
    private readonly PropertyInfo _keyPropertyInfo;

    /// <summary>The name of the temporary json property that the key property will be serialized / parsed from.</summary>
    private readonly string _keyJsonPropertyName;

    /// <summary>An array of the names of all the data properties that are part of the redis payload, i.e. all properties except the key and vector properties.</summary>
    private readonly string[] _dataPropertyNames;

    /// <summary>An array of the names of all the data and vector properties that are part of the redis payload.</summary>
    private readonly string[] _dataAndVectorPropertyNames;

    /// <summary>The mapper to use when mapping between the consumer data model and the redis record.</summary>
    private readonly IVectorStoreRecordMapper<TRecord, (string Key, JsonNode Node)> _mapper;

    /// <summary>
    /// Initializes a new instance of the <see cref="RedisVectorRecordStore{TRecord}"/> class.
    /// </summary>
    /// <param name="database">The redis database to read/write records from.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    /// <exception cref="ArgumentNullException">Throw when parameters are invalid.</exception>
    public RedisVectorRecordStore(IDatabase database, RedisVectorRecordStoreOptions<TRecord>? options)
    {
        // Verify.
        Verify.NotNull(database);

        // Assign.
        this._database = database;
        this._options = options ?? new RedisVectorRecordStoreOptions<TRecord>();

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
        this._keyJsonPropertyName = VectorStoreRecordPropertyReader.GetSerializedPropertyName(this._keyPropertyInfo);

        this._dataPropertyNames = properties
            .dataProperties
            .Select(VectorStoreRecordPropertyReader.GetSerializedPropertyName)
            .ToArray();

        this._dataAndVectorPropertyNames = this._dataPropertyNames
            .Concat(properties.vectorProperties.Select(VectorStoreRecordPropertyReader.GetSerializedPropertyName))
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
    public async Task<TRecord> GetAsync(string key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(key);

        // Create Options
        var collectionName = this.ChooseCollectionName(options?.CollectionName);
        var maybePrefixedKey = this.PrefixKeyIfNeeded(key, collectionName);

        // Get the redis value.
        var redisResult = await RunOperationAsync(
            collectionName,
            "GET",
            () => options?.IncludeVectors is true ?
                this._database
                    .JSON()
                    .GetAsync(maybePrefixedKey) :
                this._database
                    .JSON()
                    .GetAsync(maybePrefixedKey, this._dataPropertyNames)).ConfigureAwait(false);

        // Check if the key was found before trying to serialize the result.
        if (redisResult.IsNull)
        {
            throw new VectorStoreOperationException($"Could not find document with key '{key}'");
        }

        // Convert to the caller's data model.
        return RunModelConversion(
            collectionName,
            "GET",
            () =>
            {
                var node = JsonSerializer.Deserialize<JsonNode>(redisResult.ToString())!;
                return this._mapper.MapFromStorageToDataModel((key, node));
            });
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<string> keys, GetRecordOptions? options = default, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);
        var keysList = keys.ToList();

        // Create Options
        var collectionName = this.ChooseCollectionName(options?.CollectionName);
        var maybePrefixedKeys = keysList.Select(key => this.PrefixKeyIfNeeded(key, collectionName));
        var redisKeys = maybePrefixedKeys.Select(x => new RedisKey(x)).ToArray();

        // Get the list of redis results.
        var redisResults = await RunOperationAsync(
            collectionName,
            "MGET",
            () => this._database
                .JSON()
                .MGetAsync(redisKeys, "$")).ConfigureAwait(false);

        // Loop through each key and result and convert to the caller's data model.
        for (int i = 0; i < keysList.Count; i++)
        {
            var key = keysList[i];
            var redisResult = redisResults[i];

            // Check if the key was found before trying to serialize the result.
            if (redisResult.IsNull)
            {
                throw new VectorStoreOperationException($"Could not find document with key '{key}'");
            }

            // Convert to the caller's data model.
            yield return RunModelConversion(
                collectionName,
                "MGET",
                () =>
                {
                    var node = JsonSerializer.Deserialize<JsonNode>(redisResult.ToString())!;
                    return this._mapper.MapFromStorageToDataModel((key, node));
                });
        }
    }

    /// <inheritdoc />
    public Task DeleteAsync(string key, DeleteRecordOptions? options = default, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(key);

        // Create Options
        var collectionName = this.ChooseCollectionName(options?.CollectionName);
        var maybePrefixedKey = this.PrefixKeyIfNeeded(key, collectionName);

        // Remove.
        return RunOperationAsync(
            collectionName,
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

        // Create Options
        var collectionName = this.ChooseCollectionName(options?.CollectionName);

        // Map.
        var redisJsonRecord = RunModelConversion(
            collectionName,
            "SET",
            () => this._mapper.MapFromDataToStorageModel(record));

        // Upsert.
        var maybePrefixedKey = this.PrefixKeyIfNeeded(redisJsonRecord.Key, collectionName);
        await RunOperationAsync(
            collectionName,
            "SET",
            () => this._database
                .JSON()
                .SetAsync(
                    maybePrefixedKey,
                    "$",
                    redisJsonRecord.Node)).ConfigureAwait(false);

        return redisJsonRecord.Key;
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> UpsertBatchAsync(IEnumerable<TRecord> records, UpsertRecordOptions? options = default, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        // Create Options
        var collectionName = this.ChooseCollectionName(options?.CollectionName);

        // Map.
        var redisRecords = new List<(string maybePrefixedKey, string originalKey, JsonNode jsonNode)>();
        foreach (var record in records)
        {
            var redisJsonRecord = RunModelConversion(
                collectionName,
                "MSET",
                () => this._mapper.MapFromDataToStorageModel(record));

            var maybePrefixedKey = this.PrefixKeyIfNeeded(redisJsonRecord.Key, collectionName);
            redisRecords.Add((maybePrefixedKey, redisJsonRecord.Key, redisJsonRecord.Node));
        }

        // Upsert.
        var keyPathValues = redisRecords.Select(x => new KeyPathValue(x.maybePrefixedKey, "$", x.jsonNode)).ToArray();
        await RunOperationAsync(
            collectionName,
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
    /// <param name="collectionName">The collection name that was provided as part of an operation to override the default or the default if not.</param>
    /// <returns>The updated key if updating is required, otherwise the input key.</returns>
    private string PrefixKeyIfNeeded(string key, string? collectionName)
    {
        if (this._options.PrefixCollectionNameToKeyNames)
        {
            return $"{collectionName}:{key}";
        }

        return key;
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
    /// Run the given operation and wrap any redis exceptions with <see cref="VectorStoreOperationException"/>."/>
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
        catch (RedisConnectionException ex)
        {
            var wrapperException = new VectorStoreOperationException("Call to vector store failed.", ex);

            // Using Open Telemetry standard for naming of these entries.
            // https://opentelemetry.io/docs/specs/semconv/attributes-registry/db/
            wrapperException.Data.Add("db.system", "Redis");
            wrapperException.Data.Add("db.collection.name", collectionName);
            wrapperException.Data.Add("db.operation.name", operationName);

            throw wrapperException;
        }
    }

    /// <summary>
    /// Run the given model conversion and wrap any exceptions with <see cref="VectorStoreRecordMappingException"/>.
    /// </summary>
    /// <typeparam name="T">The response type of the operation.</typeparam>
    /// <param name="collectionName">The name of the collection the operation is being run on.</param>
    /// <param name="operationName">The type of database operation being run.</param>
    /// <param name="operation">The operation to run.</param>
    /// <returns>The result of the operation.</returns>
    private static T RunModelConversion<T>(string collectionName, string operationName, Func<T> operation)
    {
        try
        {
            return operation.Invoke();
        }
        catch (Exception ex)
        {
            var wrapperException = new VectorStoreRecordMappingException("Failed to convert vector store record.", ex);

            // Using Open Telemetry standard for naming of these entries.
            // https://opentelemetry.io/docs/specs/semconv/attributes-registry/db/
            wrapperException.Data.Add("db.system", "AzureAISearch");
            wrapperException.Data.Add("db.collection.name", collectionName);
            wrapperException.Data.Add("db.operation.name", operationName);

            throw wrapperException;
        }
    }
}
