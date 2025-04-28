// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Linq.Expressions;
using System.Runtime.CompilerServices;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Azure.Search.Documents;
using Azure.Search.Documents.Indexes;
using Azure.Search.Documents.Indexes.Models;
using Azure.Search.Documents.Models;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

/// <summary>
/// Service for storing and retrieving vector records, that uses Azure AI Search as the underlying storage.
/// </summary>
/// <typeparam name="TKey">The data type of the record key. Can be either <see cref="string"/>, or <see cref="object"/> for dynamic mapping.</typeparam>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
#pragma warning disable CS0618 // IVectorizableTextSearch is obsolete
public sealed class AzureAISearchVectorStoreRecordCollection<TKey, TRecord> :
    IVectorStoreRecordCollection<TKey, TRecord>,
    IVectorizableTextSearch<TRecord>,
    IKeywordHybridSearch<TRecord>
    where TKey : notnull
    where TRecord : notnull
#pragma warning restore CS0618 // IVectorizableTextSearch is obsolete
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    /// <summary>Metadata about vector store record collection.</summary>
    private readonly VectorStoreRecordCollectionMetadata _collectionMetadata;

    /// <summary>The default options for vector search.</summary>
    private static readonly VectorSearchOptions<TRecord> s_defaultVectorSearchOptions = new();

    /// <summary>The default options for hybrid vector search.</summary>
    private static readonly HybridSearchOptions<TRecord> s_defaultKeywordVectorizedHybridSearchOptions = new();

    /// <summary>Azure AI Search client that can be used to manage the list of indices in an Azure AI Search Service.</summary>
    private readonly SearchIndexClient _searchIndexClient;

    /// <summary>Azure AI Search client that can be used to manage data in an Azure AI Search Service index.</summary>
    private readonly SearchClient _searchClient;

    /// <summary>The name of the collection that this <see cref="AzureAISearchVectorStoreRecordCollection{TKey, TRecord}"/> will access.</summary>
    private readonly string _collectionName;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly AzureAISearchVectorStoreRecordCollectionOptions<TRecord> _options;

    /// <summary>A mapper to use for converting between the data model and the Azure AI Search record.</summary>
    private readonly AzureAISearchDynamicDataModelMapper? _dynamicMapper;

    /// <summary>The model for this collection.</summary>
    private readonly VectorStoreRecordModel _model;

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureAISearchVectorStoreRecordCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="searchIndexClient">Azure AI Search client that can be used to manage the list of indices in an Azure AI Search Service.</param>
    /// <param name="name">The name of the collection that this <see cref="AzureAISearchVectorStoreRecordCollection{TKey, TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    /// <exception cref="ArgumentNullException">Thrown when <paramref name="searchIndexClient"/> is null.</exception>
    /// <exception cref="ArgumentException">Thrown when options are misconfigured.</exception>
    public AzureAISearchVectorStoreRecordCollection(SearchIndexClient searchIndexClient, string name, AzureAISearchVectorStoreRecordCollectionOptions<TRecord>? options = default)
    {
        // Verify.
        Verify.NotNull(searchIndexClient);
        Verify.NotNullOrWhiteSpace(name);

        if (typeof(TKey) != typeof(string) && typeof(TKey) != typeof(object))
        {
            throw new NotSupportedException("Only string keys are supported (and object for dynamic mapping)");
        }

        // Assign.
        this._searchIndexClient = searchIndexClient;
        this._collectionName = name;
        this._options = options ?? new AzureAISearchVectorStoreRecordCollectionOptions<TRecord>();
        this._searchClient = this._searchIndexClient.GetSearchClient(name);

        this._model = typeof(TRecord) == typeof(Dictionary<string, object?>) ?
            new AzureAISearchDynamicModelBuilder().Build(typeof(TRecord), this._options.VectorStoreRecordDefinition, this._options.EmbeddingGenerator) :
            new AzureAISearchModelBuilder().Build(typeof(TRecord), this._options.VectorStoreRecordDefinition, this._options.EmbeddingGenerator, this._options.JsonSerializerOptions);

        // Resolve mapper.
        // If they didn't provide a custom mapper, and the record type is the generic data model, use the built in mapper for that.
        // Otherwise, don't set the mapper, and we'll default to just using Azure AI Search's built in json serialization and deserialization.
        if (typeof(TRecord) == typeof(Dictionary<string, object?>))
        {
            this._dynamicMapper = new AzureAISearchDynamicDataModelMapper(this._model);
        }

        this._collectionMetadata = new()
        {
            VectorStoreSystemName = AzureAISearchConstants.VectorStoreSystemName,
            VectorStoreName = searchIndexClient.ServiceName,
            CollectionName = name
        };
    }

    /// <inheritdoc />
    public string Name => this._collectionName;

    /// <inheritdoc />
    public async Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            await this._searchIndexClient.GetIndexAsync(this._collectionName, cancellationToken).ConfigureAwait(false);
            return true;
        }
        catch (RequestFailedException ex) when (ex.Status == 404)
        {
            return false;
        }
        catch (RequestFailedException ex)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = AzureAISearchConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this._collectionName,
                OperationName = "GetIndex"
            };
        }
    }

    /// <inheritdoc />
    public Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        var vectorSearchConfig = new VectorSearch();
        var searchFields = new List<SearchField>();

        // Loop through all properties and create the search fields.
        foreach (var property in this._model.Properties)
        {
            switch (property)
            {
                case VectorStoreRecordKeyPropertyModel p:
                    searchFields.Add(AzureAISearchVectorStoreCollectionCreateMapping.MapKeyField(p));
                    break;

                case VectorStoreRecordDataPropertyModel p:
                    searchFields.Add(AzureAISearchVectorStoreCollectionCreateMapping.MapDataField(p));
                    break;

                case VectorStoreRecordVectorPropertyModel p:
                    (VectorSearchField vectorSearchField, VectorSearchAlgorithmConfiguration algorithmConfiguration, VectorSearchProfile vectorSearchProfile) = AzureAISearchVectorStoreCollectionCreateMapping.MapVectorField(p);

                    // Add the search field, plus its profile and algorithm configuration to the search config.
                    searchFields.Add(vectorSearchField);
                    vectorSearchConfig.Algorithms.Add(algorithmConfiguration);
                    vectorSearchConfig.Profiles.Add(vectorSearchProfile);
                    break;

                default:
                    throw new UnreachableException();
            }
        }

        // Create the index.
        var searchIndex = new SearchIndex(this._collectionName, searchFields);
        searchIndex.VectorSearch = vectorSearchConfig;

        return this.RunOperationAsync(
            "CreateIndex",
            () => this._searchIndexClient.CreateIndexAsync(searchIndex, cancellationToken));
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
        return this.RunOperationAsync<Response>(
            "DeleteIndex",
            async () =>
            {
                try
                {
                    return await this._searchIndexClient.DeleteIndexAsync(this._collectionName, cancellationToken).ConfigureAwait(false);
                }
                catch (RequestFailedException ex) when (ex.Status == 404)
                {
                    return null!;
                }
            });
    }

    /// <inheritdoc />
    public Task<TRecord?> GetAsync(TKey key, GetRecordOptions? options = default, CancellationToken cancellationToken = default)
    {
        // Create Options.
        var innerOptions = this.ConvertGetDocumentOptions(options);
        var includeVectors = options?.IncludeVectors ?? false;

        // Get record.
        return this.GetDocumentAndMapToDataModelAsync(key, includeVectors, innerOptions, cancellationToken);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetAsync(IEnumerable<TKey> keys, GetRecordOptions? options = default, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        // Create Options
        var innerOptions = this.ConvertGetDocumentOptions(options);
        var includeVectors = options?.IncludeVectors ?? false;

        // Get records in parallel.
        var tasks = keys.Select(key => this.GetDocumentAndMapToDataModelAsync(key, includeVectors, innerOptions, cancellationToken));
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
    public Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        var stringKey = this.GetStringKey(key);

        // Remove record.
        return this.RunOperationAsync(
            "DeleteDocuments",
            () => this._searchClient.DeleteDocumentsAsync(this._model.KeyProperty.StorageName, [stringKey], new IndexDocumentsOptions(), cancellationToken));
    }

    /// <inheritdoc />
    public Task DeleteAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);
        if (!keys.Any())
        {
            return Task.CompletedTask;
        }

        var stringKeys = keys is IEnumerable<string> k ? k : keys.Cast<string>();

        // Remove records.
        return this.RunOperationAsync(
            "DeleteDocuments",
            () => this._searchClient.DeleteDocumentsAsync(this._model.KeyProperty.StorageName, stringKeys, new IndexDocumentsOptions(), cancellationToken));
    }

    /// <inheritdoc />
    public async Task<TKey> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        // Create options.
        var innerOptions = new IndexDocumentsOptions { ThrowOnAnyError = true };

        // Upsert record.
        var results = await this.MapToStorageModelAndUploadDocumentAsync([record], innerOptions, cancellationToken).ConfigureAwait(false);

        return (TKey)(object)results.Value.Results[0].Key;
    }

    /// <inheritdoc />
    public async Task<IReadOnlyList<TKey>> UpsertAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);
        if (!records.Any())
        {
            return [];
        }

        // Create Options
        var innerOptions = new IndexDocumentsOptions { ThrowOnAnyError = true };

        // Upsert records
        var results = await this.MapToStorageModelAndUploadDocumentAsync(records, innerOptions, cancellationToken).ConfigureAwait(false);

        return results.Value.Results.Select(x => (TKey)(object)x.Key).ToList();
    }

    /// <inheritdoc />
    public IAsyncEnumerable<VectorSearchResult<TRecord>> SearchEmbeddingAsync<TVector>(
        TVector vector,
        int top,
        VectorSearchOptions<TRecord>? options = null,
        CancellationToken cancellationToken = default)
        where TVector : notnull
    {
        options ??= s_defaultVectorSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle(options);

        var floatVector = VerifyVectorParam(vector);
        Verify.NotLessThan(top, 1);

        // Configure search settings.
        var vectorQueries = new List<VectorQuery>
        {
            new VectorizedQuery(floatVector) { KNearestNeighborsCount = top, Fields = { vectorProperty.StorageName } }
        };

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
        // Build filter object.
        var filter = options switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => AzureAISearchVectorStoreCollectionSearchMapping.BuildLegacyFilterString(legacyFilter, this._model),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => new AzureAISearchFilterTranslator().Translate(newFilter, this._model),
            _ => null
        };
#pragma warning restore CS0618

        // Build search options.
        var searchOptions = new SearchOptions
        {
            VectorSearch = new(),
            Size = top,
            Skip = options.Skip,
        };

        if (filter is not null)
        {
            searchOptions.Filter = filter;
        }

        searchOptions.VectorSearch.Queries.AddRange(vectorQueries);

        // Filter out vector fields if requested.
        if (!options.IncludeVectors)
        {
            searchOptions.Select.Add(this._model.KeyProperty.StorageName);

            foreach (var dataProperty in this._model.DataProperties)
            {
                searchOptions.Select.Add(dataProperty.StorageName);
            }
        }

        return this.SearchAndMapToDataModelAsync(null, searchOptions, options.IncludeVectors, cancellationToken);
    }

    /// <inheritdoc />
    [Obsolete("Use either SearchEmbeddingAsync to search directly on embeddings, or SearchAsync to handle embedding generation internally as part of the call.")]
    public IAsyncEnumerable<VectorSearchResult<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, int top, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
        where TVector : notnull
        => this.SearchEmbeddingAsync(vector, top, options, cancellationToken);

    /// <inheritdoc />
    public IAsyncEnumerable<TRecord> GetAsync(Expression<Func<TRecord, bool>> filter, int top,
        GetFilteredRecordOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(filter);
        Verify.NotLessThan(top, 1);

        options ??= new();

        SearchOptions searchOptions = new()
        {
            VectorSearch = new(),
            Size = top,
            Skip = options.Skip,
            Filter = new AzureAISearchFilterTranslator().Translate(filter, this._model),
        };

        // Filter out vector fields if requested.
        if (!options.IncludeVectors)
        {
            searchOptions.Select.Add(this._model.KeyProperty.StorageName);

            foreach (var dataProperty in this._model.DataProperties)
            {
                searchOptions.Select.Add(dataProperty.StorageName);
            }
        }

        foreach (var pair in options.OrderBy.Values)
        {
            VectorStoreRecordPropertyModel property = this._model.GetDataOrKeyProperty(pair.PropertySelector);
            string name = property.StorageName;
            // From https://learn.microsoft.com/dotnet/api/azure.search.documents.searchoptions.orderby:
            // "Each expression can be followed by asc to indicate ascending, or desc to indicate descending".
            // "The default is ascending order."
            if (!pair.Ascending)
            {
                name += " desc";
            }

            searchOptions.OrderBy.Add(name);
        }

        return this.SearchAndMapToDataModelAsync(null, searchOptions, options.IncludeVectors, cancellationToken)
            .SelectAsync(result => result.Record, cancellationToken);
    }

    /// <inheritdoc />
    public IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TInput>(
        TInput value,
        int top,
        VectorSearchOptions<TRecord>? options = default,
        CancellationToken cancellationToken = default)
        where TInput : notnull
    {
        var searchText = value switch
        {
            string s => s,
            null => throw new ArgumentNullException(nameof(value)),
            _ => throw new ArgumentException($"The provided search type '{value?.GetType().Name}' is not supported by the Azure AI Search connector, pass a string.")
        };

        Verify.NotNull(searchText);
        Verify.NotLessThan(top, 1);

        if (this._model.VectorProperties.Count == 0)
        {
            throw new InvalidOperationException("The collection does not have any vector fields, so vector search is not possible.");
        }

        // Resolve options.
        options ??= s_defaultVectorSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle(options);

        // Configure search settings.
        var vectorQueries = new List<VectorQuery>
        {
            new VectorizableTextQuery(searchText) { KNearestNeighborsCount = top, Fields = { vectorProperty.StorageName } }
        };

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
        // Build filter object.
        var filter = options switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => AzureAISearchVectorStoreCollectionSearchMapping.BuildLegacyFilterString(legacyFilter, this._model),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => new AzureAISearchFilterTranslator().Translate(newFilter, this._model),
            _ => null
        };
#pragma warning restore CS0618

        // Build search options.
        var searchOptions = new SearchOptions
        {
            VectorSearch = new(),
            Size = top,
            Skip = options.Skip,
        };

        if (filter is not null)
        {
            searchOptions.Filter = filter;
        }

        searchOptions.VectorSearch.Queries.AddRange(vectorQueries);

        // Filter out vector fields if requested.
        if (!options.IncludeVectors)
        {
            searchOptions.Select.Add(this._model.KeyProperty.StorageName);

            foreach (var dataProperty in this._model.DataProperties)
            {
                searchOptions.Select.Add(dataProperty.StorageName);
            }
        }

        return this.SearchAndMapToDataModelAsync(null, searchOptions, options.IncludeVectors, cancellationToken);
    }

    /// <inheritdoc />
    [Obsolete("Use SearchAsync")]
    public IAsyncEnumerable<VectorSearchResult<TRecord>> VectorizableTextSearchAsync(string searchText, int top, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
        => this.SearchAsync(searchText, top, options, cancellationToken);

    /// <inheritdoc />
    public IAsyncEnumerable<VectorSearchResult<TRecord>> HybridSearchAsync<TVector>(TVector vector, ICollection<string> keywords, int top, HybridSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keywords);
        var floatVector = VerifyVectorParam(vector);
        Verify.NotLessThan(top, 1);

        // Resolve options.
        options ??= s_defaultKeywordVectorizedHybridSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle<TRecord>(new() { VectorProperty = options.VectorProperty });
        var textDataProperty = this._model.GetFullTextDataPropertyOrSingle(options.AdditionalProperty);

        // Configure search settings.
        var vectorQueries = new List<VectorQuery>
        {
            new VectorizedQuery(floatVector) { KNearestNeighborsCount = top, Fields = { vectorProperty.StorageName } }
        };

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
        // Build filter object.
        var filter = options switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => AzureAISearchVectorStoreCollectionSearchMapping.BuildLegacyFilterString(legacyFilter, this._model),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => new AzureAISearchFilterTranslator().Translate(newFilter, this._model),
            _ => null
        };
#pragma warning restore CS0618

        // Build search options.
        var searchOptions = new SearchOptions
        {
            VectorSearch = new(),
            Size = top,
            Skip = options.Skip,
            Filter = filter,
            IncludeTotalCount = options.IncludeTotalCount,
        };
        searchOptions.VectorSearch.Queries.AddRange(vectorQueries);
        searchOptions.SearchFields.Add(textDataProperty.StorageName);

        // Filter out vector fields if requested.
        if (!options.IncludeVectors)
        {
            searchOptions.Select.Add(this._model.KeyProperty.StorageName);

            foreach (var dataProperty in this._model.DataProperties)
            {
                searchOptions.Select.Add(dataProperty.StorageName);
            }
        }

        var keywordsCombined = string.Join(" ", keywords);

        return this.SearchAndMapToDataModelAsync(keywordsCombined, searchOptions, options.IncludeVectors, cancellationToken);
    }

    /// <inheritdoc />
    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreRecordCollectionMetadata) ? this._collectionMetadata :
            serviceType == typeof(SearchIndexClient) ? this._searchIndexClient :
            serviceType == typeof(SearchClient) ? this._searchClient :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }

    /// <summary>
    /// Get the document with the given key and map it to the data model using the configured mapper type.
    /// </summary>
    /// <param name="key">The key of the record to get.</param>
    /// <param name="includeVectors">A value indicating whether to include vectors in the result or not.</param>
    /// <param name="innerOptions">The Azure AI Search sdk options for getting a document.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The retrieved document, mapped to the consumer data model.</returns>
    private async Task<TRecord?> GetDocumentAndMapToDataModelAsync(
        TKey key,
        bool includeVectors,
        GetDocumentOptions innerOptions,
        CancellationToken cancellationToken)
    {
        const string OperationName = "GetDocument";

        var stringKey = this.GetStringKey(key);

        // Use the user provided mapper.
        if (this._dynamicMapper is not null)
        {
            Debug.Assert(typeof(TRecord) == typeof(Dictionary<string, object?>));

            var jsonObject = await this.RunOperationAsync(
                OperationName,
                () => GetDocumentWithNotFoundHandlingAsync<JsonObject>(this._searchClient, stringKey, innerOptions, cancellationToken)).ConfigureAwait(false);

            if (jsonObject is null)
            {
                return default;
            }

            return VectorStoreErrorHandler.RunModelConversion(
                AzureAISearchConstants.VectorStoreSystemName,
                this._collectionMetadata.VectorStoreName,
                this._collectionName,
                OperationName,
                () => (TRecord)(object)this._dynamicMapper!.MapFromStorageToDataModel(jsonObject, new() { IncludeVectors = includeVectors }));
        }

        // Use the built in Azure AI Search mapper.
        return await this.RunOperationAsync(
            OperationName,
            () => GetDocumentWithNotFoundHandlingAsync<TRecord>(this._searchClient, stringKey, innerOptions, cancellationToken)).ConfigureAwait(false);
    }

    /// <summary>
    /// Search for the documents matching the given options and map them to the data model using the configured mapper type.
    /// </summary>
    /// <param name="searchText">Text to use if doing a hybrid search. Null for non-hybrid search.</param>
    /// <param name="searchOptions">The options controlling the behavior of the search operation.</param>
    /// <param name="includeVectors">A value indicating whether to include vectors in the result or not.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The mapped search results.</returns>
    private async IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAndMapToDataModelAsync(
        string? searchText,
        SearchOptions searchOptions,
        bool includeVectors,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        const string OperationName = "Search";

        // Execute search and map using the user provided mapper.
        if (this._dynamicMapper is not null)
        {
            Debug.Assert(typeof(TRecord) == typeof(Dictionary<string, object?>));

            var jsonObjectResults = await this.RunOperationAsync(
                OperationName,
                () => this._searchClient.SearchAsync<JsonObject>(searchText, searchOptions, cancellationToken)).ConfigureAwait(false);

            await foreach (var result in this.MapSearchResultsAsync(jsonObjectResults.Value.GetResultsAsync(), OperationName, includeVectors).ConfigureAwait(false))
            {
                yield return result;
            }

            yield break;
        }

        // Execute search and map using the built in Azure AI Search mapper.
        Response<SearchResults<TRecord>> results = await this.RunOperationAsync(OperationName, () => this._searchClient.SearchAsync<TRecord>(searchText, searchOptions, cancellationToken)).ConfigureAwait(false);
        await foreach (var result in this.MapSearchResultsAsync(results.Value.GetResultsAsync()).ConfigureAwait(false))
        {
            yield return result;
        }
    }

    /// <summary>
    /// Map the data model to the storage model and upload the document.
    /// </summary>
    /// <param name="records">The records to upload.</param>
    /// <param name="innerOptions">The Azure AI Search sdk options for uploading a document.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The document upload result.</returns>
    private Task<Response<IndexDocumentsResult>> MapToStorageModelAndUploadDocumentAsync(
        IEnumerable<TRecord> records,
        IndexDocumentsOptions innerOptions,
        CancellationToken cancellationToken)
    {
        const string OperationName = "UploadDocuments";

        // Use the user provided mapper.
        if (this._dynamicMapper is not null)
        {
            Debug.Assert(typeof(TRecord) == typeof(Dictionary<string, object?>));

            var jsonObjects = VectorStoreErrorHandler.RunModelConversion(
                AzureAISearchConstants.VectorStoreSystemName,
                this._collectionMetadata.VectorStoreName,
                this._collectionName,
                OperationName,
                () => records.Select(r => this._dynamicMapper!.MapFromDataToStorageModel((Dictionary<string, object?>)(object)r)));

            return this.RunOperationAsync(
                OperationName,
                () => this._searchClient.UploadDocumentsAsync<JsonObject>(jsonObjects, innerOptions, cancellationToken));
        }

        // Use the built in Azure AI Search mapper.
        return this.RunOperationAsync(
            OperationName,
            () => this._searchClient.UploadDocumentsAsync<TRecord>(records, innerOptions, cancellationToken));
    }

    /// <summary>
    /// Map the search results from <see cref="SearchResult{JsonObject}"/> to <see cref="VectorSearchResult{TRecord}"/> objects using the configured mapper type.
    /// </summary>
    /// <param name="results">The search results to map.</param>
    /// <param name="operationName">The name of the current operation for telemetry purposes.</param>
    /// <param name="includeVectors">A value indicating whether to include vectors in the resultset or not.</param>
    /// <returns>The mapped results.</returns>
    private async IAsyncEnumerable<VectorSearchResult<TRecord>> MapSearchResultsAsync(IAsyncEnumerable<SearchResult<JsonObject>> results, string operationName, bool includeVectors)
    {
        await foreach (var result in results.ConfigureAwait(false))
        {
            var document = VectorStoreErrorHandler.RunModelConversion(
                AzureAISearchConstants.VectorStoreSystemName,
                this._collectionMetadata.VectorStoreName,
                this._collectionName,
                operationName,
                () => (TRecord)(object)this._dynamicMapper!.MapFromStorageToDataModel(result.Document, new() { IncludeVectors = includeVectors }));
            yield return new VectorSearchResult<TRecord>(document, result.Score);
        }
    }

    /// <summary>
    /// Map the search results from <see cref="SearchResult{TRecord}"/> to <see cref="VectorSearchResult{TRecord}"/> objects.
    /// </summary>
    /// <param name="results">The search results to map.</param>
    /// <returns>The mapped results.</returns>
    private async IAsyncEnumerable<VectorSearchResult<TRecord>> MapSearchResultsAsync(IAsyncEnumerable<SearchResult<TRecord>> results)
    {
        await foreach (var result in results.ConfigureAwait(false))
        {
            yield return new VectorSearchResult<TRecord>(result.Document, result.Score);
        }
    }

    /// <summary>
    /// Convert the public <see cref="GetRecordOptions"/> options model to the Azure AI Search <see cref="GetDocumentOptions"/> options model.
    /// </summary>
    /// <param name="options">The public options model.</param>
    /// <returns>The Azure AI Search options model.</returns>
    private GetDocumentOptions ConvertGetDocumentOptions(GetRecordOptions? options)
    {
        var innerOptions = new GetDocumentOptions();
        if (options?.IncludeVectors is not true)
        {
            innerOptions.SelectedFields.Add(this._model.KeyProperty.StorageName);

            foreach (var dataProperty in this._model.DataProperties)
            {
                innerOptions.SelectedFields.Add(dataProperty.StorageName);
            }
        }

        return innerOptions;
    }

    /// <summary>
    /// Get a document with the given key, and return null if it is not found.
    /// </summary>
    /// <typeparam name="T">The type to deserialize the document to.</typeparam>
    /// <param name="searchClient">The search client to use when fetching the document.</param>
    /// <param name="key">The key of the record to get.</param>
    /// <param name="innerOptions">The Azure AI Search sdk options for getting a document.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The retrieved document, mapped to the consumer data model, or null if not found.</returns>
    private static async Task<T?> GetDocumentWithNotFoundHandlingAsync<T>(
        SearchClient searchClient,
        string key,
        GetDocumentOptions innerOptions,
        CancellationToken cancellationToken)
    {
        try
        {
            return await searchClient.GetDocumentAsync<T>(key, innerOptions, cancellationToken).ConfigureAwait(false);
        }
        catch (RequestFailedException ex) when (ex.Status == 404)
        {
            return default;
        }
    }

    /// <summary>
    /// Run the given operation and wrap any <see cref="RequestFailedException"/> with <see cref="VectorStoreOperationException"/>."/>
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
        catch (AggregateException ex) when (ex.InnerException is RequestFailedException innerEx)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = AzureAISearchConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this._collectionName,
                OperationName = operationName
            };
        }
        catch (RequestFailedException ex)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = AzureAISearchConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this._collectionName,
                OperationName = operationName
            };
        }
    }

    private static ReadOnlyMemory<float> VerifyVectorParam<TVector>(TVector vector)
    {
        Verify.NotNull(vector);

        if (vector is not ReadOnlyMemory<float> floatVector)
        {
            throw new NotSupportedException($"The provided vector type {vector.GetType().FullName} is not supported by the Azure AI Search connector.");
        }

        return floatVector;
    }

    private string GetStringKey(TKey key)
    {
        Verify.NotNull(key);

        var stringKey = key as string ?? throw new UnreachableException("string key should have been validated during model building");

        Verify.NotNullOrWhiteSpace(stringKey, nameof(key));

        return stringKey;
    }
}
