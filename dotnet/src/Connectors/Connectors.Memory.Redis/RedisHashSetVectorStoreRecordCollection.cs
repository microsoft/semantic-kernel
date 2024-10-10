<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
﻿// Copyright (c) Microsoft. All rights reserved.
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
﻿// Copyright (c) Microsoft. All rights reserved.
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes

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

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
    /// <summary>The default options for vector search.</summary>
    private static readonly VectorSearchOptions s_defaultVectorSearchOptions = new();

>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    /// <summary>The default options for vector search.</summary>
    private static readonly VectorSearchOptions s_defaultVectorSearchOptions = new();

>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
    /// <summary>The Redis database to read/write records from.</summary>
    private readonly IDatabase _database;

    /// <summary>The name of the collection that this <see cref="RedisHashSetVectorStoreRecordCollection{TRecord}"/> will access.</summary>
    private readonly string _collectionName;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly RedisHashSetVectorStoreRecordCollectionOptions<TRecord> _options;

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
    /// <summary>A definition of the current storage model.</summary>
    private readonly VectorStoreRecordDefinition _vectorStoreRecordDefinition;

=======
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    /// <summary>A definition of the current storage model.</summary>
    private readonly VectorStoreRecordDefinition _vectorStoreRecordDefinition;

=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
    /// <summary>A helper to access property information for the current data model and record definition.</summary>
    private readonly VectorStoreRecordPropertyReader _propertyReader;

    /// <summary>An array of the names of all the data properties that are part of the Redis payload as RedisValue objects, i.e. all properties except the key and vector properties.</summary>
    private readonly RedisValue[] _dataStoragePropertyNameRedisValues;

    /// <summary>An array of the names of all the data properties that are part of the Redis payload, i.e. all properties except the key and vector properties.</summary>
    private readonly string[] _dataStoragePropertyNames;

    /// <summary>An array of the names of all the properties that are part of the Redis payload, i.e. all properties except the key property.</summary>
    private readonly string[] _dataAndVectorStoragePropertyNames;
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
    /// <summary>An array of the names of all the data properties that are part of the Redis payload, i.e. all properties except the key and vector properties.</summary>
    private readonly RedisValue[] _dataStoragePropertyNames;

    /// <summary>A dictionary that maps from a property name to the storage name that should be used when serializing it to json for data and vector properties.</summary>
    private readonly Dictionary<string, string> _storagePropertyNames = new();

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
    /// <summary>The name of the first vector field for the collections that this class is used with.</summary>
    private readonly string? _firstVectorPropertyName = null;

>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    /// <summary>The name of the first vector field for the collections that this class is used with.</summary>
    private readonly string? _firstVectorPropertyName = null;

>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
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
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelKeyType(typeof(TRecord), options?.HashEntriesCustomMapper is not null, s_supportedKeyTypes);
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelDefinitionSupplied(typeof(TRecord), options?.VectorStoreRecordDefinition is not null);
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelKeyType(typeof(TRecord), options?.HashEntriesCustomMapper is not null, s_supportedKeyTypes);
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelDefinitionSupplied(typeof(TRecord), options?.VectorStoreRecordDefinition is not null);
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes

        // Assign.
        this._database = database;
        this._collectionName = collectionName;
        this._options = options ?? new RedisHashSetVectorStoreRecordCollectionOptions<TRecord>();
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
        this._propertyReader = new VectorStoreRecordPropertyReader(
            typeof(TRecord),
            this._options.VectorStoreRecordDefinition,
            new()
            {
                RequiresAtLeastOneVector = false,
                SupportsMultipleKeys = false,
                SupportsMultipleVectors = true
            });

        // Validate property types.
        this._propertyReader.VerifyKeyProperties(s_supportedKeyTypes);
        this._propertyReader.VerifyDataProperties(s_supportedDataTypes, supportEnumerable: false);
        this._propertyReader.VerifyVectorProperties(s_supportedVectorTypes);

        // Lookup storage property names.
        this._dataStoragePropertyNames = this._propertyReader
            .DataPropertyStoragePropertyNames
            .ToArray();
        this._dataStoragePropertyNameRedisValues = this._dataStoragePropertyNames
            .Select(RedisValue.Unbox)
            .ToArray();
        this._dataAndVectorStoragePropertyNames = properties
            .DataProperties
            .Cast<VectorStoreRecordProperty>()
            .Concat(properties.VectorProperties)
            .Select(x => this._storagePropertyNames[x.DataModelPropertyName])
            .ToArray();

        if (properties.VectorProperties.Count > 0)
        {
            this._firstVectorPropertyName = this._storagePropertyNames[properties.VectorProperties.First().DataModelPropertyName];
        }
        this._dataStoragePropertyNames = this._propertyReader
            .DataPropertyStoragePropertyNames
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
            .Select(RedisValue.Unbox)
            .ToArray();

        // Assign Mapper.
        if (this._options.HashEntriesCustomMapper is not null)
        {
            // Custom Mapper.
            this._mapper = this._options.HashEntriesCustomMapper;
        }
        else if (typeof(TRecord) == typeof(VectorStoreGenericDataModel<string>))
        {
            // Generic data model mapper.
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            this._mapper = (IVectorStoreRecordMapper<TRecord, (string Key, HashEntry[] HashEntries)>)new RedisHashSetGenericDataModelMapper(this._vectorStoreRecordDefinition);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
            this._mapper = (IVectorStoreRecordMapper<TRecord, (string Key, HashEntry[] HashEntries)>)new RedisHashSetGenericDataModelMapper(this._vectorStoreRecordDefinition);
=======
            this._mapper = (IVectorStoreRecordMapper<TRecord, (string Key, HashEntry[] HashEntries)>)new RedisHashSetGenericDataModelMapper(this._propertyReader.Properties);
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
            this._mapper = (IVectorStoreRecordMapper<TRecord, (string Key, HashEntry[] HashEntries)>)new RedisHashSetGenericDataModelMapper(this._propertyReader.Properties);
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
        }
        else
        {
            // Default Mapper.
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            this._mapper = new RedisHashSetVectorStoreRecordMapper<TRecord>(this._vectorStoreRecordDefinition, this._storagePropertyNames);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
            this._mapper = new RedisHashSetVectorStoreRecordMapper<TRecord>(this._vectorStoreRecordDefinition, this._storagePropertyNames);
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
            this._mapper = new RedisHashSetVectorStoreRecordMapper<TRecord>(this._vectorStoreRecordDefinition, this._storagePropertyNames);
=======
>>>>>>> Stashed changes
            this._mapper = this._options.HashEntriesCustomMapper;
        }
        else
        {
            this._mapper = new RedisHashSetVectorStoreRecordMapper<TRecord>(this._vectorStoreRecordDefinition, this._storagePropertyNames);
            this._mapper = new RedisHashSetVectorStoreRecordMapper<TRecord>(this._propertyReader);
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
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
        var schema = RedisVectorStoreCollectionCreateMapping.MapToSchema(this._vectorStoreRecordDefinition.Properties, this._storagePropertyNames, useDollarPrefix: false);
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
<<<<<<< main
        var schema = RedisVectorStoreCollectionCreateMapping.MapToSchema(this._vectorStoreRecordDefinition.Properties, this._storagePropertyNames);
        var schema = RedisVectorStoreCollectionCreateMapping.MapToSchema(this._propertyReader.Properties, this._propertyReader.StoragePropertyNamesMap, useDollarPrefix: false);
=======
        var schema = RedisVectorStoreCollectionCreateMapping.MapToSchema(this._propertyReader.Properties, this._propertyReader.StoragePropertyNamesMap, useDollarPrefix: false);
>>>>>>> upstream/feature-vector-search
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes

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
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
            var fieldKeys = this._dataStoragePropertyNameRedisValues;
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
            var fieldKeys = this._dataStoragePropertyNameRedisValues;
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
            var fieldKeys = this._dataStoragePropertyNameRedisValues;
>>>>>>> main
>>>>>>> Stashed changes
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

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
    /// <inheritdoc />
    public async IAsyncEnumerable<VectorSearchResult<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, VectorSearchOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(vector);

        if (this._propertyReader.FirstVectorPropertyName is null)
        {
            throw new InvalidOperationException("The collection does not have any vector fields, so vector search is not possible.");
        }

        var internalOptions = options ?? s_defaultVectorSearchOptions;

        // Build query & search.
        var selectFields = internalOptions.IncludeVectors ? null : this._dataStoragePropertyNames;
        byte[] vectorBytes = RedisVectorStoreCollectionSearchMapping.ValidateVectorAndConvertToBytes(vector, "HashSet");
        var query = RedisVectorStoreCollectionSearchMapping.BuildQuery(vectorBytes, internalOptions, this._propertyReader.StoragePropertyNamesMap, this._propertyReader.FirstVectorPropertyStoragePropertyName!, selectFields);
        var results = await this.RunOperationAsync(
            "FT.SEARCH",
            () => this._database
                .FT()
                .SearchAsync(this._collectionName, query)).ConfigureAwait(false);

        // Loop through result and convert to the caller's data model.
        foreach (var result in results.Documents)
        {
            var retrievedHashEntries = this._propertyReader.DataPropertyStoragePropertyNames
                .Concat(this._propertyReader.VectorPropertyStoragePropertyNames)
                .Select(propertyName => new HashEntry(propertyName, result[propertyName]))
                .ToArray();

            // Convert to the caller's data model.
            var dataModel = VectorStoreErrorHandler.RunModelConversion(
                DatabaseName,
                this._collectionName,
                "FT.SEARCH",
                () =>
                {
                    return this._mapper.MapFromStorageToDataModel((this.RemoveKeyPrefixIfNeeded(result.Id), retrievedHashEntries), new() { IncludeVectors = internalOptions.IncludeVectors });
                });

            yield return new VectorSearchResult<TRecord>(dataModel, result.Score);
        }
    }

<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
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
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
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
