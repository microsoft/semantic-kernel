// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Linq.Expressions;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using NRedisStack.Json.DataTypes;
using NRedisStack.RedisStackCommands;
using NRedisStack.Search;
using NRedisStack.Search.Literals.Enums;
using StackExchange.Redis;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Service for storing and retrieving vector records, that uses Redis JSON as the underlying storage.
/// </summary>
/// <typeparam name="TKey">The data type of the record key. Must be <see cref="string"/>.</typeparam>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public class RedisJsonCollection<TKey, TRecord> : VectorStoreCollection<TKey, TRecord>
    where TKey : notnull
    where TRecord : class
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    /// <summary>Metadata about vector store record collection.</summary>
    private readonly VectorStoreCollectionMetadata _collectionMetadata;

    internal static readonly CollectionModelBuildingOptions ModelBuildingOptions = new()
    {
        RequiresAtLeastOneVector = false,
        SupportsMultipleKeys = false,
        SupportsMultipleVectors = true,
        UsesExternalSerializer = true
    };

    /// <summary>The default options for vector search.</summary>
    private static readonly VectorSearchOptions<TRecord> s_defaultVectorSearchOptions = new();

    /// <summary>The Redis database to read/write records from.</summary>
    private readonly IDatabase _database;

    /// <summary>The model.</summary>
    private readonly CollectionModel _model;

    /// <summary>An array of the storage names of all the data properties that are part of the Redis payload, i.e. all properties except the key and vector properties.</summary>
    private readonly string[] _dataStoragePropertyNames;

    /// <summary>The mapper to use when mapping between the consumer data model and the Redis record.</summary>
    private readonly IRedisJsonMapper<TRecord> _mapper;

    /// <summary>The JSON serializer options to use when converting between the data model and the Redis record.</summary>
    private readonly JsonSerializerOptions _jsonSerializerOptions;

    /// <summary>whether the collection name should be prefixed to the key names before reading or writing to the Redis store.</summary>
    private readonly bool _prefixCollectionNameToKeyNames;

    /// <summary>
    /// Initializes a new instance of the <see cref="RedisJsonCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="database">The Redis database to read/write records from.</param>
    /// <param name="name">The name of the collection that this <see cref="RedisJsonCollection{TKey, TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    /// <exception cref="ArgumentNullException">Throw when parameters are invalid.</exception>
    // TODO: The provider uses unsafe JSON serialization in many places, #11963
    [RequiresUnreferencedCode("The Weaviate provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The Weaviate provider is currently incompatible with NativeAOT.")]
    public RedisJsonCollection(IDatabase database, string name, RedisJsonCollectionOptions? options = null)
        : this(
            database,
            name,
            static options => typeof(TRecord) == typeof(Dictionary<string, object?>)
                ? throw new NotSupportedException(VectorDataStrings.NonDynamicCollectionWithDictionaryNotSupported(typeof(RedisJsonDynamicCollection)))
                : new RedisJsonModelBuilder(ModelBuildingOptions)
                    .Build(
                        typeof(TRecord),
                        options.Definition,
                        options.EmbeddingGenerator,
                        options.JsonSerializerOptions ?? JsonSerializerOptions.Default),
            options)
    {
    }

    internal RedisJsonCollection(IDatabase database, string name, Func<RedisJsonCollectionOptions, CollectionModel> modelFactory, RedisJsonCollectionOptions? options)
    {
        // Verify.
        Verify.NotNull(database);
        Verify.NotNullOrWhiteSpace(name);

        if (typeof(TKey) != typeof(string) && typeof(TKey) != typeof(object))
        {
            throw new NotSupportedException("Only string keys are supported.");
        }

        var isDynamic = typeof(TRecord) == typeof(Dictionary<string, object?>);

        options ??= RedisJsonCollectionOptions.Default;

        // Assign.
        this._database = database;
        this.Name = name;
        this._model = modelFactory(options);

        this._prefixCollectionNameToKeyNames = options.PrefixCollectionNameToKeyNames;
        this._jsonSerializerOptions = options.JsonSerializerOptions ?? JsonSerializerOptions.Default;

        // Lookup storage property names.
        this._dataStoragePropertyNames = this._model.DataProperties.Select(p => p.StorageName).ToArray();

        // Assign Mapper.
        this._mapper = isDynamic
            ? (IRedisJsonMapper<TRecord>)new RedisJsonDynamicMapper(this._model, this._jsonSerializerOptions)
            : new RedisJsonMapper<TRecord>(this._model, this._jsonSerializerOptions);

        this._collectionMetadata = new()
        {
            VectorStoreSystemName = RedisConstants.VectorStoreSystemName,
            VectorStoreName = database.Database.ToString(),
            CollectionName = name
        };
    }

    /// <inheritdoc />
    public override string Name { get; }

    /// <inheritdoc />
    public override async Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            await this._database.FT().InfoAsync(this.Name).ConfigureAwait(false);
            return true;
        }
        catch (RedisServerException ex) when (ex.Message.Contains("Unknown index name"))
        {
            return false;
        }
        catch (RedisConnectionException ex)
        {
            throw new VectorStoreException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = RedisConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this.Name,
                OperationName = "FT.INFO"
            };
        }
    }

    /// <inheritdoc />
    public override async Task EnsureCollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "FT.CREATE";

        // Don't even try to create if the collection already exists.
        if (await this.CollectionExistsAsync(cancellationToken).ConfigureAwait(false))
        {
            return;
        }

        try
        {
            // Map the record definition to a schema.
            var schema = RedisCollectionCreateMapping.MapToSchema(this._model.Properties, useDollarPrefix: true);

            // Create the index creation params.
            // Add the collection name and colon as the index prefix, which means that any record where the key is prefixed with this text will be indexed by this index
            var createParams = new FTCreateParams()
                .AddPrefix($"{this.Name}:")
                .On(IndexDataType.JSON);

            // Create the index.
            await this._database.FT().CreateAsync(this.Name, createParams, schema).ConfigureAwait(false);
        }
        catch (RedisException ex)
        {
            // Since redis only returns textual error messages, we can check here if the index already exists.
            // If it does, we can ignore the error.
#pragma warning disable CA1031 // Do not catch general exception types
            try
            {
                if (await this.CollectionExistsAsync(cancellationToken).ConfigureAwait(false))
                {
                    return;
                }
            }
            catch
            {
            }
#pragma warning restore CA1031 // Do not catch general exception types

            throw new VectorStoreException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = RedisConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this.Name,
                OperationName = OperationName
            };
        }
    }

    /// <inheritdoc />
    public override async Task EnsureCollectionDeletedAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            await this.RunOperationAsync("FT.DROPINDEX",
                () => this._database.FT().DropIndexAsync(this.Name)).ConfigureAwait(false);
        }
        catch (VectorStoreException ex) when (ex.InnerException is RedisServerException)
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
    public override async Task<TRecord?> GetAsync(TKey key, RecordRetrievalOptions? options = null, CancellationToken cancellationToken = default)
    {
        var stringKey = this.GetStringKey(key);

        // Create Options
        var maybePrefixedKey = this.PrefixKeyIfNeeded(stringKey);
        var includeVectors = options?.IncludeVectors ?? false;
        if (includeVectors && this._model.EmbeddingGenerationRequired)
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

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
            throw new InvalidOperationException($"Document with key '{key}' does not contain any json.");
        }

        // Convert to the caller's data model.
        var node = JsonSerializer.Deserialize<JsonNode>(redisResultString, this._jsonSerializerOptions)!;
        return this._mapper.MapFromStorageToDataModel((stringKey, node), includeVectors);
    }

    /// <inheritdoc />
    public override async IAsyncEnumerable<TRecord> GetAsync(IEnumerable<TKey> keys, RecordRetrievalOptions? options = default, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

#pragma warning disable CA1851 // Possible multiple enumerations of 'IEnumerable' collection
        var keysList = keys switch
        {
            IEnumerable<string> k => k.ToList(),
            IEnumerable<object> k => k.Cast<string>().ToList(),
            _ => throw new UnreachableException()
        };
#pragma warning restore CA1851 // Possible multiple enumerations of 'IEnumerable' collection

        // Create Options
        var maybePrefixedKeys = keysList.Select(key => this.PrefixKeyIfNeeded(key));
        var redisKeys = maybePrefixedKeys.Select(x => new RedisKey(x)).ToArray();
        var includeVectors = options?.IncludeVectors ?? false;
        if (includeVectors && this._model.EmbeddingGenerationRequired)
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

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
                throw new InvalidOperationException($"Document with key '{key}' does not contain any json.");
            }

            // Convert to the caller's data model.
            var node = JsonSerializer.Deserialize<JsonNode>(redisResultString, this._jsonSerializerOptions)!;
            yield return this._mapper.MapFromStorageToDataModel((key, node), includeVectors);
        }
    }

    /// <inheritdoc />
    public override Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        var stringKey = this.GetStringKey(key);

        // Create Options
        var maybePrefixedKey = this.PrefixKeyIfNeeded(stringKey);

        // Remove.
        return this.RunOperationAsync(
            "DEL",
            () => this._database
                .JSON()
                .DelAsync(maybePrefixedKey));
    }

    /// <inheritdoc />
    public override async Task UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        // Map.
        (_, var generatedEmbeddings) = await RedisFieldMapping.ProcessEmbeddingsAsync<TRecord>(this._model, [record], cancellationToken).ConfigureAwait(false);

        var mapResult = this._mapper.MapFromDataToStorageModel(record, recordIndex: 0, generatedEmbeddings);
        var serializedRecord = JsonSerializer.Serialize(mapResult.Node, this._jsonSerializerOptions);
        var redisJsonRecord = new { Key = mapResult.Key, SerializedRecord = serializedRecord };

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
    }

    /// <inheritdoc />
    public override async Task UpsertAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        // Map.
        (records, var generatedEmbeddings) = await RedisFieldMapping.ProcessEmbeddingsAsync<TRecord>(this._model, records, cancellationToken).ConfigureAwait(false);

        var redisRecords = new List<(string maybePrefixedKey, string originalKey, string serializedRecord)>();

        var recordIndex = 0;

        foreach (var record in records)
        {
            var mapResult = this._mapper.MapFromDataToStorageModel(record, recordIndex++, generatedEmbeddings);
            var serializedRecord = JsonSerializer.Serialize(mapResult.Node, this._jsonSerializerOptions);
            var redisJsonRecord = new { Key = mapResult.Key, SerializedRecord = serializedRecord };

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

        object vector = searchValue switch
        {
            // float32
            ReadOnlyMemory<float> r => r,
            float[] f => new ReadOnlyMemory<float>(f),
            Embedding<float> e => e.Vector,
            _ when vectorProperty.EmbeddingGenerator is IEmbeddingGenerator<TInput, Embedding<float>> generator
                => await generator.GenerateVectorAsync(searchValue, cancellationToken: cancellationToken).ConfigureAwait(false),

            // float64
            ReadOnlyMemory<double> r => r,
            double[] f => new ReadOnlyMemory<double>(f),
            Embedding<double> e => e.Vector,
            _ when vectorProperty.EmbeddingGenerator is IEmbeddingGenerator<TInput, Embedding<double>> generator
                => await generator.GenerateVectorAsync(searchValue, cancellationToken: cancellationToken).ConfigureAwait(false),

            _ => vectorProperty.EmbeddingGenerator is null
                ? throw new NotSupportedException(VectorDataStrings.InvalidSearchInputAndNoEmbeddingGeneratorWasConfigured(searchValue.GetType(), RedisModelBuilder.SupportedVectorTypes))
                : throw new InvalidOperationException(VectorDataStrings.IncompatibleEmbeddingGeneratorWasConfiguredForInputType(typeof(TInput), vectorProperty.EmbeddingGenerator.GetType()))
        };

        // Build query & search.
        byte[] vectorBytes = RedisCollectionSearchMapping.ValidateVectorAndConvertToBytes(vector, "JSON");
        var query = RedisCollectionSearchMapping.BuildQuery(
            vectorBytes,
            top,
            options,
            this._model,
            vectorProperty,
            null);
        var results = await this.RunOperationAsync(
            "FT.SEARCH",
            () => this._database
                .FT()
                .SearchAsync(this.Name, query)).ConfigureAwait(false);

        // Loop through result and convert to the caller's data model.
        var mappedResults = results.Documents.Select(result =>
        {
            var redisResultString = result["json"].ToString();
            var node = JsonSerializer.Deserialize<JsonNode>(redisResultString, this._jsonSerializerOptions)!;
            var mappedRecord = this._mapper.MapFromStorageToDataModel(
                (this.RemoveKeyPrefixIfNeeded(result.Id), node),
                options.IncludeVectors);

            // Process the score of the result item.
            var vectorProperty = this._model.GetVectorPropertyOrSingle(options);
            var distanceFunction = RedisCollectionSearchMapping.ResolveDistanceFunction(vectorProperty);
            var score = RedisCollectionSearchMapping.GetOutputScoreFromRedisScore(result["vector_score"].HasValue ? (float)result["vector_score"] : null, distanceFunction);

            return new VectorSearchResult<TRecord>(mappedRecord, score);
        });

        foreach (var result in mappedResults)
        {
            yield return result;
        }
    }

    #endregion Search

    /// <inheritdoc />
    public override async IAsyncEnumerable<TRecord> GetAsync(Expression<Func<TRecord, bool>> filter, int top,
        FilteredRecordRetrievalOptions<TRecord>? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(filter);
        Verify.NotLessThan(top, 1);

        if (options?.IncludeVectors == true && this._model.EmbeddingGenerationRequired)
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        Query query = RedisCollectionSearchMapping.BuildQuery(filter, top, options ??= new(), this._model);

        var results = await this.RunOperationAsync(
            "FT.SEARCH",
            () => this._database
                .FT()
                .SearchAsync(this.Name, query)).ConfigureAwait(false);

        foreach (var document in results.Documents)
        {
            var redisResultString = document["json"].ToString();
            var node = JsonSerializer.Deserialize<JsonNode>(redisResultString, this._jsonSerializerOptions)!;
            yield return this._mapper.MapFromStorageToDataModel(
                (this.RemoveKeyPrefixIfNeeded(document.Id), node),
                options.IncludeVectors);
        }
    }

    /// <inheritdoc />
    public override object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreCollectionMetadata) ? this._collectionMetadata :
            serviceType == typeof(IDatabase) ? this._database :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }

    /// <summary>
    /// Prefix the key with the collection name if the option is set.
    /// </summary>
    /// <param name="key">The key to prefix.</param>
    /// <returns>The updated key if updating is required, otherwise the input key.</returns>
    private string PrefixKeyIfNeeded(string key)
    {
        if (this._prefixCollectionNameToKeyNames)
        {
            return $"{this.Name}:{key}";
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
        var prefixLength = this.Name.Length + 1;

        if (this._prefixCollectionNameToKeyNames && key.Length > prefixLength)
        {
            return key.Substring(prefixLength);
        }

        return key;
    }

    /// <summary>
    /// Run the given operation and wrap any Redis exceptions with <see cref="VectorStoreException"/>."/>
    /// </summary>
    /// <typeparam name="T">The response type of the operation.</typeparam>
    /// <param name="operationName">The type of database operation being run.</param>
    /// <param name="operation">The operation to run.</param>
    /// <returns>The result of the operation.</returns>
    private Task<T> RunOperationAsync<T>(string operationName, Func<Task<T>> operation)
        => VectorStoreErrorHandler.RunOperationAsync<T, RedisException>(
            this._collectionMetadata,
            operationName,
            operation);

    /// <summary>
    /// Run the given operation and wrap any Redis exceptions with <see cref="VectorStoreException"/>."/>
    /// </summary>
    /// <param name="operationName">The type of database operation being run.</param>
    /// <param name="operation">The operation to run.</param>
    /// <returns>The result of the operation.</returns>
    private Task RunOperationAsync(string operationName, Func<Task> operation)
        => VectorStoreErrorHandler.RunOperationAsync<RedisException>(
            this._collectionMetadata,
            operationName,
            operation);

    private string GetStringKey(TKey key)
    {
        Verify.NotNull(key);

        var stringKey = key as string ?? throw new UnreachableException("string key should have been validated during model building");

        Verify.NotNullOrWhiteSpace(stringKey, nameof(key));

        return stringKey;
    }
}
