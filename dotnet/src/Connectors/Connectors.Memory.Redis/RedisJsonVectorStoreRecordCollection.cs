// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using NRedisStack.Json.DataTypes;
using NRedisStack.RedisStackCommands;
using NRedisStack.Search;
using NRedisStack.Search.Literals.Enums;
using StackExchange.Redis;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Service for storing and retrieving vector records, that uses Redis JSON as the underlying storage.
/// </summary>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public class RedisJsonVectorStoreRecordCollection<TRecord> : IVectorStoreRecordCollection<string, TRecord>
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
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

    /// <summary>The default options for vector search.</summary>
    private static readonly VectorSearchOptions<TRecord> s_defaultVectorSearchOptions = new();

    /// <summary>The Redis database to read/write records from.</summary>
    private readonly IDatabase _database;

    /// <summary>The name of the collection that this <see cref="RedisJsonVectorStoreRecordCollection{TRecord}"/> will access.</summary>
    private readonly string _collectionName;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly RedisJsonVectorStoreRecordCollectionOptions<TRecord> _options;

    /// <summary>A helper to access property information for the current data model and record definition.</summary>
    private readonly VectorStoreRecordPropertyReader _propertyReader;

    /// <summary>An array of the storage names of all the data properties that are part of the Redis payload, i.e. all properties except the key and vector properties.</summary>
    private readonly string[] _dataStoragePropertyNames;

    /// <summary>The mapper to use when mapping between the consumer data model and the Redis record.</summary>
    private readonly IVectorStoreRecordMapper<TRecord, (string Key, JsonNode Node)> _mapper;

    /// <summary>The JSON serializer options to use when converting between the data model and the Redis record.</summary>
    private readonly JsonSerializerOptions _jsonSerializerOptions;

    /// <summary>
    /// Initializes a new instance of the <see cref="RedisJsonVectorStoreRecordCollection{TRecord}"/> class.
    /// </summary>
    /// <param name="database">The Redis database to read/write records from.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="RedisJsonVectorStoreRecordCollection{TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    /// <exception cref="ArgumentNullException">Throw when parameters are invalid.</exception>
    public RedisJsonVectorStoreRecordCollection(IDatabase database, string collectionName, RedisJsonVectorStoreRecordCollectionOptions<TRecord>? options = null)
    {
        // Verify.
        Verify.NotNull(database);
        Verify.NotNullOrWhiteSpace(collectionName);
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelKeyType(typeof(TRecord), options?.JsonNodeCustomMapper is not null, s_supportedKeyTypes);
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelDefinitionSupplied(typeof(TRecord), options?.VectorStoreRecordDefinition is not null);

        // Assign.
        this._database = database;
        this._collectionName = collectionName;
        this._options = options ?? new RedisJsonVectorStoreRecordCollectionOptions<TRecord>();
        this._jsonSerializerOptions = this._options.JsonSerializerOptions ?? JsonSerializerOptions.Default;
        this._propertyReader = new VectorStoreRecordPropertyReader(
            typeof(TRecord),
            this._options.VectorStoreRecordDefinition,
            new()
            {
                RequiresAtLeastOneVector = false,
                SupportsMultipleKeys = false,
                SupportsMultipleVectors = true,
                JsonSerializerOptions = this._jsonSerializerOptions
            });

        // Validate property types.
        this._propertyReader.VerifyKeyProperties(s_supportedKeyTypes);
        this._propertyReader.VerifyVectorProperties(s_supportedVectorTypes);

        // Lookup storage property names.
        this._dataStoragePropertyNames = this._propertyReader.DataPropertyJsonNames.ToArray();

        // Assign Mapper.
        if (this._options.JsonNodeCustomMapper is not null)
        {
            // Custom Mapper.
            this._mapper = this._options.JsonNodeCustomMapper;
        }
        else if (typeof(TRecord) == typeof(VectorStoreGenericDataModel<string>))
        {
            // Generic data model mapper.
            this._mapper = (IVectorStoreRecordMapper<TRecord, (string Key, JsonNode Node)>)new RedisJsonGenericDataModelMapper(
                this._propertyReader.Properties,
                this._jsonSerializerOptions);
        }
        else
        {
            // Default Mapper.
            this._mapper = new RedisJsonVectorStoreRecordMapper<TRecord>(this._propertyReader.KeyPropertyJsonName, this._jsonSerializerOptions);
        }
    }

    /// <inheritdoc />
    public string CollectionName => this._collectionName;

    /// <inheritdoc />
    public virtual async Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
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
    public virtual Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        // Map the record definition to a schema.
        var schema = RedisVectorStoreCollectionCreateMapping.MapToSchema(this._propertyReader.Properties, this._propertyReader.JsonPropertyNamesMap, useDollarPrefix: true);

        // Create the index creation params.
        // Add the collection name and colon as the index prefix, which means that any record where the key is prefixed with this text will be indexed by this index
        var createParams = new FTCreateParams()
            .AddPrefix($"{this._collectionName}:")
            .On(IndexDataType.JSON);

        // Create the index.
        return this.RunOperationAsync("FT.CREATE", () => this._database.FT().CreateAsync(this._collectionName, createParams, schema));
    }

    /// <inheritdoc />
    public virtual async Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
    {
        if (!await this.CollectionExistsAsync(cancellationToken).ConfigureAwait(false))
        {
            await this.CreateCollectionAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc />
    public virtual async Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            await this.RunOperationAsync("FT.DROPINDEX",
                () => this._database.FT().DropIndexAsync(this._collectionName)).ConfigureAwait(false);
        }
        catch (VectorStoreOperationException ex) when (ex.InnerException is RedisServerException)
        {
            // The RedisServerException does not expose any reliable way of checking if the index does not exist.
            // It just sets the message to "Unknown index name".
            // We catch the exception and ignore it, but only after checking that the index does not exist.
            if (!await this.CollectionExistsAsync(cancellationToken).ConfigureAwait(false))
            {
                return;
            }

            throw;
        }
    }

    /// <inheritdoc />
    public virtual async Task<TRecord?> GetAsync(string key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
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
                    .GetAsync(maybePrefixedKey, this._dataStoragePropertyNames)).ConfigureAwait(false);

        // Check if the key was found before trying to parse the result.
        if (redisResult.IsNull || redisResult is null)
        {
            return default;
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
    public virtual async IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<string> keys, GetRecordOptions? options = default, [EnumeratorCancellation] CancellationToken cancellationToken = default)
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
    public virtual Task DeleteAsync(string key, CancellationToken cancellationToken = default)
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
    public virtual Task DeleteBatchAsync(IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        // Remove records in parallel.
        var tasks = keys.Select(key => this.DeleteAsync(key, cancellationToken));
        return Task.WhenAll(tasks);
    }

    /// <inheritdoc />
    public virtual async Task<string> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
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
    public virtual async IAsyncEnumerable<string> UpsertBatchAsync(IEnumerable<TRecord> records, [EnumeratorCancellation] CancellationToken cancellationToken = default)
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

    /// <inheritdoc />
    public virtual async Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(vector);

        var internalOptions = options ?? s_defaultVectorSearchOptions;
        var vectorProperty = this._propertyReader.GetVectorPropertyOrSingle(internalOptions);

        // Build query & search.
        byte[] vectorBytes = RedisVectorStoreCollectionSearchMapping.ValidateVectorAndConvertToBytes(vector, "JSON");
        var query = RedisVectorStoreCollectionSearchMapping.BuildQuery(
            vectorBytes,
            internalOptions,
            this._propertyReader.JsonPropertyNamesMap,
            this._propertyReader.GetJsonPropertyName(vectorProperty.DataModelPropertyName),
            null);
        var results = await this.RunOperationAsync(
            "FT.SEARCH",
            () => this._database
                .FT()
                .SearchAsync(this._collectionName, query)).ConfigureAwait(false);

        // Loop through result and convert to the caller's data model.
        var mappedResults = results.Documents.Select(result =>
        {
            var redisResultString = result["json"].ToString();
            var mappedRecord = VectorStoreErrorHandler.RunModelConversion(
                DatabaseName,
                this._collectionName,
                "FT.SEARCH",
                () =>
                {
                    var node = JsonSerializer.Deserialize<JsonNode>(redisResultString, this._jsonSerializerOptions)!;
                    return this._mapper.MapFromStorageToDataModel(
                        (this.RemoveKeyPrefixIfNeeded(result.Id), node),
                        new() { IncludeVectors = internalOptions.IncludeVectors });
                });

            // Process the score of the result item.
            var vectorProperty = this._propertyReader.GetVectorPropertyOrSingle(internalOptions);
            var distanceFunction = RedisVectorStoreCollectionSearchMapping.ResolveDistanceFunction(vectorProperty);
            var score = RedisVectorStoreCollectionSearchMapping.GetOutputScoreFromRedisScore(result["vector_score"].HasValue ? (float)result["vector_score"] : null, distanceFunction);

            return new VectorSearchResult<TRecord>(mappedRecord, score);
        });

        return new VectorSearchResults<TRecord>(mappedResults.ToAsyncEnumerable());
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
    /// Remove the prefix of the given key if the option is set.
    /// </summary>
    /// <param name="key">The key to remove a prefix from.</param>
    /// <returns>The updated key if updating is required, otherwise the input key.</returns>
    private string RemoveKeyPrefixIfNeeded(string key)
    {
        var prefixLength = this._collectionName.Length + 1;

        if (this._options.PrefixCollectionNameToKeyNames && key.Length > prefixLength)
        {
            return key.Substring(prefixLength);
        }

        return key;
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
        catch (RedisException ex)
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
        catch (RedisException ex)
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
