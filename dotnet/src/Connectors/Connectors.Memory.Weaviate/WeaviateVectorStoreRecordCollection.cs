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
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

/// <summary>
/// Service for storing and retrieving vector records, that uses Weaviate as the underlying storage.
/// </summary>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class WeaviateVectorStoreRecordCollection<TRecord> : IVectorStoreRecordCollection<Guid, TRecord>
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    /// <summary>The name of this database for telemetry purposes.</summary>
    private const string DatabaseName = "Weaviate";

    /// <summary>A set of types that a key on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedKeyTypes =
    [
        typeof(Guid)
    ];

    /// <summary>A set of types that vectors on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedVectorTypes =
    [
        typeof(ReadOnlyMemory<float>),
        typeof(ReadOnlyMemory<float>?),
        typeof(ReadOnlyMemory<double>),
        typeof(ReadOnlyMemory<double>?)
    ];

    /// <summary>A set of types that data properties on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedDataTypes =
    [
        typeof(string),
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
        typeof(bool),
        typeof(bool?),
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
        typeof(bool),
        typeof(bool?),
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
        typeof(int),
        typeof(int?),
        typeof(long),
        typeof(long?),
        typeof(short),
        typeof(short?),
        typeof(byte),
        typeof(byte?),
        typeof(float),
        typeof(float?),
        typeof(double),
        typeof(double?),
        typeof(decimal),
        typeof(decimal?),
        typeof(DateTime),
        typeof(DateTime?),
        typeof(DateTimeOffset),
        typeof(DateTimeOffset?),
        typeof(Guid),
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
        typeof(Guid?),
        typeof(bool),
        typeof(bool?)
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
        typeof(Guid?),
        typeof(bool),
        typeof(bool?)
=======
        typeof(Guid?)
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
        typeof(Guid?)
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
        typeof(Guid?)
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
    ];

    /// <summary>Default JSON serializer options.</summary>
    private static readonly JsonSerializerOptions s_jsonSerializerOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
        Converters =
        {
            new WeaviateDateTimeOffsetConverter(),
            new WeaviateNullableDateTimeOffsetConverter()
        }
    };

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
    /// <summary><see cref="HttpClient"/> that is used to interact with Weaviate API.</summary>
    private readonly HttpClient _httpClient;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly WeaviateVectorStoreRecordCollectionOptions<TRecord> _options;

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
    /// <summary>A definition of the current storage model.</summary>
    private readonly VectorStoreRecordDefinition _vectorStoreRecordDefinition;

    /// <summary>A dictionary that maps from a property name to the storage name that should be used when serializing it to JSON for data and vector properties.</summary>
    private readonly Dictionary<string, string> _storagePropertyNames;

    /// <summary>The key property of the current storage model.</summary>
    private readonly VectorStoreRecordKeyProperty _keyProperty;

    /// <summary>The data properties of the current storage model.</summary>
    private readonly List<VectorStoreRecordDataProperty> _dataProperties;

    /// <summary>The vector properties of the current storage model.</summary>
    private readonly List<VectorStoreRecordVectorProperty> _vectorProperties;

    /// <summary>The mapper to use when mapping between the consumer data model and the Weaviate record.</summary>
    private readonly IVectorStoreRecordMapper<TRecord, JsonNode> _mapper;
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
    /// <summary>A helper to access property information for the current data model and record definition.</summary>
    private readonly VectorStoreRecordPropertyReader _propertyReader;

    /// <summary>First vector property for the collections that this class is used with.</summary>
    private readonly VectorStoreRecordVectorProperty? _firstVectorProperty;

    /// <summary>Collection of storage names for data properties of the current storage model.</summary>
    private readonly List<string> _dataPropertyStorageNames;

    /// <summary>Collection of storage names for vector properties of the current storage model.</summary>
    private readonly List<string> _vectorPropertyStorageNames;

    /// <summary>The mapper to use when mapping between the consumer data model and the Weaviate record.</summary>
    private readonly IVectorStoreRecordMapper<TRecord, JsonObject> _mapper;
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

    /// <summary>Weaviate endpoint.</summary>
    private readonly Uri _endpoint;

    /// <summary>Weaviate API key.</summary>
    private readonly string? _apiKey;

    /// <inheritdoc />
    public string CollectionName { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="WeaviateVectorStoreRecordCollection{TRecord}"/> class.
    /// </summary>
    /// <param name="httpClient">
    /// <see cref="HttpClient"/> that is used to interact with Weaviate API.
    /// <see cref="HttpClient.BaseAddress"/> should point to remote or local cluster and API key can be configured via <see cref="HttpClient.DefaultRequestHeaders"/>.
    /// It's also possible to provide these parameters via <see cref="WeaviateVectorStoreRecordCollectionOptions{TRecord}"/>.
    /// </param>
    /// <param name="collectionName">The name of the collection that this <see cref="WeaviateVectorStoreRecordCollection{TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public WeaviateVectorStoreRecordCollection(
        HttpClient httpClient,
        string collectionName,
        WeaviateVectorStoreRecordCollectionOptions<TRecord>? options = default)
    {
        // Verify.
        Verify.NotNull(httpClient);
        Verify.NotNullOrWhiteSpace(collectionName);

        var endpoint = (options?.Endpoint ?? httpClient.BaseAddress) ?? throw new ArgumentException($"Weaviate endpoint should be provided via HttpClient.BaseAddress property or {nameof(WeaviateVectorStoreRecordCollectionOptions<TRecord>)} options parameter.");

        // Assign.
        this._httpClient = httpClient;
        this._endpoint = endpoint;
        this.CollectionName = collectionName;
        this._options = options ?? new();
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
        this._vectorStoreRecordDefinition = this._options.VectorStoreRecordDefinition ?? VectorStoreRecordPropertyReader.CreateVectorStoreRecordDefinitionFromType(typeof(TRecord), supportsMultipleVectors: true);
        this._apiKey = this._options.ApiKey;

        // Validate property types.
        var properties = VectorStoreRecordPropertyReader.SplitDefinitionAndVerify(typeof(TRecord).Name, this._vectorStoreRecordDefinition, supportsMultipleVectors: true, requiresAtLeastOneVector: false);
        VectorStoreRecordPropertyReader.VerifyPropertyTypes([properties.KeyProperty], s_supportedKeyTypes, "Key");
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(properties.DataProperties, s_supportedDataTypes, "Data", supportEnumerable: true);
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(properties.VectorProperties, s_supportedVectorTypes, "Vector");

        // Assign properties and names for later usage.
        this._storagePropertyNames = VectorStoreRecordPropertyReader.BuildPropertyNameToJsonPropertyNameMap(properties, typeof(TRecord), s_jsonSerializerOptions);
        this._keyProperty = properties.KeyProperty;
        this._dataProperties = properties.DataProperties;
        this._vectorProperties = properties.VectorProperties;

        // Assign mapper.
        this._mapper = this._options.JsonNodeCustomMapper ??
            new WeaviateVectorStoreRecordMapper<TRecord>(
                this.CollectionName,
                this._keyProperty,
                this._dataProperties,
                this._vectorProperties,
                this._storagePropertyNames,
                s_jsonSerializerOptions);
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
=======
=======
>>>>>>> Stashed changes
=======
=======
<<<<<<< div
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
>>>>>>> head
        this._apiKey = this._options.ApiKey;
        this._propertyReader = new VectorStoreRecordPropertyReader(
            typeof(TRecord),
            this._options.VectorStoreRecordDefinition,
            new()
            {
                RequiresAtLeastOneVector = false,
                SupportsMultipleKeys = false,
                SupportsMultipleVectors = true,
                JsonSerializerOptions = s_jsonSerializerOptions
            });

        // Validate property types.
        this._propertyReader.VerifyKeyProperties(s_supportedKeyTypes);
        this._propertyReader.VerifyDataProperties(s_supportedDataTypes, supportEnumerable: true);
        this._propertyReader.VerifyVectorProperties(s_supportedVectorTypes);

        if (this._vectorProperties.Count > 0)
        {
            this._firstVectorProperty = this._vectorProperties[0];
        }

        this._dataPropertyStorageNames = this._dataProperties.Select(l => this._storagePropertyNames[l.DataModelPropertyName]).ToList();
        this._vectorPropertyStorageNames = this._vectorProperties.Select(l => this._storagePropertyNames[l.DataModelPropertyName]).ToList();

        // Assign mapper.
        this._mapper = this.InitializeMapper();
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

    /// <inheritdoc />
    public Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "GetCollectionSchema";

        return this.RunOperationAsync(OperationName, async () =>
        {
            var request = new WeaviateGetCollectionSchemaRequest(this.CollectionName).Build();

            var response = await this
                .ExecuteRequestWithNotFoundHandlingAsync<WeaviateGetCollectionSchemaResponse>(request, cancellationToken)
                .ConfigureAwait(false);

            return response != null;
        });
    }

    /// <inheritdoc />
    public Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "CreateCollectionSchema";

        return this.RunOperationAsync(OperationName, () =>
        {
            var schema = WeaviateVectorStoreCollectionCreateMapping.MapToSchema(
                this.CollectionName,
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
                this._dataProperties,
                this._vectorProperties,
                this._storagePropertyNames);
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
                this._dataProperties,
                this._vectorProperties,
                this._storagePropertyNames);
=======
                this._propertyReader.DataProperties,
                this._propertyReader.VectorProperties,
                this._propertyReader.JsonPropertyNamesMap);
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
                this._propertyReader.DataProperties,
                this._propertyReader.VectorProperties,
                this._propertyReader.JsonPropertyNamesMap);
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
                this._propertyReader.DataProperties,
                this._propertyReader.VectorProperties,
                this._propertyReader.JsonPropertyNamesMap);
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head

            var request = new WeaviateCreateCollectionSchemaRequest(schema).Build();

            return this.ExecuteRequestAsync(request, cancellationToken);
        });
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
        const string OperationName = "DeleteCollectionSchema";

        return this.RunOperationAsync(OperationName, () =>
        {
            var request = new WeaviateDeleteCollectionSchemaRequest(this.CollectionName).Build();

            return this.ExecuteRequestAsync(request, cancellationToken);
        });
    }

    /// <inheritdoc />
    public Task DeleteAsync(Guid key, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        const string OperationName = "DeleteObject";

        return this.RunOperationAsync(OperationName, () =>
        {
            var request = new WeaviateDeleteObjectRequest(this.CollectionName, key).Build();

            return this.ExecuteRequestAsync(request, cancellationToken);
        });
    }

    /// <inheritdoc />
    public Task DeleteBatchAsync(IEnumerable<Guid> keys, DeleteRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        const string OperationName = "DeleteObjectBatch";
        const string ContainsAnyOperator = "ContainsAny";

        return this.RunOperationAsync(OperationName, () =>
        {
            var match = new WeaviateQueryMatch
            {
                CollectionName = this.CollectionName,
                WhereClause = new WeaviateQueryMatchWhereClause
                {
                    Operator = ContainsAnyOperator,
                    Path = [WeaviateConstants.ReservedKeyPropertyName],
                    Values = keys.Select(key => key.ToString()).ToList()
                }
            };

            var request = new WeaviateDeleteObjectBatchRequest(match).Build();

            return this.ExecuteRequestAsync(request, cancellationToken);
        });
    }

    /// <inheritdoc />
    public Task<TRecord?> GetAsync(Guid key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        const string OperationName = "GetCollectionObject";

        return this.RunOperationAsync(OperationName, async () =>
        {
            var includeVectors = options?.IncludeVectors is true;
            var request = new WeaviateGetCollectionObjectRequest(this.CollectionName, key, includeVectors).Build();

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
            var jsonNode = await this.ExecuteRequestWithNotFoundHandlingAsync<JsonNode>(request, cancellationToken).ConfigureAwait(false);

            if (jsonNode is null)
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
            var jsonNode = await this.ExecuteRequestWithNotFoundHandlingAsync<JsonNode>(request, cancellationToken).ConfigureAwait(false);

            if (jsonNode is null)
=======
            var jsonObject = await this.ExecuteRequestWithNotFoundHandlingAsync<JsonObject>(request, cancellationToken).ConfigureAwait(false);

            if (jsonObject is null)
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
            var jsonObject = await this.ExecuteRequestWithNotFoundHandlingAsync<JsonObject>(request, cancellationToken).ConfigureAwait(false);

            if (jsonObject is null)
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
            var jsonObject = await this.ExecuteRequestWithNotFoundHandlingAsync<JsonObject>(request, cancellationToken).ConfigureAwait(false);

            if (jsonObject is null)
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
            {
                return default;
            }

            return VectorStoreErrorHandler.RunModelConversion(
                DatabaseName,
                this.CollectionName,
                OperationName,
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
                () => this._mapper.MapFromStorageToDataModel(jsonNode!, new() { IncludeVectors = includeVectors }));
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
                () => this._mapper.MapFromStorageToDataModel(jsonNode!, new() { IncludeVectors = includeVectors }));
=======
                () => this._mapper.MapFromStorageToDataModel(jsonObject!, new() { IncludeVectors = includeVectors }));
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
                () => this._mapper.MapFromStorageToDataModel(jsonObject!, new() { IncludeVectors = includeVectors }));
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
                () => this._mapper.MapFromStorageToDataModel(jsonObject!, new() { IncludeVectors = includeVectors }));
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
        });
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetBatchAsync(
        IEnumerable<Guid> keys,
        GetRecordOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var tasks = keys.Select(key => this.GetAsync(key, options, cancellationToken));

        var records = await Task.WhenAll(tasks).ConfigureAwait(false);

        foreach (var record in records)
        {
            if (record is not null)
            {
                yield return record;
            }
        }
    }

    /// <inheritdoc />
    public async Task<Guid> UpsertAsync(TRecord record, UpsertRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        return await this.UpsertBatchAsync([record], options, cancellationToken)
            .FirstOrDefaultAsync(cancellationToken)
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<Guid> UpsertBatchAsync(
        IEnumerable<TRecord> records,
        UpsertRecordOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        const string OperationName = "UpsertCollectionObject";

        var responses = await this.RunOperationAsync(OperationName, async () =>
        {
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
            var jsonNodes = records.Select(record => VectorStoreErrorHandler.RunModelConversion(
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
            var jsonNodes = records.Select(record => VectorStoreErrorHandler.RunModelConversion(
=======
            var jsonObjects = records.Select(record => VectorStoreErrorHandler.RunModelConversion(
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
            var jsonObjects = records.Select(record => VectorStoreErrorHandler.RunModelConversion(
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
            var jsonObjects = records.Select(record => VectorStoreErrorHandler.RunModelConversion(
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
                DatabaseName,
                this.CollectionName,
                OperationName,
                () => this._mapper.MapFromDataToStorageModel(record))).ToList();

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
            var request = new WeaviateUpsertCollectionObjectBatchRequest(jsonNodes).Build();
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
            var request = new WeaviateUpsertCollectionObjectBatchRequest(jsonNodes).Build();
=======
            var request = new WeaviateUpsertCollectionObjectBatchRequest(jsonObjects).Build();
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
            var request = new WeaviateUpsertCollectionObjectBatchRequest(jsonObjects).Build();
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
            var request = new WeaviateUpsertCollectionObjectBatchRequest(jsonObjects).Build();
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head

            return await this.ExecuteRequestAsync<List<WeaviateUpsertCollectionObjectBatchResponse>>(request, cancellationToken).ConfigureAwait(false);
        }).ConfigureAwait(false);

        if (responses is not null)
        {
            foreach (var response in responses)
            {
                if (response?.Result?.IsSuccess is true)
                {
                    yield return response.Id;
                }
            }
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
    public async IAsyncEnumerable<VectorSearchResult<TRecord>> VectorizedSearchAsync<TVector>(
        TVector vector,
        VectorSearchOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
=======
    /// <inheritdoc />
    public async Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(
        TVector vector,
        VectorSearchOptions? options = null,
        CancellationToken cancellationToken = default)
>>>>>>> upstream/main
    {
        const string OperationName = "VectorSearch";

        Verify.NotNull(vector);

        var vectorType = vector.GetType();

        if (!s_supportedVectorTypes.Contains(vectorType))
        {
            throw new NotSupportedException(
                $"The provided vector type {vectorType.FullName} is not supported by the Azure CosmosDB NoSQL connector. " +
                $"Supported types are: {string.Join(", ", s_supportedVectorTypes.Select(l => l.FullName))}");
        }

        var searchOptions = options ?? s_defaultVectorSearchOptions;
        var vectorProperty = this.GetVectorPropertyForSearch(searchOptions.VectorPropertyName);

        if (vectorProperty is null)
        {
            throw new InvalidOperationException("The collection does not have any vector properties, so vector search is not possible.");
        }

        var vectorPropertyName = this._propertyReader.GetJsonPropertyName(vectorProperty.DataModelPropertyName);
        var fields = this._propertyReader.DataPropertyJsonNames;

        var query = WeaviateVectorStoreRecordCollectionQueryBuilder.BuildSearchQuery(
            vector,
            this.CollectionName,
            vectorPropertyName,
            this._propertyReader.KeyPropertyName,
            s_jsonSerializerOptions,
            searchOptions,
            this._propertyReader.JsonPropertyNamesMap,
            this._propertyReader.VectorPropertyJsonNames,
            this._propertyReader.DataPropertyJsonNames);

        using var request = new WeaviateVectorSearchRequest(query).Build();

        var (responseModel, content) = await this.ExecuteRequestWithResponseContentAsync<WeaviateVectorSearchResponse>(request, cancellationToken).ConfigureAwait(false);

        var collectionResults = responseModel?.Data?.GetOperation?[this.CollectionName];

        if (collectionResults is null)
        {
            throw new VectorStoreOperationException($"Error occurred during vector search. Response: {content}")
            {
                VectorStoreType = DatabaseName,
                CollectionName = this.CollectionName,
                OperationName = OperationName
            };
        }

<<<<<<< main
        foreach (var result in collectionResults)
        {
            if (result is not null)
            {
                var (storageModel, score) = WeaviateVectorStoreCollectionSearchMapping.MapSearchResult(result);

                var record = VectorStoreErrorHandler.RunModelConversion(
                    DatabaseName,
                    this.CollectionName,
                    OperationName,
                    () => this._mapper.MapFromStorageToDataModel(storageModel, new() { IncludeVectors = searchOptions.IncludeVectors }));

                yield return new VectorSearchResult<TRecord>(record, score);
            }
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
        var mappedResults = collectionResults.Where(x => x is not null).Select(result =>
        {
            var (storageModel, score) = WeaviateVectorStoreCollectionSearchMapping.MapSearchResult(result!);

            var record = VectorStoreErrorHandler.RunModelConversion(
                DatabaseName,
                this.CollectionName,
                OperationName,
                () => this._mapper.MapFromStorageToDataModel(storageModel, new() { IncludeVectors = searchOptions.IncludeVectors }));

            return new VectorSearchResult<TRecord>(record, score);
        });

        return new VectorSearchResults<TRecord>(mappedResults.ToAsyncEnumerable());
    }

>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
    #region private

    private Task<HttpResponseMessage> ExecuteRequestAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        request.RequestUri = new Uri(this._endpoint, request.RequestUri!);

        if (!string.IsNullOrWhiteSpace(this._apiKey))
        {
            request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", this._apiKey);
        }

        return this._httpClient.SendWithSuccessCheckAsync(request, cancellationToken);
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
    private async Task<TResponse?> ExecuteRequestAsync<TResponse>(HttpRequestMessage request, CancellationToken cancellationToken)
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
    private async Task<TResponse?> ExecuteRequestAsync<TResponse>(HttpRequestMessage request, CancellationToken cancellationToken)
=======
    private async Task<(TResponse?, string)> ExecuteRequestWithResponseContentAsync<TResponse>(HttpRequestMessage request, CancellationToken cancellationToken)
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
    private async Task<(TResponse?, string)> ExecuteRequestWithResponseContentAsync<TResponse>(HttpRequestMessage request, CancellationToken cancellationToken)
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
    private async Task<(TResponse?, string)> ExecuteRequestWithResponseContentAsync<TResponse>(HttpRequestMessage request, CancellationToken cancellationToken)
>>>>>>> upstream/main
=======
<<<<<<< div
=======
    private async Task<(TResponse?, string)> ExecuteRequestWithResponseContentAsync<TResponse>(HttpRequestMessage request, CancellationToken cancellationToken)
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
>>>>>>> div
    {
        var response = await this.ExecuteRequestAsync(request, cancellationToken).ConfigureAwait(false);

        var responseContent = await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);

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
        return JsonSerializer.Deserialize<TResponse>(responseContent, s_jsonSerializerOptions);
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
        return JsonSerializer.Deserialize<TResponse>(responseContent, s_jsonSerializerOptions);
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        return JsonSerializer.Deserialize<TResponse>(responseContent, s_jsonSerializerOptions);
=======
>>>>>>> Stashed changes
=======
        return JsonSerializer.Deserialize<TResponse>(responseContent, s_jsonSerializerOptions);
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
        var responseModel = JsonSerializer.Deserialize<TResponse>(responseContent, s_jsonSerializerOptions);

        return (responseModel, responseContent);
    }

    private async Task<TResponse?> ExecuteRequestAsync<TResponse>(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        var (model, _) = await this.ExecuteRequestWithResponseContentAsync<TResponse>(request, cancellationToken).ConfigureAwait(false);

        return model;
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
    }

    private async Task<TResponse?> ExecuteRequestWithNotFoundHandlingAsync<TResponse>(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        try
        {
            return await this.ExecuteRequestAsync<TResponse>(request, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException ex) when (ex.StatusCode == HttpStatusCode.NotFound)
        {
            return default;
        }
    }

    private async Task<T> RunOperationAsync<T>(string operationName, Func<Task<T>> operation)
    {
        try
        {
            return await operation.Invoke().ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreType = DatabaseName,
                CollectionName = this.CollectionName,
                OperationName = operationName
            };
        }
    }

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
    /// <summary>
    /// Get vector property to use for a search by using the storage name for the field name from options
    /// if available, and falling back to the first vector property in <typeparamref name="TRecord"/> if not.
    /// </summary>
    /// <param name="vectorFieldName">The vector field name.</param>
    /// <exception cref="InvalidOperationException">Thrown if the provided field name is not a valid field name.</exception>
    private VectorStoreRecordVectorProperty? GetVectorPropertyForSearch(string? vectorFieldName)
    {
        // If vector property name is provided in options, try to find it in schema or throw an exception.
        if (!string.IsNullOrWhiteSpace(vectorFieldName))
        {
            // Check vector properties by data model property name.
            var vectorProperty = this._propertyReader.VectorProperties
                .FirstOrDefault(l => l.DataModelPropertyName.Equals(vectorFieldName, StringComparison.Ordinal));

            if (vectorProperty is not null)
            {
                return vectorProperty;
            }

            throw new InvalidOperationException($"The {typeof(TRecord).FullName} type does not have a vector property named '{vectorFieldName}'.");
        }

        // If vector property is not provided in options, return first vector property from schema.
        return this._firstVectorProperty;
        return this._propertyReader.VectorProperty;
    }

    /// <summary>
    /// Get vector property to use for a search by using the storage name for the field name from options
    /// if available, and falling back to the first vector property in <typeparamref name="TRecord"/> if not.
    /// </summary>
    /// <param name="vectorFieldName">The vector field name.</param>
    /// <exception cref="InvalidOperationException">Thrown if the provided field name is not a valid field name.</exception>
    private VectorStoreRecordVectorProperty? GetVectorPropertyForSearch(string? vectorFieldName)
    {
        // If vector property name is provided in options, try to find it in schema or throw an exception.
        if (!string.IsNullOrWhiteSpace(vectorFieldName))
        {
            // Check vector properties by data model property name.
            var vectorProperty = this._propertyReader.VectorProperties
                .FirstOrDefault(l => l.DataModelPropertyName.Equals(vectorFieldName, StringComparison.Ordinal));

            if (vectorProperty is not null)
            {
                return vectorProperty;
            }

            throw new InvalidOperationException($"The {typeof(TRecord).FullName} type does not have a vector property named '{vectorFieldName}'.");
        }

        // If vector property is not provided in options, return first vector property from schema.
        return this._propertyReader.VectorProperty;
    }

    /// <summary>
    /// Returns custom mapper, generic data model mapper or default record mapper.
    /// </summary>
    private IVectorStoreRecordMapper<TRecord, JsonObject> InitializeMapper()
    {
        if (this._options.JsonObjectCustomMapper is not null)
        {
            return this._options.JsonObjectCustomMapper;
        }

        if (typeof(TRecord) == typeof(VectorStoreGenericDataModel<Guid>))
        {
            var mapper = new WeaviateGenericDataModelMapper(
                this.CollectionName,
                this._propertyReader.KeyProperty,
                this._propertyReader.DataProperties,
                this._propertyReader.VectorProperties,
                this._propertyReader.JsonPropertyNamesMap,
                s_jsonSerializerOptions);

            return (mapper as IVectorStoreRecordMapper<TRecord, JsonObject>)!;
        }

        return new WeaviateVectorStoreRecordMapper<TRecord>(
            this.CollectionName,
            this._propertyReader.KeyProperty,
            this._propertyReader.DataProperties,
            this._propertyReader.VectorProperties,
            this._propertyReader.JsonPropertyNamesMap,
            s_jsonSerializerOptions);
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
>>>>>>> head
    #endregion
}
