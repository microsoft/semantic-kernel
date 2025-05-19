// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
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
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

/// <summary>
/// Service for storing and retrieving vector records, that uses Weaviate as the underlying storage.
/// </summary>
/// <typeparam name="TKey">The data type of the record key. Must be <see cref="Guid"/>.</typeparam>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public class WeaviateCollection<TKey, TRecord> : VectorStoreCollection<TKey, TRecord>, IKeywordHybridSearchable<TRecord>
    where TKey : notnull
    where TRecord : class
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    /// <summary>Metadata about vector store record collection.</summary>
    private readonly VectorStoreCollectionMetadata _collectionMetadata;

    /// <summary>The default options for vector search.</summary>
    private static readonly VectorSearchOptions<TRecord> s_defaultVectorSearchOptions = new();

    /// <summary>The default options for hybrid vector search.</summary>
    private static readonly HybridSearchOptions<TRecord> s_defaultKeywordVectorizedHybridSearchOptions = new();

    /// <summary><see cref="HttpClient"/> that is used to interact with Weaviate API.</summary>
    private readonly HttpClient _httpClient;

    /// <summary>The model for this collection.</summary>
    private readonly CollectionModel _model;

    /// <summary>The mapper to use when mapping between the consumer data model and the Weaviate record.</summary>
    private readonly WeaviateMapper<TRecord> _mapper;

    /// <summary>Weaviate endpoint.</summary>
    private readonly Uri _endpoint;

    /// <summary>Weaviate API key.</summary>
    private readonly string? _apiKey;

    /// <inheritdoc />
    public override string Name { get; }

    /// <summary>Whether the vectors in the store are named and multiple vectors are supported, or whether there is just a single unnamed vector in Weaviate collection.</summary>
    private readonly bool _hasNamedVectors;

    /// <summary>
    /// Initializes a new instance of the <see cref="WeaviateCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="httpClient">
    /// <see cref="HttpClient"/> that is used to interact with Weaviate API.
    /// <see cref="HttpClient.BaseAddress"/> should point to remote or local cluster and API key can be configured via <see cref="HttpClient.DefaultRequestHeaders"/>.
    /// It's also possible to provide these parameters via <see cref="WeaviateCollectionOptions"/>.
    /// </param>
    /// <param name="name">The name of the collection that this <see cref="WeaviateCollection{TKey, TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    /// <remarks>The collection name must start with a capital letter and contain only ASCII letters and digits.</remarks>
    [RequiresUnreferencedCode("The Weaviate provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The Weaviate provider is currently incompatible with NativeAOT.")]
    public WeaviateCollection(
        HttpClient httpClient,
        string name,
        WeaviateCollectionOptions? options = default)
        : this(
            httpClient,
            name,
            static options => typeof(TRecord) == typeof(Dictionary<string, object?>)
                ? throw new NotSupportedException(VectorDataStrings.NonDynamicCollectionWithDictionaryNotSupported(typeof(WeaviateDynamicCollection)))
                : new WeaviateModelBuilder(options.HasNamedVectors)
                    .Build(typeof(TRecord), options.Definition, options.EmbeddingGenerator, WeaviateConstants.s_jsonSerializerOptions),
            options)
    {
    }

    internal WeaviateCollection(HttpClient httpClient, string name, Func<WeaviateCollectionOptions, CollectionModel> modelFactory, WeaviateCollectionOptions? options)
    {
        // Verify.
        Verify.NotNull(httpClient);
        VerifyCollectionName(name);

        if (typeof(TKey) != typeof(Guid) && typeof(TKey) != typeof(object))
        {
            throw new NotSupportedException($"Only {nameof(Guid)} key is supported.");
        }

        var endpoint = (options?.Endpoint ?? httpClient.BaseAddress) ?? throw new ArgumentException($"Weaviate endpoint should be provided via HttpClient.BaseAddress property or {nameof(WeaviateCollectionOptions)} options parameter.");

        options ??= WeaviateCollectionOptions.Default;

        // Assign.
        this._httpClient = httpClient;
        this._endpoint = endpoint;
        this.Name = name;
        this._model = modelFactory(options);
        this._apiKey = options.ApiKey;
        this._hasNamedVectors = options.HasNamedVectors;

        // Assign mapper.
        this._mapper = new WeaviateMapper<TRecord>(this.Name, options.HasNamedVectors, this._model, WeaviateConstants.s_jsonSerializerOptions);

        this._collectionMetadata = new()
        {
            VectorStoreSystemName = WeaviateConstants.VectorStoreSystemName,
            CollectionName = name
        };
    }

    /// <inheritdoc />
    public override async Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        using var request = new WeaviateGetCollectionSchemaRequest(this.Name).Build();

        var response = await this
            .ExecuteRequestWithNotFoundHandlingAsync<WeaviateGetCollectionSchemaResponse>(request, cancellationToken)
            .ConfigureAwait(false);

        return response != null;
    }

    /// <inheritdoc />
    public override async Task EnsureCollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        // Don't even try to create if the collection already exists.
        if (await this.CollectionExistsAsync(cancellationToken).ConfigureAwait(false))
        {
            return;
        }

        var schema = WeaviateCollectionCreateMapping.MapToSchema(
            this.Name,
            this._hasNamedVectors,
            this._model);

        using var request = new WeaviateCreateCollectionSchemaRequest(schema).Build();

        try
        {
            await this.ExecuteRequestAsync(request, cancellationToken: cancellationToken).ConfigureAwait(false);
        }
        catch (VectorStoreException)
        {
            // Since weaviate error info is ambiguous, we can check here if the index already exists.
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

            throw;
        }
    }

    /// <inheritdoc />
    public override async Task EnsureCollectionDeletedAsync(CancellationToken cancellationToken = default)
    {
        using var request = new WeaviateDeleteCollectionSchemaRequest(this.Name).Build();

        await this.ExecuteRequestAsync(request, cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public override async Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        var guid = key switch
        {
            Guid g => g,
            object o => (Guid)o,
            _ => throw new UnreachableException("Guid key should have been validated during model building")
        };

        using var request = new WeaviateDeleteObjectRequest(this.Name, guid).Build();

        await this.ExecuteRequestAsync(request, cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public override async Task DeleteAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
    {
        const string ContainsAnyOperator = "ContainsAny";

        Verify.NotNull(keys);

        var stringKeys = keys.Select(key => key.ToString()).ToList();

        if (stringKeys.Count == 0)
        {
            return;
        }

        var match = new WeaviateQueryMatch
        {
            CollectionName = this.Name,
            WhereClause = new WeaviateQueryMatchWhereClause
            {
                Operator = ContainsAnyOperator,
                Path = [WeaviateConstants.ReservedKeyPropertyName],
                Values = stringKeys!
            }
        };

        using var request = new WeaviateDeleteObjectBatchRequest(match).Build();
        await this.ExecuteRequestAsync(request, cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public override async Task<TRecord?> GetAsync(TKey key, RecordRetrievalOptions? options = null, CancellationToken cancellationToken = default)
    {
        var guid = key as Guid? ?? throw new InvalidCastException("Only Guid keys are supported");
        var includeVectors = options?.IncludeVectors is true;
        if (includeVectors && this._model.EmbeddingGenerationRequired)
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        using var request = new WeaviateGetCollectionObjectRequest(this.Name, guid, includeVectors).Build();

        var jsonObject = await this.ExecuteRequestWithNotFoundHandlingAsync<JsonObject>(request, cancellationToken).ConfigureAwait(false);

        if (jsonObject is null)
        {
            return default;
        }

        return this._mapper.MapFromStorageToDataModel(jsonObject!, includeVectors);
    }

    /// <inheritdoc />
    public override Task UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
        => this.UpsertAsync([record], cancellationToken);

    /// <inheritdoc />
    public override async Task UpsertAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        IReadOnlyList<TRecord>? recordsList = null;

        // If an embedding generator is defined, invoke it once per property for all records.
        IReadOnlyList<Embedding>?[]? generatedEmbeddings = null;

        var vectorPropertyCount = this._model.VectorProperties.Count;
        for (var i = 0; i < vectorPropertyCount; i++)
        {
            var vectorProperty = this._model.VectorProperties[i];

            if (WeaviateModelBuilder.IsVectorPropertyTypeValidCore(vectorProperty.Type, out _))
            {
                continue;
            }

            // We have a vector property whose type isn't natively supported - we need to generate embeddings.
            Debug.Assert(vectorProperty.EmbeddingGenerator is not null);

            // We have a property with embedding generation; materialize the records' enumerable if needed, to
            // prevent multiple enumeration.
            if (recordsList is null)
            {
                recordsList = records is IReadOnlyList<TRecord> r ? r : records.ToList();

                if (recordsList.Count == 0)
                {
                    return;
                }

                records = recordsList;
            }

            // TODO: Ideally we'd group together vector properties using the same generator (and with the same input and output properties),
            // and generate embeddings for them in a single batch. That's some more complexity though.
            if (vectorProperty.TryGenerateEmbeddings<TRecord, Embedding<float>>(records, cancellationToken, out var floatTask))
            {
                generatedEmbeddings ??= new IReadOnlyList<Embedding>?[vectorPropertyCount];
                generatedEmbeddings[i] = (IReadOnlyList<Embedding<float>>)await floatTask.ConfigureAwait(false);
            }
            else
            {
                throw new InvalidOperationException(
                    $"The embedding generator configured on property '{vectorProperty.ModelName}' cannot produce an embedding of type '{typeof(Embedding<float>).Name}' for the given input type.");
            }
        }

        var jsonObjects = records.Select((record, i) => this._mapper.MapFromDataToStorageModel(record, i, generatedEmbeddings)).ToList();

        if (jsonObjects.Count == 0)
        {
            return;
        }

        using var request = new WeaviateUpsertCollectionObjectBatchRequest(jsonObjects).Build();

        await this.ExecuteRequestAsync<List<WeaviateUpsertCollectionObjectBatchResponse>>(request, cancellationToken).ConfigureAwait(false);
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
        var vector = await GetSearchVectorAsync(searchValue, vectorProperty, cancellationToken).ConfigureAwait(false);

        var query = WeaviateQueryBuilder.BuildSearchQuery(
            vector,
            this.Name,
            vectorProperty.StorageName,
            WeaviateConstants.s_jsonSerializerOptions,
            top,
            options,
            this._model,
            this._hasNamedVectors);

        await foreach (var record in this.ExecuteQueryAsync(query, options.IncludeVectors, WeaviateConstants.ScorePropertyName, operationName: "VectorSearch", cancellationToken).ConfigureAwait(false))
        {
            yield return record;
        }
    }

    private static async ValueTask<ReadOnlyMemory<float>> GetSearchVectorAsync<TInput>(TInput searchValue, VectorPropertyModel vectorProperty, CancellationToken cancellationToken)
        where TInput : notnull
        => searchValue switch
        {
            ReadOnlyMemory<float> r => r,
            float[] f => new ReadOnlyMemory<float>(f),
            Embedding<float> e => e.Vector,
            _ when vectorProperty.EmbeddingGenerator is IEmbeddingGenerator<TInput, Embedding<float>> generator
                => await generator.GenerateVectorAsync(searchValue, cancellationToken: cancellationToken).ConfigureAwait(false),

            _ => vectorProperty.EmbeddingGenerator is null
                ? throw new NotSupportedException(VectorDataStrings.InvalidSearchInputAndNoEmbeddingGeneratorWasConfigured(searchValue.GetType(), WeaviateModelBuilder.SupportedVectorTypes))
                : throw new InvalidOperationException(VectorDataStrings.IncompatibleEmbeddingGeneratorWasConfiguredForInputType(typeof(TInput), vectorProperty.EmbeddingGenerator.GetType()))
        };

    #endregion Search

    /// <inheritdoc />
    public override IAsyncEnumerable<TRecord> GetAsync(Expression<Func<TRecord, bool>> filter, int top,
        FilteredRecordRetrievalOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(filter);
        Verify.NotLessThan(top, 1);

        options ??= new();

        var query = WeaviateQueryBuilder.BuildQuery(
            filter,
            top,
            options,
            this.Name,
            this._model,
            this._hasNamedVectors);

        return this.ExecuteQueryAsync(query, options.IncludeVectors, WeaviateConstants.ScorePropertyName, "GetAsync", cancellationToken)
            .SelectAsync(result => result.Record, cancellationToken: cancellationToken);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<VectorSearchResult<TRecord>> HybridSearchAsync<TInput>(
        TInput searchValue,
        ICollection<string> keywords,
        int top,
        HybridSearchOptions<TRecord>? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
        where TInput : notnull
    {
        const string OperationName = "HybridSearch";

        Verify.NotLessThan(top, 1);

        options ??= s_defaultKeywordVectorizedHybridSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle<TRecord>(new() { VectorProperty = options.VectorProperty });
        var vector = await GetSearchVectorAsync(searchValue, vectorProperty, cancellationToken).ConfigureAwait(false);
        var textDataProperty = this._model.GetFullTextDataPropertyOrSingle(options.AdditionalProperty);

        var query = WeaviateQueryBuilder.BuildHybridSearchQuery(
            vector,
            top,
            string.Join(" ", keywords),
            this.Name,
            this._model,
            vectorProperty,
            textDataProperty,
            WeaviateConstants.s_jsonSerializerOptions,
            options,
            this._hasNamedVectors);

        await foreach (var record in this.ExecuteQueryAsync(query, options.IncludeVectors, WeaviateConstants.HybridScorePropertyName, OperationName, cancellationToken).ConfigureAwait(false))
        {
            yield return record;
        }
    }

    /// <inheritdoc />
    public override object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreCollectionMetadata) ? this._collectionMetadata :
            serviceType == typeof(HttpClient) ? this._httpClient :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }

    #region private

    private async IAsyncEnumerable<VectorSearchResult<TRecord>> ExecuteQueryAsync(string query, bool includeVectors, string scorePropertyName, string operationName, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        using var request = new WeaviateVectorSearchRequest(query).Build();

        var (responseModel, content) = await this.ExecuteRequestWithResponseContentAsync<WeaviateVectorSearchResponse>(request, cancellationToken).ConfigureAwait(false);

        var collectionResults = responseModel?.Data?.GetOperation?[this.Name];

        if (collectionResults is null)
        {
            throw new VectorStoreException($"Error occurred during vector search. Response: {content}")
            {
                VectorStoreSystemName = WeaviateConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this.Name,
                OperationName = operationName
            };
        }

        foreach (var result in collectionResults)
        {
            if (result is not null)
            {
                var (storageModel, score) = WeaviateCollectionSearchMapping.MapSearchResult(result, scorePropertyName, this._hasNamedVectors);

                var record = this._mapper.MapFromStorageToDataModel(storageModel, includeVectors);

                yield return new VectorSearchResult<TRecord>(record, score);
            }
        }
    }

    private Task<HttpResponseMessage> ExecuteRequestAsync(
        HttpRequestMessage request,
        bool ensureSuccessStatusCode = true,
        CancellationToken cancellationToken = default)
    {
        request.RequestUri = new Uri(this._endpoint, request.RequestUri!);

        if (!string.IsNullOrWhiteSpace(this._apiKey))
        {
            request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", this._apiKey);
        }

        return VectorStoreErrorHandler.RunOperationAsync<HttpResponseMessage, HttpRequestException>(
            this._collectionMetadata,
            $"{request.Method} {request.RequestUri}",
            async () =>
            {
                var response = await this._httpClient
                    .SendAsync(request, HttpCompletionOption.ResponseContentRead, cancellationToken)
                    .ConfigureAwait(false);

                if (ensureSuccessStatusCode)
                {
                    response.EnsureSuccessStatusCode();
                }

                return response;
            });
    }

    private async Task<(TResponse?, string)> ExecuteRequestWithResponseContentAsync<TResponse>(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        var response = await this.ExecuteRequestAsync(request, ensureSuccessStatusCode: true, cancellationToken: cancellationToken).ConfigureAwait(false);

        var responseContent = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);

        var responseModel = VectorStoreErrorHandler.RunOperation<TResponse?, JsonException>(
            this._collectionMetadata,
            $"{request.Method} {request.RequestUri}",
            () => JsonSerializer.Deserialize<TResponse>(responseContent, WeaviateConstants.s_jsonSerializerOptions));

        return (responseModel, responseContent);
    }

    private async Task<TResponse?> ExecuteRequestAsync<TResponse>(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        var (model, _) = await this.ExecuteRequestWithResponseContentAsync<TResponse>(request, cancellationToken).ConfigureAwait(false);

        return model;
    }

    private async Task<TResponse?> ExecuteRequestWithNotFoundHandlingAsync<TResponse>(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        var response = await this.ExecuteRequestAsync(request, ensureSuccessStatusCode: false, cancellationToken: cancellationToken).ConfigureAwait(false);

        if (response.StatusCode == HttpStatusCode.NotFound)
        {
            return default;
        }

        response.EnsureSuccessStatusCode();

        var responseContent = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);

        var responseModel = VectorStoreErrorHandler.RunOperation<TResponse?, JsonException>(
            this._collectionMetadata,
            $"{request.Method} {request.RequestUri}",
            () => JsonSerializer.Deserialize<TResponse>(responseContent, WeaviateConstants.s_jsonSerializerOptions));

        return responseModel;
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
