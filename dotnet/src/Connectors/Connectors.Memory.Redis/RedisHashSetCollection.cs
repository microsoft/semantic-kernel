// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Linq.Expressions;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using NRedisStack.RedisStackCommands;
using NRedisStack.Search;
using NRedisStack.Search.Literals.Enums;
using StackExchange.Redis;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Service for storing and retrieving vector records, that uses Redis HashSets as the underlying storage.
/// </summary>
/// <typeparam name="TKey">The data type of the record key. Can be either <see cref="string"/>, or <see cref="object"/> for dynamic mapping.</typeparam>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class RedisHashSetCollection<TKey, TRecord> : VectorStoreCollection<TKey, TRecord>
    where TKey : notnull
    where TRecord : class
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    /// <summary>Metadata about vector store record collection.</summary>
    private readonly VectorStoreCollectionMetadata _collectionMetadata;

    /// <summary>A set of types that vectors on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedVectorTypes =
    [
        typeof(ReadOnlyMemory<float>),
        typeof(ReadOnlyMemory<double>),
        typeof(ReadOnlyMemory<float>?),
        typeof(ReadOnlyMemory<double>?)
    ];

    internal static readonly CollectionModelBuildingOptions ModelBuildingOptions = new()
    {
        RequiresAtLeastOneVector = false,
        SupportsMultipleKeys = false,
        SupportsMultipleVectors = true,

        SupportedKeyPropertyTypes = [typeof(string)],

        SupportedDataPropertyTypes =
        [
            typeof(string),
            typeof(int),
            typeof(uint),
            typeof(long),
            typeof(ulong),
            typeof(double),
            typeof(float),
            typeof(bool)
        ],

        SupportedEnumerableDataPropertyElementTypes = [],

        SupportedVectorPropertyTypes = s_supportedVectorTypes
    };

    /// <summary>The default options for vector search.</summary>
    private static readonly RecordSearchOptions<TRecord> s_defaultVectorSearchOptions = new();

    /// <summary>The Redis database to read/write records from.</summary>
    private readonly IDatabase _database;

    /// <summary>The model.</summary>
    private readonly CollectionModel _model;

    /// <summary>An array of the names of all the data properties that are part of the Redis payload as RedisValue objects, i.e. all properties except the key and vector properties.</summary>
    private readonly RedisValue[] _dataStoragePropertyNameRedisValues;

    /// <summary>An array of the names of all the data properties that are part of the Redis payload, i.e. all properties except the key and vector properties, plus the generated score property.</summary>
    private readonly string[] _dataStoragePropertyNamesWithScore;

    /// <summary>The mapper to use when mapping between the consumer data model and the Redis record.</summary>
    private readonly RedisHashSetMapper<TRecord> _mapper;

    /// <summary>whether the collection name should be prefixed to the key names before reading or writing to the Redis store.</summary>
    private readonly bool _prefixCollectionNameToKeyNames;

    /// <summary>
    /// Initializes a new instance of the <see cref="RedisHashSetCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="database">The Redis database to read/write records from.</param>
    /// <param name="name">The name of the collection that this <see cref="RedisHashSetCollection{TKey, TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    /// <exception cref="ArgumentNullException">Throw when parameters are invalid.</exception>
    public RedisHashSetCollection(IDatabase database, string name, RedisHashSetCollectionOptions? options = null)
    {
        // Verify.
        Verify.NotNull(database);
        Verify.NotNullOrWhiteSpace(name);

        if (typeof(TKey) != typeof(string) && typeof(TKey) != typeof(object))
        {
            throw new NotSupportedException("Only string keys are supported (and object for dynamic mapping).");
        }

        // Assign.
        this._database = database;
        this.Name = name;

        options ??= RedisHashSetCollectionOptions.Default;
        this._prefixCollectionNameToKeyNames = options.PrefixCollectionNameToKeyNames;

        this._model = new CollectionModelBuilder(ModelBuildingOptions)
            .Build(typeof(TRecord), options.VectorStoreRecordDefinition, options.EmbeddingGenerator);

        // Lookup storage property names.
        this._dataStoragePropertyNameRedisValues = this._model.DataProperties.Select(p => RedisValue.Unbox(p.StorageName)).ToArray();
        this._dataStoragePropertyNamesWithScore = [.. this._model.DataProperties.Select(p => p.StorageName), "vector_score"];

        // Assign Mapper.
        this._mapper = new RedisHashSetMapper<TRecord>(this._model);

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
    public override Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        // Map the record definition to a schema.
        var schema = RedisCollectionCreateMapping.MapToSchema(this._model.Properties, useDollarPrefix: false);

        // Create the index creation params.
        // Add the collection name and colon as the index prefix, which means that any record where the key is prefixed with this text will be indexed by this index
        var createParams = new FTCreateParams()
            .AddPrefix($"{this.Name}:")
            .On(IndexDataType.HASH);

        // Create the index.
        return this.RunOperationAsync("FT.CREATE", () => this._database.FT().CreateAsync(this.Name, createParams, schema));
    }

    /// <inheritdoc />
    public override async Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
    {
        if (!await this.CollectionExistsAsync(cancellationToken).ConfigureAwait(false))
        {
            await this.CreateCollectionAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc />
    public override async Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
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
        if (includeVectors && this._model.VectorProperties.Any(p => p.EmbeddingGenerator is not null))
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

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
            var fieldKeys = this._dataStoragePropertyNameRedisValues;
            var retrievedValues = await this.RunOperationAsync(
                operationName,
                () => this._database.HashGetAsync(maybePrefixedKey, fieldKeys)).ConfigureAwait(false);
            retrievedHashEntries = fieldKeys.Zip(retrievedValues, (field, value) => new HashEntry(field, value)).Where(x => x.Value.HasValue).ToArray();
        }

        // Return null if we found nothing.
        if (retrievedHashEntries == null || retrievedHashEntries.Length == 0)
        {
            return default;
        }

        // Convert to the caller's data model.
        return this._mapper.MapFromStorageToDataModel((stringKey, retrievedHashEntries), includeVectors);
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
                .KeyDeleteAsync(maybePrefixedKey));
    }

    /// <inheritdoc />
    public override async Task UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        (_, var generatedEmbeddings) = await RedisFieldMapping.ProcessEmbeddingsAsync<TRecord>(this._model, [record], cancellationToken).ConfigureAwait(false);

        await this.UpsertCoreAsync(record, 0, generatedEmbeddings, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public override async Task UpsertAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        (records, var generatedEmbeddings) = await RedisFieldMapping.ProcessEmbeddingsAsync<TRecord>(this._model, records, cancellationToken).ConfigureAwait(false);

        var i = 0;

        foreach (var record in records)
        {
            await this.UpsertCoreAsync(record, i++, generatedEmbeddings, cancellationToken).ConfigureAwait(false);
        }
    }

    private async Task UpsertCoreAsync(TRecord record, int recordIndex, IReadOnlyList<Embedding>?[]? generatedEmbeddings, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        // Map.
        var redisHashSetRecord = this._mapper.MapFromDataToStorageModel(record, recordIndex, generatedEmbeddings);

        // Upsert.
        var maybePrefixedKey = this.PrefixKeyIfNeeded(redisHashSetRecord.Key);

        await this.RunOperationAsync(
            "HSET",
            () => this._database
                .HashSetAsync(
                    maybePrefixedKey,
                    redisHashSetRecord.HashEntries)).ConfigureAwait(false);
    }

    #region Search

    /// <inheritdoc />
    public override async IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TInput>(
        TInput value,
        int top,
        RecordSearchOptions<TRecord>? options = default,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        options ??= s_defaultVectorSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle(options);

        switch (vectorProperty.EmbeddingGenerator)
        {
            case IEmbeddingGenerator<TInput, Embedding<float>> generator:
            {
                var embedding = await generator.GenerateEmbeddingAsync(value, new() { Dimensions = vectorProperty.Dimensions }, cancellationToken).ConfigureAwait(false);

                await foreach (var record in this.SearchCoreAsync(embedding.Vector, top, vectorProperty, operationName: "Search", options, cancellationToken).ConfigureAwait(false))
                {
                    yield return record;
                }

                yield break;
            }

            case IEmbeddingGenerator<TInput, Embedding<double>> generator:
            {
                var embedding = await generator.GenerateEmbeddingAsync(value, new() { Dimensions = vectorProperty.Dimensions }, cancellationToken).ConfigureAwait(false);

                await foreach (var record in this.SearchCoreAsync(embedding.Vector, top, vectorProperty, operationName: "Search", options, cancellationToken).ConfigureAwait(false))
                {
                    yield return record;
                }

                yield break;
            }

            case null:
                throw new InvalidOperationException(VectorDataStrings.NoEmbeddingGeneratorWasConfiguredForSearch);

            default:
                throw new InvalidOperationException(
                    s_supportedVectorTypes.Contains(typeof(TInput))
                        ? VectorDataStrings.EmbeddingTypePassedToSearchAsync
                        : VectorDataStrings.IncompatibleEmbeddingGeneratorWasConfiguredForInputType(typeof(TInput), vectorProperty.EmbeddingGenerator.GetType()));
        }
    }

    /// <inheritdoc />
    public override IAsyncEnumerable<VectorSearchResult<TRecord>> SearchEmbeddingAsync<TVector>(
        TVector vector,
        int top,
        RecordSearchOptions<TRecord>? options = null,
        CancellationToken cancellationToken = default)
    {
        options ??= s_defaultVectorSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle(options);

        return this.SearchCoreAsync(vector, top, vectorProperty, operationName: "SearchEmbedding", options, cancellationToken);
    }

    private async IAsyncEnumerable<VectorSearchResult<TRecord>> SearchCoreAsync<TVector>(
        TVector vector,
        int top,
        VectorPropertyModel vectorProperty,
        string operationName,
        RecordSearchOptions<TRecord> options,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
        where TVector : notnull
    {
        Verify.NotNull(vector);
        Verify.NotLessThan(top, 1);

        if (options.IncludeVectors && this._model.VectorProperties.Any(p => p.EmbeddingGenerator is not null))
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        // Build query & search.
        var selectFields = options.IncludeVectors ? null : this._dataStoragePropertyNamesWithScore;
        byte[] vectorBytes = RedisCollectionSearchMapping.ValidateVectorAndConvertToBytes(vector, "HashSet");
        var query = RedisCollectionSearchMapping.BuildQuery(
            vectorBytes,
            top,
            options,
            this._model,
            vectorProperty,
            selectFields);
        var results = await this.RunOperationAsync(
            "FT.SEARCH",
            () => this._database
                .FT()
                .SearchAsync(this.Name, query)).ConfigureAwait(false);

        // Loop through result and convert to the caller's data model.
        var mappedResults = results.Documents.Select(result =>
        {
            var retrievedHashEntries = this._model.DataProperties.Select(p => p.StorageName)
                .Concat(this._model.VectorProperties.Select(p => p.StorageName))
                .Select(propertyName => new HashEntry(propertyName, result[propertyName]))
                .ToArray();

            // Convert to the caller's data model.
            var dataModel = this._mapper.MapFromStorageToDataModel((this.RemoveKeyPrefixIfNeeded(result.Id), retrievedHashEntries), options.IncludeVectors);

            // Process the score of the result item.
            var vectorProperty = this._model.GetVectorPropertyOrSingle(options);
            var distanceFunction = RedisCollectionSearchMapping.ResolveDistanceFunction(vectorProperty);
            var score = RedisCollectionSearchMapping.GetOutputScoreFromRedisScore(result["vector_score"].HasValue ? (float)result["vector_score"] : null, distanceFunction);

            return new VectorSearchResult<TRecord>(dataModel, score);
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

        options ??= new();

        if (options.IncludeVectors && this._model.VectorProperties.Any(p => p.EmbeddingGenerator is not null))
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        Query query = RedisCollectionSearchMapping.BuildQuery(filter, top, options, this._model);

        var results = await this.RunOperationAsync(
            "FT.SEARCH",
            () => this._database
                .FT()
                .SearchAsync(this.Name, query)).ConfigureAwait(false);

        foreach (var document in results.Documents)
        {
            var retrievedHashEntries = this._model.DataProperties.Select(p => p.StorageName)
                .Concat(this._model.VectorProperties.Select(p => p.StorageName))
                .Select(propertyName => new HashEntry(propertyName, document[propertyName]))
                .ToArray();

            // Convert to the caller's data model.
            yield return this._mapper.MapFromStorageToDataModel((this.RemoveKeyPrefixIfNeeded(document.Id), retrievedHashEntries), options.IncludeVectors);
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
