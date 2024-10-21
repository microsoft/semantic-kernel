<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
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
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
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
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head

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
public sealed class RedisJsonVectorStoreRecordCollection<TRecord> : IVectorStoreRecordCollection<string, TRecord>
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

<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
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
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
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
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< div
>>>>>>> div
=======
    /// <summary>The default options for vector search.</summary>
    private static readonly VectorSearchOptions s_defaultVectorSearchOptions = new();

<<<<<<< main
>>>>>>> upstream/main
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
>>>>>>> div
    /// <summary>The Redis database to read/write records from.</summary>
    private readonly IDatabase _database;

    /// <summary>The name of the collection that this <see cref="RedisJsonVectorStoreRecordCollection{TRecord}"/> will access.</summary>
    private readonly string _collectionName;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly RedisJsonVectorStoreRecordCollectionOptions<TRecord> _options;

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    /// <summary>A definition of the current storage model.</summary>
    private readonly VectorStoreRecordDefinition _vectorStoreRecordDefinition;
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
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    /// <summary>A definition of the current storage model.</summary>
    private readonly VectorStoreRecordDefinition _vectorStoreRecordDefinition;
=======
    /// <summary>A helper to access property information for the current data model and record definition.</summary>
    private readonly VectorStoreRecordPropertyReader _propertyReader;
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
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
    /// <summary>A helper to access property information for the current data model and record definition.</summary>
    private readonly VectorStoreRecordPropertyReader _propertyReader;
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
    /// <summary>A helper to access property information for the current data model and record definition.</summary>
    private readonly VectorStoreRecordPropertyReader _propertyReader;
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head

    /// <summary>An array of the storage names of all the data properties that are part of the Redis payload, i.e. all properties except the key and vector properties.</summary>
    private readonly string[] _dataStoragePropertyNames;

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    /// <summary>A dictionary that maps from a property name to the storage name that should be used when serializing it to json for data and vector properties.</summary>
    private readonly Dictionary<string, string> _storagePropertyNames = new();

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
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    /// <summary>A dictionary that maps from a property name to the storage name that should be used when serializing it to json for data and vector properties.</summary>
    private readonly Dictionary<string, string> _storagePropertyNames = new();

=======
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
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
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
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
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
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
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelKeyType(typeof(TRecord), options?.JsonNodeCustomMapper is not null, s_supportedKeyTypes);
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelDefinitionSupplied(typeof(TRecord), options?.VectorStoreRecordDefinition is not null);
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
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
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelKeyType(typeof(TRecord), options?.JsonNodeCustomMapper is not null, s_supportedKeyTypes);
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelDefinitionSupplied(typeof(TRecord), options?.VectorStoreRecordDefinition is not null);
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelKeyType(typeof(TRecord), options?.JsonNodeCustomMapper is not null, s_supportedKeyTypes);
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelDefinitionSupplied(typeof(TRecord), options?.VectorStoreRecordDefinition is not null);
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head

        // Assign.
        this._database = database;
        this._collectionName = collectionName;
        this._options = options ?? new RedisJsonVectorStoreRecordCollectionOptions<TRecord>();
        this._jsonSerializerOptions = this._options.JsonSerializerOptions ?? JsonSerializerOptions.Default;
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
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
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        this._vectorStoreRecordDefinition = this._options.VectorStoreRecordDefinition ?? VectorStoreRecordPropertyReader.CreateVectorStoreRecordDefinitionFromType(typeof(TRecord), true);

        // Validate property types.
        var properties = VectorStoreRecordPropertyReader.SplitDefinitionAndVerify(typeof(TRecord).Name, this._vectorStoreRecordDefinition, supportsMultipleVectors: true, requiresAtLeastOneVector: false);
        VectorStoreRecordPropertyReader.VerifyPropertyTypes([properties.KeyProperty], s_supportedKeyTypes, "Key");
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(properties.VectorProperties, s_supportedVectorTypes, "Vector");

        // Lookup json storage property names.
        var keyJsonPropertyName = VectorStoreRecordPropertyReader.GetJsonPropertyName(properties.KeyProperty, typeof(TRecord), this._jsonSerializerOptions);
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
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
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head

        // Lookup storage property names.
        this._storagePropertyNames = VectorStoreRecordPropertyReader.BuildPropertyNameToJsonPropertyNameMap(properties, typeof(TRecord), this._jsonSerializerOptions);
        this._dataStoragePropertyNames = properties
            .DataProperties
            .Select(x => this._storagePropertyNames[x.DataModelPropertyName])
            .ToArray();
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
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
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
        var keyJsonPropertyName = this._storagePropertyNames[properties.KeyProperty.DataModelPropertyName];

        if (properties.VectorProperties.Count > 0)
        {
            this._firstVectorPropertyName = this._storagePropertyNames[properties.VectorProperties.First().DataModelPropertyName];
        }
        this._dataStoragePropertyNames = this._propertyReader.DataPropertyJsonNames.ToArray();
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head

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
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
                this._vectorStoreRecordDefinition,
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
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
                this._vectorStoreRecordDefinition,
=======
                this._propertyReader.Properties,
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
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
                this._propertyReader.Properties,
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
                this._propertyReader.Properties,
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
                this._jsonSerializerOptions);
        }
        else
        {
            // Default Mapper.
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            this._mapper = new RedisJsonVectorStoreRecordMapper<TRecord>(keyJsonPropertyName, this._jsonSerializerOptions);
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
>>>>>>> Stashed changes
<<<<<<< HEAD
            this._mapper = new RedisJsonVectorStoreRecordMapper<TRecord>(keyJsonPropertyName, this._jsonSerializerOptions);
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
            this._mapper = new RedisJsonVectorStoreRecordMapper<TRecord>(keyJsonPropertyName, this._jsonSerializerOptions);
=======
>>>>>>> Stashed changes
=======
            this._mapper = new RedisJsonVectorStoreRecordMapper<TRecord>(keyJsonPropertyName, this._jsonSerializerOptions);
=======
>>>>>>> Stashed changes
>>>>>>> head
            this._mapper = this._options.JsonNodeCustomMapper;
        }
        else
        {
            this._mapper = new RedisJsonVectorStoreRecordMapper<TRecord>(keyJsonPropertyName, this._jsonSerializerOptions);
            this._mapper = new RedisJsonVectorStoreRecordMapper<TRecord>(this._propertyReader.KeyPropertyJsonName, this._jsonSerializerOptions);
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
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
        var schema = RedisVectorStoreCollectionCreateMapping.MapToSchema(this._vectorStoreRecordDefinition.Properties, this._storagePropertyNames, useDollarPrefix: true);
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
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
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
        var schema = RedisVectorStoreCollectionCreateMapping.MapToSchema(this._vectorStoreRecordDefinition.Properties, this._storagePropertyNames);
        var schema = RedisVectorStoreCollectionCreateMapping.MapToSchema(this._propertyReader.Properties, this._propertyReader.JsonPropertyNamesMap, useDollarPrefix: true);
=======
        var schema = RedisVectorStoreCollectionCreateMapping.MapToSchema(this._propertyReader.Properties, this._propertyReader.JsonPropertyNamesMap, useDollarPrefix: true);
>>>>>>> upstream/feature-vector-search
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head

        // Create the index creation params.
        // Add the collection name and colon as the index prefix, which means that any record where the key is prefixed with this text will be indexed by this index
        var createParams = new FTCreateParams()
            .AddPrefix($"{this._collectionName}:")
            .On(IndexDataType.JSON);

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

<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
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
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
    /// <inheritdoc />
    public async IAsyncEnumerable<VectorSearchResult<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, VectorSearchOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
=======
    /// <inheritdoc />
    public async Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, VectorSearchOptions? options = null, CancellationToken cancellationToken = default)
>>>>>>> upstream/main
    {
        Verify.NotNull(vector);

        if (this._propertyReader.FirstVectorPropertyName is null)
        {
            throw new InvalidOperationException("The collection does not have any vector fields, so vector search is not possible.");
        }

        var internalOptions = options ?? s_defaultVectorSearchOptions;

        // Build query & search.
        byte[] vectorBytes = RedisVectorStoreCollectionSearchMapping.ValidateVectorAndConvertToBytes(vector, "JSON");
        var query = RedisVectorStoreCollectionSearchMapping.BuildQuery(vectorBytes, internalOptions, this._propertyReader.JsonPropertyNamesMap, this._propertyReader.FirstVectorPropertyJsonName!, null);
        var results = await this.RunOperationAsync(
            "FT.SEARCH",
            () => this._database
                .FT()
                .SearchAsync(this._collectionName, query)).ConfigureAwait(false);

        // Loop through result and convert to the caller's data model.
<<<<<<< main
        foreach (var result in results.Documents)
=======
        var mappedResults = results.Documents.Select(result =>
>>>>>>> upstream/main
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

<<<<<<< main
            yield return new VectorSearchResult<TRecord>(mappedRecord, result.Score);
        }
    }

<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
            return new VectorSearchResult<TRecord>(mappedRecord, result.Score);
        });

        return new VectorSearchResults<TRecord>(mappedResults.ToAsyncEnumerable());
    }

>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
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
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
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
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
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
<<<<<<< main
<<<<<<< main
=======
<<<<<<< div
=======
>>>>>>> div
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
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
