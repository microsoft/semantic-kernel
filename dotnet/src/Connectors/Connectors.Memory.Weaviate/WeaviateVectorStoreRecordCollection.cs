﻿// Copyright (c) Microsoft. All rights reserved.

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
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

/// <summary>
/// Service for storing and retrieving vector records, that uses Weaviate as the underlying storage.
/// </summary>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public sealed class WeaviateVectorStoreRecordCollection<TRecord> : IVectorStoreRecordCollection<Guid, TRecord> where TRecord : class
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
        typeof(bool),
        typeof(bool?),
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
        typeof(Guid?)
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

    /// <summary><see cref="HttpClient"/> that is used to interact with Weaviate API.</summary>
    private readonly HttpClient _httpClient;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly WeaviateVectorStoreRecordCollectionOptions<TRecord> _options;

    /// <summary>A helper to access property information for the current data model and record definition.</summary>
    private readonly VectorStoreRecordPropertyReader _propertyReader;

    /// <summary>The mapper to use when mapping between the consumer data model and the Weaviate record.</summary>
    private readonly IVectorStoreRecordMapper<TRecord, JsonObject> _mapper;

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

        // Assign mapper.
        this._mapper = this.InitializeMapper();
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
                this._propertyReader.DataProperties,
                this._propertyReader.VectorProperties,
                this._propertyReader.JsonPropertyNamesMap);

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

            var jsonObject = await this.ExecuteRequestWithNotFoundHandlingAsync<JsonObject>(request, cancellationToken).ConfigureAwait(false);

            if (jsonObject is null)
            {
                return null;
            }

            return VectorStoreErrorHandler.RunModelConversion(
                DatabaseName,
                this.CollectionName,
                OperationName,
                () => this._mapper.MapFromStorageToDataModel(jsonObject!, new() { IncludeVectors = includeVectors }));
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
            var jsonObjects = records.Select(record => VectorStoreErrorHandler.RunModelConversion(
                DatabaseName,
                this.CollectionName,
                OperationName,
                () => this._mapper.MapFromDataToStorageModel(record))).ToList();

            var request = new WeaviateUpsertCollectionObjectBatchRequest(jsonObjects).Build();

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

    private async Task<TResponse?> ExecuteRequestAsync<TResponse>(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        var response = await this.ExecuteRequestAsync(request, cancellationToken).ConfigureAwait(false);

        var responseContent = await response.Content.ReadAsStringWithExceptionMappingAsync().ConfigureAwait(false);

        return JsonSerializer.Deserialize<TResponse>(responseContent, s_jsonSerializerOptions);
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

    #endregion
}
