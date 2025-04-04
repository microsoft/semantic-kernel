// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

/// <summary>
/// Service for storing and retrieving vector records, that uses Weaviate as the underlying storage.
/// </summary>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public class WeaviateVectorStoreRecordCollection<TRecord> : IVectorStoreRecordCollection<Guid, TRecord>, IKeywordHybridSearch<TRecord>
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    /// <summary>Default JSON serializer options.</summary>
    private static readonly JsonSerializerOptions s_jsonSerializerOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        Converters =
        {
            new WeaviateDateTimeOffsetConverter(),
            new WeaviateNullableDateTimeOffsetConverter()
        }
    };

    /// <summary>The default options for vector search.</summary>
    private static readonly VectorSearchOptions<TRecord> s_defaultVectorSearchOptions = new();

    /// <summary>The default options for hybrid vector search.</summary>
    private static readonly HybridSearchOptions<TRecord> s_defaultKeywordVectorizedHybridSearchOptions = new();

    /// <summary><see cref="HttpClient"/> that is used to interact with Weaviate API.</summary>
    private readonly HttpClient _httpClient;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly WeaviateVectorStoreRecordCollectionOptions<TRecord> _options;

    /// <summary>The model for this collection.</summary>
    private readonly VectorStoreRecordModel _model;

    /// <summary>The mapper to use when mapping between the consumer data model and the Weaviate record.</summary>
#pragma warning disable CS0618 // IVectorStoreRecordMapper is obsolete
    private readonly IVectorStoreRecordMapper<TRecord, JsonObject> _mapper;
#pragma warning restore CS0618

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
    /// <remarks>The collection name must start with a capital letter and contain only ASCII letters and digits.</remarks>
    public WeaviateVectorStoreRecordCollection(
        HttpClient httpClient,
        string collectionName,
        WeaviateVectorStoreRecordCollectionOptions<TRecord>? options = default)
    {
        // Verify.
        Verify.NotNull(httpClient);
        VerifyCollectionName(collectionName);

        var endpoint = (options?.Endpoint ?? httpClient.BaseAddress) ?? throw new ArgumentException($"Weaviate endpoint should be provided via HttpClient.BaseAddress property or {nameof(WeaviateVectorStoreRecordCollectionOptions<TRecord>)} options parameter.");

        // Assign.
        this._httpClient = httpClient;
        this._endpoint = endpoint;
        this.CollectionName = collectionName;
        this._options = options ?? new();
        this._apiKey = this._options.ApiKey;
        this._model = new WeaviateModelBuilder().Build(typeof(TRecord), this._options.VectorStoreRecordDefinition, s_jsonSerializerOptions);

        // Assign mapper.
        this._mapper = this.InitializeMapper();
    }

    /// <inheritdoc />
    public virtual Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
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
    public virtual Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "CreateCollectionSchema";

        return this.RunOperationAsync(OperationName, () =>
        {
            var schema = WeaviateVectorStoreCollectionCreateMapping.MapToSchema(this.CollectionName, this._model);

            var request = new WeaviateCreateCollectionSchemaRequest(schema).Build();

            return this.ExecuteRequestAsync(request, cancellationToken);
        });
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
    public virtual Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "DeleteCollectionSchema";

        return this.RunOperationAsync(OperationName, () =>
        {
            var request = new WeaviateDeleteCollectionSchemaRequest(this.CollectionName).Build();

            return this.ExecuteRequestAsync(request, cancellationToken);
        });
    }

    /// <inheritdoc />
    public virtual Task DeleteAsync(Guid key, CancellationToken cancellationToken = default)
    {
        const string OperationName = "DeleteObject";

        return this.RunOperationAsync(OperationName, () =>
        {
            var request = new WeaviateDeleteObjectRequest(this.CollectionName, key).Build();

            return this.ExecuteRequestAsync(request, cancellationToken);
        });
    }

    /// <inheritdoc />
    public virtual Task DeleteAsync(IEnumerable<Guid> keys, CancellationToken cancellationToken = default)
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
    public virtual Task<TRecord?> GetAsync(Guid key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        const string OperationName = "GetCollectionObject";

        return this.RunOperationAsync(OperationName, async () =>
        {
            var includeVectors = options?.IncludeVectors is true;
            var request = new WeaviateGetCollectionObjectRequest(this.CollectionName, key, includeVectors).Build();

            var jsonObject = await this.ExecuteRequestWithNotFoundHandlingAsync<JsonObject>(request, cancellationToken).ConfigureAwait(false);

            if (jsonObject is null)
            {
                return default;
            }

            return VectorStoreErrorHandler.RunModelConversion(
                WeaviateConstants.DatabaseName,
                this.CollectionName,
                OperationName,
                () => this._mapper.MapFromStorageToDataModel(jsonObject!, new() { IncludeVectors = includeVectors }));
        });
    }

    /// <inheritdoc />
    public virtual async IAsyncEnumerable<TRecord> GetAsync(
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
    public virtual async Task<Guid> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        return await this.UpsertAsync([record], cancellationToken)
            .FirstOrDefaultAsync(cancellationToken)
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
    public virtual async IAsyncEnumerable<Guid> UpsertAsync(IEnumerable<TRecord> records, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        const string OperationName = "UpsertCollectionObject";

        var responses = await this.RunOperationAsync(OperationName, async () =>
        {
            var jsonObjects = records.Select(record => VectorStoreErrorHandler.RunModelConversion(
                WeaviateConstants.DatabaseName,
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

    /// <inheritdoc />
    public virtual async Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(
        TVector vector,
        int top,
        VectorSearchOptions<TRecord>? options = null,
        CancellationToken cancellationToken = default)
    {
        const string OperationName = "VectorSearch";

        VerifyVectorParam(vector);
        Verify.NotLessThan(top, 1);

        var searchOptions = options ?? s_defaultVectorSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle(searchOptions);

        var query = WeaviateVectorStoreRecordCollectionQueryBuilder.BuildSearchQuery(
            vector,
            this.CollectionName,
            vectorProperty.StorageName,
            s_jsonSerializerOptions,
            top,
            searchOptions,
            this._model);

        return await this.ExecuteQueryAsync(query, searchOptions.IncludeVectors, WeaviateConstants.ScorePropertyName, OperationName, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetAsync(Expression<Func<TRecord, bool>> filter, int top,
        FilterOptions<TRecord>? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(filter);
        Verify.NotLessThan(top, 1);

        options ??= new();

        var query = WeaviateVectorStoreRecordCollectionQueryBuilder.BuildQuery(
            filter,
            top,
            options,
            options.Sort.Values.Select(pair => new KeyValuePair<VectorStoreRecordPropertyModel, bool>(this._model.GetDataOrKeyProperty<TRecord>(pair.Key), pair.Value)),
            this.CollectionName,
            this._model);

        var results = await this.ExecuteQueryAsync(query, options.IncludeVectors, WeaviateConstants.ScorePropertyName, "GetAsync", cancellationToken).ConfigureAwait(false);
        await foreach (var record in results.Results.ConfigureAwait(false))
        {
            yield return record.Record;
        }
    }

    /// <inheritdoc />
    public async Task<VectorSearchResults<TRecord>> HybridSearchAsync<TVector>(TVector vector, ICollection<string> keywords, int top, HybridSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        const string OperationName = "HybridSearch";

        VerifyVectorParam(vector);
        Verify.NotLessThan(top, 1);

        var searchOptions = options ?? s_defaultKeywordVectorizedHybridSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle<TRecord>(new() { VectorProperty = searchOptions.VectorProperty });
        var textDataProperty = this._model.GetFullTextDataPropertyOrSingle(searchOptions.AdditionalProperty);

        var query = WeaviateVectorStoreRecordCollectionQueryBuilder.BuildHybridSearchQuery(
            vector,
            top,
            string.Join(" ", keywords),
            this.CollectionName,
            this._model,
            vectorProperty,
            textDataProperty,
            s_jsonSerializerOptions,
            searchOptions);

        return await this.ExecuteQueryAsync(query, searchOptions.IncludeVectors, WeaviateConstants.HybridScorePropertyName, OperationName, cancellationToken).ConfigureAwait(false);
    }

    #region private

    private async Task<VectorSearchResults<TRecord>> ExecuteQueryAsync(string query, bool includeVectors, string scorePropertyName, string operationName, CancellationToken cancellationToken)
    {
        using var request = new WeaviateVectorSearchRequest(query).Build();

        var (responseModel, content) = await this.ExecuteRequestWithResponseContentAsync<WeaviateVectorSearchResponse>(request, cancellationToken).ConfigureAwait(false);

        var collectionResults = responseModel?.Data?.GetOperation?[this.CollectionName];

        if (collectionResults is null)
        {
            throw new VectorStoreOperationException($"Error occurred during vector search. Response: {content}")
            {
                VectorStoreType = WeaviateConstants.DatabaseName,
                CollectionName = this.CollectionName,
                OperationName = operationName
            };
        }

        var mappedResults = collectionResults.Where(x => x is not null).Select(result =>
        {
            var (storageModel, score) = WeaviateVectorStoreCollectionSearchMapping.MapSearchResult(result!, scorePropertyName);

            var record = VectorStoreErrorHandler.RunModelConversion(
                WeaviateConstants.DatabaseName,
                this.CollectionName,
                operationName,
                () => this._mapper.MapFromStorageToDataModel(storageModel, new() { IncludeVectors = includeVectors }));

            return new VectorSearchResult<TRecord>(record, score);
        });

        return new VectorSearchResults<TRecord>(mappedResults.ToAsyncEnumerable());
    }

    private Task<HttpResponseMessage> ExecuteRequestAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        request.RequestUri = new Uri(this._endpoint, request.RequestUri!);

        if (!string.IsNullOrWhiteSpace(this._apiKey))
        {
            request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", this._apiKey);
        }

        return this._httpClient.SendAsync(request, HttpCompletionOption.ResponseContentRead, cancellationToken);
    }

    private async Task<(TResponse?, string)> ExecuteRequestWithResponseContentAsync<TResponse>(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        var response = await this.ExecuteRequestAsync(request, cancellationToken).ConfigureAwait(false);

        var responseContent = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);

        var responseModel = JsonSerializer.Deserialize<TResponse>(responseContent, s_jsonSerializerOptions);

        return (responseModel, responseContent);
    }

    private async Task<TResponse?> ExecuteRequestAsync<TResponse>(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        var (model, _) = await this.ExecuteRequestWithResponseContentAsync<TResponse>(request, cancellationToken).ConfigureAwait(false);

        return model;
    }

    private async Task<TResponse?> ExecuteRequestWithNotFoundHandlingAsync<TResponse>(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        var response = await this.ExecuteRequestAsync(request, cancellationToken).ConfigureAwait(false);
        if (response.StatusCode == HttpStatusCode.NotFound)
        {
            return default;
        }

        var responseContent = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
        var responseModel = JsonSerializer.Deserialize<TResponse>(responseContent, s_jsonSerializerOptions);

        return responseModel;
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
                VectorStoreType = WeaviateConstants.DatabaseName,
                CollectionName = this.CollectionName,
                OperationName = operationName
            };
        }
    }

    /// <summary>
    /// Returns custom mapper, generic data model mapper or default record mapper.
    /// </summary>
#pragma warning disable CS0618 // IVectorStoreRecordMapper is obsolete
    private IVectorStoreRecordMapper<TRecord, JsonObject> InitializeMapper()
    {
        if (this._options.JsonObjectCustomMapper is not null)
        {
            return this._options.JsonObjectCustomMapper;
        }

        if (typeof(TRecord) == typeof(VectorStoreGenericDataModel<Guid>))
        {
            var mapper = new WeaviateGenericDataModelMapper(this.CollectionName, this._model, s_jsonSerializerOptions);

            return (mapper as IVectorStoreRecordMapper<TRecord, JsonObject>)!;
        }

        return new WeaviateVectorStoreRecordMapper<TRecord>(this.CollectionName, this._model, s_jsonSerializerOptions);
    }
#pragma warning restore CS0618

    private static void VerifyVectorParam<TVector>(TVector vector)
    {
        Verify.NotNull(vector);

        var vectorType = vector.GetType();

        if (!WeaviateModelBuilder.s_supportedVectorTypes.Contains(vectorType))
        {
            throw new NotSupportedException(
                $"The provided vector type {vectorType.FullName} is not supported by the Weaviate connector. " +
                $"Supported types are: {string.Join(", ", WeaviateModelBuilder.s_supportedVectorTypes.Select(l => l.FullName))}");
        }
    }

    private static void VerifyCollectionName(string collectionName)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        // Based on https://weaviate.io/developers/weaviate/starter-guides/managing-collections#collection--property-names
        char first = collectionName[0];
        if (!(first is >= 'A' and <= 'Z'))
        {
            throw new ArgumentException("Collection name must start with an uppercase ASCII letter.", nameof(collectionName));
        }

        foreach (char character in collectionName)
        {
            if (!((character is >= 'a' and <= 'z') || (character is >= 'A' and <= 'Z') || (character is >= '0' and <= '9')))
            {
                throw new ArgumentException("Collection name must contain only ASCII letters and digits.", nameof(collectionName));
            }
        }
    }
    #endregion
}
