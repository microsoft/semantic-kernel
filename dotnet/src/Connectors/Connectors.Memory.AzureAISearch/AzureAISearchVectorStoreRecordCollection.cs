// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Azure.Search.Documents;
using Azure.Search.Documents.Indexes;
using Azure.Search.Documents.Indexes.Models;
using Azure.Search.Documents.Models;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

/// <summary>
/// Service for storing and retrieving vector records, that uses Azure AI Search as the underlying storage.
/// </summary>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public class AzureAISearchVectorStoreRecordCollection<TRecord> :
    IVectorStoreRecordCollection<string, TRecord>,
    IVectorizableTextSearch<TRecord>,
    IKeywordHybridSearch<TRecord>
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    /// <summary>The name of this database for telemetry purposes.</summary>
    private const string DatabaseName = "AzureAISearch";

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
        typeof(long),
        typeof(double),
        typeof(float),
        typeof(bool),
        typeof(DateTimeOffset),
        typeof(int?),
        typeof(long?),
        typeof(double?),
        typeof(float?),
        typeof(bool?),
        typeof(DateTimeOffset?),
    ];

    /// <summary>A set of types that vectors on the provided model may have.</summary>
    /// <remarks>
    /// Azure AI Search is adding support for more types than just float32, but these are not available for use via the
    /// SDK yet. We will update this list as the SDK is updated.
    /// <see href="https://learn.microsoft.com/en-us/rest/api/searchservice/supported-data-types#edm-data-types-for-vector-fields"/>
    /// </remarks>
    private static readonly HashSet<Type> s_supportedVectorTypes =
    [
        typeof(ReadOnlyMemory<float>),
        typeof(ReadOnlyMemory<float>?)
    ];

    /// <summary>The default options for vector search.</summary>
    private static readonly VectorSearchOptions<TRecord> s_defaultVectorSearchOptions = new();

    /// <summary>The default options for hybrid vector search.</summary>
    private static readonly HybridSearchOptions<TRecord> s_defaultKeywordVectorizedHybridSearchOptions = new();

    /// <summary>Azure AI Search client that can be used to manage the list of indices in an Azure AI Search Service.</summary>
    private readonly SearchIndexClient _searchIndexClient;

    /// <summary>Azure AI Search client that can be used to manage data in an Azure AI Search Service index.</summary>
    private readonly SearchClient _searchClient;

    /// <summary>The name of the collection that this <see cref="AzureAISearchVectorStoreRecordCollection{TRecord}"/> will access.</summary>
    private readonly string _collectionName;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly AzureAISearchVectorStoreRecordCollectionOptions<TRecord> _options;

    /// <summary>A mapper to use for converting between the data model and the Azure AI Search record.</summary>
    private readonly IVectorStoreRecordMapper<TRecord, JsonObject>? _mapper;

    /// <summary>A helper to access property information for the current data model and record definition.</summary>
    private readonly VectorStoreRecordPropertyReader _propertyReader;

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureAISearchVectorStoreRecordCollection{TRecord}"/> class.
    /// </summary>
    /// <param name="searchIndexClient">Azure AI Search client that can be used to manage the list of indices in an Azure AI Search Service.</param>
    /// <param name="collectionName">The name of the collection that this <see cref="AzureAISearchVectorStoreRecordCollection{TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    /// <exception cref="ArgumentNullException">Thrown when <paramref name="searchIndexClient"/> is null.</exception>
    /// <exception cref="ArgumentException">Thrown when options are misconfigured.</exception>
    public AzureAISearchVectorStoreRecordCollection(SearchIndexClient searchIndexClient, string collectionName, AzureAISearchVectorStoreRecordCollectionOptions<TRecord>? options = default)
    {
        // Verify.
        Verify.NotNull(searchIndexClient);
        Verify.NotNullOrWhiteSpace(collectionName);
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelKeyType(typeof(TRecord), options?.JsonObjectCustomMapper is not null, s_supportedKeyTypes);
        VectorStoreRecordPropertyVerification.VerifyGenericDataModelDefinitionSupplied(typeof(TRecord), options?.VectorStoreRecordDefinition is not null);

        // Assign.
        this._searchIndexClient = searchIndexClient;
        this._collectionName = collectionName;
        this._options = options ?? new AzureAISearchVectorStoreRecordCollectionOptions<TRecord>();
        this._searchClient = this._searchIndexClient.GetSearchClient(collectionName);
        this._propertyReader = new VectorStoreRecordPropertyReader(
            typeof(TRecord),
            this._options.VectorStoreRecordDefinition,
            new()
            {
                RequiresAtLeastOneVector = false,
                SupportsMultipleKeys = false,
                SupportsMultipleVectors = true,
                JsonSerializerOptions = this._options.JsonSerializerOptions ?? JsonSerializerOptions.Default
            });

        // Validate property types.
        this._propertyReader.VerifyKeyProperties(s_supportedKeyTypes);
        this._propertyReader.VerifyDataProperties(s_supportedDataTypes, supportEnumerable: true);
        this._propertyReader.VerifyVectorProperties(s_supportedVectorTypes);

        // Resolve mapper.
        // First, if someone has provided a custom mapper, use that.
        // If they didn't provide a custom mapper, and the record type is the generic data model, use the built in mapper for that.
        // Otherwise, don't set the mapper, and we'll default to just using Azure AI Search's built in json serialization and deserialization.
        if (this._options.JsonObjectCustomMapper is not null)
        {
            this._mapper = this._options.JsonObjectCustomMapper;
        }
        else if (typeof(TRecord) == typeof(VectorStoreGenericDataModel<string>))
        {
            this._mapper = new AzureAISearchGenericDataModelMapper(this._propertyReader.RecordDefinition) as IVectorStoreRecordMapper<TRecord, JsonObject>;
        }
    }

    /// <inheritdoc />
    public string CollectionName => this._collectionName;

    /// <inheritdoc />
    public virtual async Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
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
                VectorStoreType = DatabaseName,
                CollectionName = this._collectionName,
                OperationName = "GetIndex"
            };
        }
    }

    /// <inheritdoc />
    public virtual Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        var vectorSearchConfig = new VectorSearch();
        var searchFields = new List<SearchField>();

        // Loop through all properties and create the search fields.
        foreach (var property in this._propertyReader.Properties)
        {
            // Key property.
            if (property is VectorStoreRecordKeyProperty keyProperty)
            {
                searchFields.Add(AzureAISearchVectorStoreCollectionCreateMapping.MapKeyField(
                    keyProperty,
                    this._propertyReader.KeyPropertyJsonName));
            }

            // Data property.
            if (property is VectorStoreRecordDataProperty dataProperty)
            {
                searchFields.Add(AzureAISearchVectorStoreCollectionCreateMapping.MapDataField(
                    dataProperty,
                    this._propertyReader.GetJsonPropertyName(dataProperty.DataModelPropertyName)));
            }

            // Vector property.
            if (property is VectorStoreRecordVectorProperty vectorProperty)
            {
                (VectorSearchField vectorSearchField, VectorSearchAlgorithmConfiguration algorithmConfiguration, VectorSearchProfile vectorSearchProfile) = AzureAISearchVectorStoreCollectionCreateMapping.MapVectorField(
                    vectorProperty,
                    this._propertyReader.GetJsonPropertyName(vectorProperty.DataModelPropertyName));

                // Add the search field, plus its profile and algorithm configuration to the search config.
                searchFields.Add(vectorSearchField);
                vectorSearchConfig.Algorithms.Add(algorithmConfiguration);
                vectorSearchConfig.Profiles.Add(vectorSearchProfile);
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
        return this.RunOperationAsync(
            "DeleteIndex",
            () => this._searchIndexClient.DeleteIndexAsync(this._collectionName, cancellationToken));
    }

    /// <inheritdoc />
    public virtual Task<TRecord?> GetAsync(string key, GetRecordOptions? options = default, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(key);

        // Create Options.
        var innerOptions = this.ConvertGetDocumentOptions(options);
        var includeVectors = options?.IncludeVectors ?? false;

        // Get record.
        return this.GetDocumentAndMapToDataModelAsync(key, includeVectors, innerOptions, cancellationToken);
    }

    /// <inheritdoc />
    public virtual async IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<string> keys, GetRecordOptions? options = default, [EnumeratorCancellation] CancellationToken cancellationToken = default)
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
    public virtual Task DeleteAsync(string key, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(key);

        // Remove record.
        return this.RunOperationAsync(
            "DeleteDocuments",
            () => this._searchClient.DeleteDocumentsAsync(this._propertyReader.KeyPropertyJsonName, [key], new IndexDocumentsOptions(), cancellationToken));
    }

    /// <inheritdoc />
    public virtual Task DeleteBatchAsync(IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        // Remove records.
        return this.RunOperationAsync(
            "DeleteDocuments",
            () => this._searchClient.DeleteDocumentsAsync(this._propertyReader.KeyPropertyJsonName, keys, new IndexDocumentsOptions(), cancellationToken));
    }

    /// <inheritdoc />
    public virtual async Task<string> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        // Create options.
        var innerOptions = new IndexDocumentsOptions { ThrowOnAnyError = true };

        // Upsert record.
        var results = await this.MapToStorageModelAndUploadDocumentAsync([record], innerOptions, cancellationToken).ConfigureAwait(false);
        return results.Value.Results[0].Key;
    }

    /// <inheritdoc />
    public virtual async IAsyncEnumerable<string> UpsertBatchAsync(IEnumerable<TRecord> records, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        // Create Options
        var innerOptions = new IndexDocumentsOptions { ThrowOnAnyError = true };

        // Upsert records
        var results = await this.MapToStorageModelAndUploadDocumentAsync(records, innerOptions, cancellationToken).ConfigureAwait(false);

        // Get results
        var resultKeys = results.Value.Results.Select(x => x.Key).ToList();
        foreach (var resultKey in resultKeys) { yield return resultKey; }
    }

    /// <inheritdoc />
    public virtual Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        var floatVector = VerifyVectorParam(vector);

        // Resolve options.
        var internalOptions = options ?? s_defaultVectorSearchOptions;
        var vectorProperty = this._propertyReader.GetVectorPropertyOrSingle(internalOptions);
        var vectorPropertyName = this._propertyReader.GetJsonPropertyName(vectorProperty!.DataModelPropertyName);

        // Configure search settings.
        var vectorQueries = new List<VectorQuery>();
        vectorQueries.Add(new VectorizedQuery(floatVector) { KNearestNeighborsCount = internalOptions.Top, Fields = { vectorPropertyName } });

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
        // Build filter object.
        var filter = internalOptions switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => AzureAISearchVectorStoreCollectionSearchMapping.BuildLegacyFilterString(legacyFilter, this._propertyReader.JsonPropertyNamesMap),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => new AzureAISearchFilterTranslator().Translate(newFilter, this._propertyReader.StoragePropertyNamesMap),
            _ => null
        };
#pragma warning restore CS0618

        // Build search options.
        var searchOptions = new SearchOptions
        {
            VectorSearch = new(),
            Size = internalOptions.Top,
            Skip = internalOptions.Skip,
            IncludeTotalCount = internalOptions.IncludeTotalCount,
        };

        if (filter is not null)
        {
            searchOptions.Filter = filter;
        }

        searchOptions.VectorSearch.Queries.AddRange(vectorQueries);

        // Filter out vector fields if requested.
        if (!internalOptions.IncludeVectors)
        {
            searchOptions.Select.Add(this._propertyReader.KeyPropertyJsonName);
            searchOptions.Select.AddRange(this._propertyReader.DataPropertyJsonNames);
        }

        return this.SearchAndMapToDataModelAsync(null, searchOptions, internalOptions.IncludeVectors, cancellationToken);
    }

    /// <inheritdoc />
    public virtual Task<VectorSearchResults<TRecord>> VectorizableTextSearchAsync(string searchText, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(searchText);

        if (this._propertyReader.FirstVectorPropertyName is null)
        {
            throw new InvalidOperationException("The collection does not have any vector fields, so vector search is not possible.");
        }

        // Resolve options.
        var internalOptions = options ?? s_defaultVectorSearchOptions;
        var vectorProperty = this._propertyReader.GetVectorPropertyOrSingle(internalOptions);
        var vectorPropertyName = this._propertyReader.GetJsonPropertyName(vectorProperty!.DataModelPropertyName);

        // Configure search settings.
        var vectorQueries = new List<VectorQuery>();
        vectorQueries.Add(new VectorizableTextQuery(searchText) { KNearestNeighborsCount = internalOptions.Top, Fields = { vectorPropertyName } });

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
        // Build filter object.
        var filter = internalOptions switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => AzureAISearchVectorStoreCollectionSearchMapping.BuildLegacyFilterString(legacyFilter, this._propertyReader.JsonPropertyNamesMap),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => new AzureAISearchFilterTranslator().Translate(newFilter, this._propertyReader.StoragePropertyNamesMap),
            _ => null
        };
#pragma warning restore CS0618

        // Build search options.
        var searchOptions = new SearchOptions
        {
            VectorSearch = new(),
            Size = internalOptions.Top,
            Skip = internalOptions.Skip,
            IncludeTotalCount = internalOptions.IncludeTotalCount,
        };

        if (filter is not null)
        {
            searchOptions.Filter = filter;
        }

        searchOptions.VectorSearch.Queries.AddRange(vectorQueries);

        // Filter out vector fields if requested.
        if (!internalOptions.IncludeVectors)
        {
            searchOptions.Select.Add(this._propertyReader.KeyPropertyJsonName);
            searchOptions.Select.AddRange(this._propertyReader.DataPropertyJsonNames);
        }

        return this.SearchAndMapToDataModelAsync(null, searchOptions, internalOptions.IncludeVectors, cancellationToken);
    }

    /// <inheritdoc />
    public Task<VectorSearchResults<TRecord>> HybridSearchAsync<TVector>(TVector vector, ICollection<string> keywords, HybridSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keywords);
        var floatVector = VerifyVectorParam(vector);

        // Resolve options.
        var internalOptions = options ?? s_defaultKeywordVectorizedHybridSearchOptions;
        var vectorProperty = this._propertyReader.GetVectorPropertyOrSingle<TRecord>(new() { VectorProperty = internalOptions.VectorProperty });
        var vectorPropertyName = this._propertyReader.GetJsonPropertyName(vectorProperty.DataModelPropertyName);
        var textDataProperty = this._propertyReader.GetFullTextDataPropertyOrSingle(internalOptions.AdditionalProperty);
        var textDataPropertyName = this._propertyReader.GetJsonPropertyName(textDataProperty.DataModelPropertyName);

        // Configure search settings.
        var vectorQueries = new List<VectorQuery>();
        vectorQueries.Add(new VectorizedQuery(floatVector) { KNearestNeighborsCount = internalOptions.Top, Fields = { vectorPropertyName } });

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
        // Build filter object.
        var filter = internalOptions switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => AzureAISearchVectorStoreCollectionSearchMapping.BuildLegacyFilterString(legacyFilter, this._propertyReader.JsonPropertyNamesMap),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => new AzureAISearchFilterTranslator().Translate(newFilter, this._propertyReader.StoragePropertyNamesMap),
            _ => null
        };
#pragma warning restore CS0618

        // Build search options.
        var searchOptions = new SearchOptions
        {
            VectorSearch = new(),
            Size = internalOptions.Top,
            Skip = internalOptions.Skip,
            Filter = filter,
            IncludeTotalCount = internalOptions.IncludeTotalCount,
        };
        searchOptions.VectorSearch.Queries.AddRange(vectorQueries);
        searchOptions.SearchFields.Add(textDataPropertyName);

        // Filter out vector fields if requested.
        if (!internalOptions.IncludeVectors)
        {
            searchOptions.Select.Add(this._propertyReader.KeyPropertyJsonName);
            searchOptions.Select.AddRange(this._propertyReader.DataPropertyJsonNames);
        }

        var keywordsCombined = string.Join(" ", keywords);

        return this.SearchAndMapToDataModelAsync(keywordsCombined, searchOptions, internalOptions.IncludeVectors, cancellationToken);
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
        string key,
        bool includeVectors,
        GetDocumentOptions innerOptions,
        CancellationToken cancellationToken)
    {
        const string OperationName = "GetDocument";

        // Use the user provided mapper.
        if (this._mapper is not null)
        {
            var jsonObject = await this.RunOperationAsync(
                OperationName,
                () => GetDocumentWithNotFoundHandlingAsync<JsonObject>(this._searchClient, key, innerOptions, cancellationToken)).ConfigureAwait(false);

            if (jsonObject is null)
            {
                return default;
            }

            return VectorStoreErrorHandler.RunModelConversion(
                DatabaseName,
                this._collectionName,
                OperationName,
                () => this._mapper!.MapFromStorageToDataModel(jsonObject, new() { IncludeVectors = includeVectors }));
        }

        // Use the built in Azure AI Search mapper.
        return await this.RunOperationAsync(
            OperationName,
            () => GetDocumentWithNotFoundHandlingAsync<TRecord>(this._searchClient, key, innerOptions, cancellationToken)).ConfigureAwait(false);
    }

    /// <summary>
    /// Search for the documents matching the given options and map them to the data model using the configured mapper type.
    /// </summary>
    /// <param name="searchText">Text to use if doing a hybrid search. Null for non-hybrid search.</param>
    /// <param name="searchOptions">The options controlling the behavior of the search operation.</param>
    /// <param name="includeVectors">A value indicating whether to include vectors in the result or not.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The mapped search results.</returns>
    private async Task<VectorSearchResults<TRecord>> SearchAndMapToDataModelAsync(
        string? searchText,
        SearchOptions searchOptions,
        bool includeVectors,
        CancellationToken cancellationToken)
    {
        const string OperationName = "Search";

        // Execute search and map using the user provided mapper.
        if (this._options.JsonObjectCustomMapper is not null)
        {
            var jsonObjectResults = await this.RunOperationAsync(
                OperationName,
                () => this._searchClient.SearchAsync<JsonObject>(searchText, searchOptions, cancellationToken)).ConfigureAwait(false);

            var mappedJsonObjectResults = this.MapSearchResultsAsync(jsonObjectResults.Value.GetResultsAsync(), OperationName, includeVectors);
            return new VectorSearchResults<TRecord>(mappedJsonObjectResults) { TotalCount = jsonObjectResults.Value.TotalCount };
        }

        // Execute search and map using the built in Azure AI Search mapper.
        Response<SearchResults<TRecord>> results = await this.RunOperationAsync(OperationName, () => this._searchClient.SearchAsync<TRecord>(searchText, searchOptions, cancellationToken)).ConfigureAwait(false);
        var mappedResults = this.MapSearchResultsAsync(results.Value.GetResultsAsync());
        return new VectorSearchResults<TRecord>(mappedResults) { TotalCount = results.Value.TotalCount };
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
        if (this._mapper is not null)
        {
            var jsonObjects = VectorStoreErrorHandler.RunModelConversion(
                DatabaseName,
                this._collectionName,
                OperationName,
                () => records.Select(this._mapper!.MapFromDataToStorageModel));

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
    /// Map the search results from <see cref="SearchResult{JsonObject}"/> to <see cref="VectorSearchResults{TRecord}"/> objects using the configured mapper type.
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
                DatabaseName,
                this._collectionName,
                operationName,
                () => this._options.JsonObjectCustomMapper!.MapFromStorageToDataModel(result.Document, new() { IncludeVectors = includeVectors }));
            yield return new VectorSearchResult<TRecord>(document, result.Score);
        }
    }

    /// <summary>
    /// Map the search results from <see cref="SearchResult{TRecord}"/> to <see cref="VectorSearchResults{TRecord}"/> objects.
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
            innerOptions.SelectedFields.AddRange(this._propertyReader.KeyPropertyJsonNames);
            innerOptions.SelectedFields.AddRange(this._propertyReader.DataPropertyJsonNames);
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
                VectorStoreType = DatabaseName,
                CollectionName = this._collectionName,
                OperationName = operationName
            };
        }
        catch (RequestFailedException ex)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreType = DatabaseName,
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
}
