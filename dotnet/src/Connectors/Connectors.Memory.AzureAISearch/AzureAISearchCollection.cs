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
using Azure;
using Azure.Search.Documents;
using Azure.Search.Documents.Indexes;
using Azure.Search.Documents.Indexes.Models;
using Azure.Search.Documents.Models;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using MEAI = Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

/// <summary>
/// Service for storing and retrieving vector records, that uses Azure AI Search as the underlying storage.
/// </summary>
/// <typeparam name="TKey">The data type of the record key. Must be <see cref="string"/>.</typeparam>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public class AzureAISearchCollection<TKey, TRecord> : VectorStoreCollection<TKey, TRecord>, IKeywordHybridSearchable<TRecord>
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

    /// <summary>Azure AI Search client that can be used to manage the list of indices in an Azure AI Search Service.</summary>
    private readonly SearchIndexClient _searchIndexClient;

    /// <summary>Azure AI Search client that can be used to manage data in an Azure AI Search Service index.</summary>
    private readonly SearchClient _searchClient;

    /// <summary>A mapper to use for converting between the data model and the Azure AI Search record.</summary>
    private readonly IAzureAISearchMapper<TRecord> _mappper;

    /// <summary>The model for this collection.</summary>
    private readonly CollectionModel _model;

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureAISearchCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="searchIndexClient">Azure AI Search client that can be used to manage the list of indices in an Azure AI Search Service.</param>
    /// <param name="name">The name of the collection that this <see cref="AzureAISearchCollection{TKey, TRecord}"/> will access.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    /// <exception cref="ArgumentNullException">Thrown when <paramref name="searchIndexClient"/> is null.</exception>
    /// <exception cref="ArgumentException">Thrown when options are misconfigured.</exception>
    [RequiresUnreferencedCode("The Azure AI Search provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The Azure AI Search provider is currently incompatible with NativeAOT.")]
    public AzureAISearchCollection(SearchIndexClient searchIndexClient, string name, AzureAISearchCollectionOptions? options = default)
        : this(
            searchIndexClient,
            name,
            static options => typeof(TRecord) == typeof(Dictionary<string, object?>)
                ? throw new NotSupportedException(VectorDataStrings.NonDynamicCollectionWithDictionaryNotSupported(typeof(AzureAISearchDynamicCollection)))
                : new AzureAISearchModelBuilder()
                    .Build(typeof(TRecord), options.Definition, options.EmbeddingGenerator, options.JsonSerializerOptions ?? JsonSerializerOptions.Default),
            options)
    {
    }

    internal AzureAISearchCollection(SearchIndexClient searchIndexClient, string name, Func<AzureAISearchCollectionOptions, CollectionModel> modelFactory, AzureAISearchCollectionOptions? options)
    {
        // Verify.
        Verify.NotNull(searchIndexClient);
        Verify.NotNullOrWhiteSpace(name);

        if (typeof(TKey) != typeof(string) && typeof(TKey) != typeof(object))
        {
            throw new NotSupportedException("Only string keys are supported.");
        }

        options ??= AzureAISearchCollectionOptions.Default;

        // Assign.
        this.Name = name;
        this._model = modelFactory(options);
        this._searchIndexClient = searchIndexClient;
        this._searchClient = this._searchIndexClient.GetSearchClient(name);

        this._mappper = typeof(TRecord) == typeof(Dictionary<string, object?>) ?
            (IAzureAISearchMapper<TRecord>)(object)new AzureAISearchDynamicMapper(this._model, options.JsonSerializerOptions) :
            new AzureAISearchMapper<TRecord>(this._model, options.JsonSerializerOptions);

        this._collectionMetadata = new()
        {
            VectorStoreSystemName = AzureAISearchConstants.VectorStoreSystemName,
            VectorStoreName = searchIndexClient.ServiceName,
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
            await this._searchIndexClient.GetIndexAsync(this.Name, cancellationToken).ConfigureAwait(false);
            return true;
        }
        catch (RequestFailedException ex) when (ex.Status == 404)
        {
            return false;
        }
        catch (RequestFailedException ex)
        {
            throw new VectorStoreException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = AzureAISearchConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this.Name,
                OperationName = "GetIndex"
            };
        }
    }

    /// <inheritdoc />
    public override async Task EnsureCollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "CreateIndex";

        // Don't even try to create if the collection already exists.
        if (await this.CollectionExistsAsync(cancellationToken).ConfigureAwait(false))
        {
            return;
        }

        var vectorSearchConfig = new VectorSearch();
        var searchFields = new List<SearchField>();

        // Loop through all properties and create the search fields.
        foreach (var property in this._model.Properties)
        {
            switch (property)
            {
                case KeyPropertyModel p:
                    searchFields.Add(AzureAISearchCollectionCreateMapping.MapKeyField(p));
                    break;

                case DataPropertyModel p:
                    searchFields.Add(AzureAISearchCollectionCreateMapping.MapDataField(p));
                    break;

                case VectorPropertyModel p:
                    (VectorSearchField vectorSearchField, VectorSearchAlgorithmConfiguration algorithmConfiguration, VectorSearchProfile vectorSearchProfile) = AzureAISearchCollectionCreateMapping.MapVectorField(p);

                    // Add the search field, plus its profile and algorithm configuration to the search config.
                    searchFields.Add(vectorSearchField);
                    vectorSearchConfig.Algorithms.Add(algorithmConfiguration);
                    vectorSearchConfig.Profiles.Add(vectorSearchProfile);
                    break;

                default:
                    throw new UnreachableException();
            }
        }

        // Create the index definition.
        var searchIndex = new SearchIndex(this.Name, searchFields);
        searchIndex.VectorSearch = vectorSearchConfig;

        try
        {
            await this._searchIndexClient.CreateIndexAsync(searchIndex, cancellationToken).ConfigureAwait(false);
        }
        catch (RequestFailedException ex) when (ex.ErrorCode == "ResourceNameAlreadyInUse")
        {
            // Index already exists, ignore.
        }
        catch (RequestFailedException ex)
        {
            throw new VectorStoreException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = AzureAISearchConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this.Name,
                OperationName = OperationName
            };
        }
        catch (AggregateException ex) when (ex.InnerException is RequestFailedException innerEx)
        {
            throw new VectorStoreException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = AzureAISearchConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this.Name,
                OperationName = OperationName
            };
        }
    }

    /// <inheritdoc />
    public override Task EnsureCollectionDeletedAsync(CancellationToken cancellationToken = default)
    {
        return this.RunOperationAsync<Response>(
            "DeleteIndex",
            async () =>
            {
                try
                {
                    return await this._searchIndexClient.DeleteIndexAsync(this.Name, cancellationToken).ConfigureAwait(false);
                }
                catch (RequestFailedException ex) when (ex.Status == 404)
                {
                    return null!;
                }
            });
    }

    /// <inheritdoc />
    public override Task<TRecord?> GetAsync(TKey key, RecordRetrievalOptions? options = default, CancellationToken cancellationToken = default)
    {
        // Create Options.
        var innerOptions = this.ConvertGetDocumentOptions(options);
        var includeVectors = options?.IncludeVectors ?? false;
        if (includeVectors && this._model.EmbeddingGenerationRequired)
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        // Get record.
        return this.GetDocumentAndMapToDataModelAsync(key, includeVectors, innerOptions, cancellationToken);
    }

    /// <inheritdoc />
    public override async IAsyncEnumerable<TRecord> GetAsync(IEnumerable<TKey> keys, RecordRetrievalOptions? options = default, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        // Create Options
        var innerOptions = this.ConvertGetDocumentOptions(options);
        var includeVectors = options?.IncludeVectors ?? false;
        if (includeVectors && this._model.EmbeddingGenerationRequired)
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        foreach (var key in keys)
        {
            var record = await this.GetDocumentAndMapToDataModelAsync(key, includeVectors, innerOptions, cancellationToken).ConfigureAwait(false);

            if (record is not null)
            {
                yield return record;
            }
        }
    }

    /// <inheritdoc />
    public override Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        var stringKey = this.GetStringKey(key);

        // Remove record.
        return this.RunOperationAsync(
            "DeleteDocuments",
            () => this._searchClient.DeleteDocumentsAsync(this._model.KeyProperty.StorageName, [stringKey], new IndexDocumentsOptions(), cancellationToken));
    }

    /// <inheritdoc />
    public override Task DeleteAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
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
    public override async Task UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        // Create options.
        var innerOptions = new IndexDocumentsOptions { ThrowOnAnyError = true };

        // Upsert record.
        await this.MapToStorageModelAndUploadDocumentAsync([record], innerOptions, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public override async Task UpsertAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);
        if (!records.Any())
        {
            return;
        }

        // Create Options
        var innerOptions = new IndexDocumentsOptions { ThrowOnAnyError = true };

        // Upsert records
        await this.MapToStorageModelAndUploadDocumentAsync(records, innerOptions, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public override IAsyncEnumerable<TRecord> GetAsync(Expression<Func<TRecord, bool>> filter, int top,
        FilteredRecordRetrievalOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(filter);
        Verify.NotLessThan(top, 1);

        options ??= new();

        var includeVectors = options.IncludeVectors;
        if (includeVectors && this._model.EmbeddingGenerationRequired)
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

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

        if (options.OrderBy is not null)
        {
            foreach (var pair in options.OrderBy(new()).Values)
            {
                PropertyModel property = this._model.GetDataOrKeyProperty(pair.PropertySelector);
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
        }

        return this.SearchAndMapToDataModelAsync(null, searchOptions, options.IncludeVectors, cancellationToken)
            .SelectAsync(result => result.Record, cancellationToken);
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
        var vectorProperty = this._model.GetVectorPropertyOrSingle(options);
        var floatVector = await GetSearchVectorAsync(searchValue, vectorProperty, cancellationToken).ConfigureAwait(false);

        var searchOptions = BuildSearchOptions(
            this._model,
            options,
            top,
            floatVector is null
                ? new VectorizableTextQuery((string)(object)searchValue) { KNearestNeighborsCount = top, Fields = { vectorProperty.StorageName } }
                : new VectorizedQuery(floatVector.Value) { KNearestNeighborsCount = top, Fields = { vectorProperty.StorageName } });

        await foreach (var record in this.SearchAndMapToDataModelAsync(null, searchOptions, options.IncludeVectors, cancellationToken).ConfigureAwait(false))
        {
            yield return record;
        }
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
        Verify.NotNull(keywords);
        Verify.NotLessThan(top, 1);

        // Resolve options.
        options ??= s_defaultKeywordVectorizedHybridSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle<TRecord>(new() { VectorProperty = options.VectorProperty });
        var floatVector = await GetSearchVectorAsync(searchValue, vectorProperty, cancellationToken).ConfigureAwait(false);

        var textDataProperty = this._model.GetFullTextDataPropertyOrSingle(options.AdditionalProperty);

        // Build search options.
        var searchOptions = BuildSearchOptions(
            this._model,
            new()
            {
#pragma warning disable CS0618 // Type or member is obsolete
                OldFilter = options.OldFilter,
#pragma warning restore CS0618 // Type or member is obsolete
                Filter = options.Filter,
                VectorProperty = options.VectorProperty,
                Skip = options.Skip,
            },
            top,
            floatVector is null
                ? new VectorizableTextQuery((string)(object)searchValue) { KNearestNeighborsCount = top, Fields = { vectorProperty.StorageName } }
                : new VectorizedQuery(floatVector.Value) { KNearestNeighborsCount = top, Fields = { vectorProperty.StorageName } });

        searchOptions.SearchFields.Add(textDataProperty.StorageName);
        var keywordsCombined = string.Join(" ", keywords);

        await foreach (var record in this.SearchAndMapToDataModelAsync(keywordsCombined, searchOptions, options.IncludeVectors, cancellationToken).ConfigureAwait(false))
        {
            yield return record;
        }
    }

    private static async ValueTask<ReadOnlyMemory<float>?> GetSearchVectorAsync<TInput>(TInput searchValue, VectorPropertyModel vectorProperty, CancellationToken cancellationToken)
        where TInput : notnull
        => searchValue switch
        {
            ReadOnlyMemory<float> r => r,
            float[] f => new ReadOnlyMemory<float>(f),
            Embedding<float> e => e.Vector,
            _ when vectorProperty.EmbeddingGenerator is IEmbeddingGenerator<TInput, Embedding<float>> generator
                => await generator.GenerateVectorAsync(searchValue, cancellationToken: cancellationToken).ConfigureAwait(false),

            // A string was passed without an embedding generator being configured; send the string to Azure AI Search for backend embedding generation.
            string when vectorProperty.EmbeddingGenerator is null => (ReadOnlyMemory<float>?)null,

            _ => vectorProperty.EmbeddingGenerator is null
                ? throw new NotSupportedException(VectorDataStrings.InvalidSearchInputAndNoEmbeddingGeneratorWasConfigured(searchValue.GetType(), AzureAISearchModelBuilder.SupportedVectorTypes))
                : throw new InvalidOperationException(VectorDataStrings.IncompatibleEmbeddingGeneratorWasConfiguredForInputType(typeof(TInput), vectorProperty.EmbeddingGenerator.GetType()))
        };

    #endregion Search

    /// <inheritdoc />
    public override object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreCollectionMetadata) ? this._collectionMetadata :
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

        var jsonObject = await this.RunOperationAsync(
            OperationName,
            () => this.GetDocumentWithNotFoundHandlingAsync<JsonObject>(this._searchClient, stringKey, innerOptions, cancellationToken)).ConfigureAwait(false);

        if (jsonObject is null)
        {
            return default;
        }

        return (TRecord)(object)this._mappper!.MapFromStorageToDataModel(jsonObject, includeVectors);
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

        var jsonObjectResults = await this.RunOperationAsync(
            OperationName,
            () => this._searchClient.SearchAsync<JsonObject>(searchText, searchOptions, cancellationToken)).ConfigureAwait(false);

        await foreach (var result in this.MapSearchResultsAsync(jsonObjectResults.Value.GetResultsAsync(), OperationName, includeVectors).ConfigureAwait(false))
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
    private async Task<Response<IndexDocumentsResult>> MapToStorageModelAndUploadDocumentAsync(
        IEnumerable<TRecord> records,
        IndexDocumentsOptions innerOptions,
        CancellationToken cancellationToken)
    {
        const string OperationName = "UploadDocuments";

        (records, var generatedEmbeddings) = await ProcessEmbeddingsAsync(this._model, records, cancellationToken).ConfigureAwait(false);

        var jsonObjects = records.Select((r, i) => this._mappper!.MapFromDataToStorageModel(r, i, generatedEmbeddings));

        return await this.RunOperationAsync(
            OperationName,
            () => this._searchClient.UploadDocumentsAsync<JsonObject>(jsonObjects, innerOptions, cancellationToken)).ConfigureAwait(false);
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
            var document = (TRecord)(object)this._mappper!.MapFromStorageToDataModel(result.Document, includeVectors);
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
    /// Convert the public <see cref="RecordRetrievalOptions"/> options model to the Azure AI Search <see cref="GetDocumentOptions"/> options model.
    /// </summary>
    /// <param name="options">The public options model.</param>
    /// <returns>The Azure AI Search options model.</returns>
    private GetDocumentOptions ConvertGetDocumentOptions(RecordRetrievalOptions? options)
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
    /// Build the search options for a vector search, where the type of vector search can be provided as input.
    /// E.g. VectorizedQuery or VectorizableTextQuery.
    /// </summary>
    private static SearchOptions BuildSearchOptions(CollectionModel model, VectorSearchOptions<TRecord> options, int top, VectorQuery? vectorQuery)
    {
        if (model.VectorProperties.Count == 0)
        {
            throw new InvalidOperationException("The collection does not have any vector fields, so vector search is not possible.");
        }

        if (options.IncludeVectors && model.EmbeddingGenerationRequired)
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
        // Build filter object.
        var filter = options switch
        {
            { OldFilter: not null, Filter: not null } => throw new ArgumentException("Either Filter or OldFilter can be specified, but not both"),
            { OldFilter: VectorSearchFilter legacyFilter } => AzureAISearchCollectionSearchMapping.BuildLegacyFilterString(legacyFilter, model),
            { Filter: Expression<Func<TRecord, bool>> newFilter } => new AzureAISearchFilterTranslator().Translate(newFilter, model),
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

        searchOptions.VectorSearch.Queries.Add(vectorQuery);

        // Filter out vector fields if requested.
        if (!options.IncludeVectors)
        {
            searchOptions.Select.Add(model.KeyProperty.StorageName);

            foreach (var dataProperty in model.DataProperties)
            {
                searchOptions.Select.Add(dataProperty.StorageName);
            }
        }

        return searchOptions;
    }

    private static async ValueTask<(IEnumerable<TRecord> records, IReadOnlyList<MEAI.Embedding>?[]?)> ProcessEmbeddingsAsync(
        CollectionModel model,
        IEnumerable<TRecord> records,
        CancellationToken cancellationToken)
    {
        IReadOnlyList<TRecord>? recordsList = null;

        // If an embedding generator is defined, invoke it once per property for all records.
        IReadOnlyList<MEAI.Embedding>?[]? generatedEmbeddings = null;

        var vectorPropertyCount = model.VectorProperties.Count;
        for (var i = 0; i < vectorPropertyCount; i++)
        {
            var vectorProperty = model.VectorProperties[i];

            if (AzureAISearchModelBuilder.IsVectorPropertyTypeValidCore(vectorProperty.Type, out _))
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
                    return (records, null);
                }

                records = recordsList;
            }

            // TODO: Ideally we'd group together vector properties using the same generator (and with the same input and output properties),
            // and generate embeddings for them in a single batch. That's some more complexity though.
            if (vectorProperty.TryGenerateEmbeddings<TRecord, Embedding<float>>(records, cancellationToken, out var floatTask))
            {
                generatedEmbeddings ??= new IReadOnlyList<MEAI.Embedding>?[vectorPropertyCount];
                generatedEmbeddings[i] = await floatTask.ConfigureAwait(false);
            }
            else
            {
                throw new InvalidOperationException(
                    $"The embedding generator configured on property '{vectorProperty.ModelName}' cannot produce an embedding of type '{typeof(Embedding<float>).Name}' for the given input type.");
            }
        }

        return (records, generatedEmbeddings);
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
    private async Task<T?> GetDocumentWithNotFoundHandlingAsync<T>(
        SearchClient searchClient,
        string key,
        GetDocumentOptions innerOptions,
        CancellationToken cancellationToken)
    {
        const string OperationName = "GetDocument";

        try
        {
            return await searchClient.GetDocumentAsync<T>(key, innerOptions, cancellationToken).ConfigureAwait(false);
        }
        catch (RequestFailedException ex) when (ex.Status == 404)
        {
            return default;
        }
        catch (AggregateException ex) when (ex.InnerException is RequestFailedException innerEx)
        {
            throw new VectorStoreException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = AzureAISearchConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this.Name,
                OperationName = OperationName
            };
        }
        catch (RequestFailedException ex)
        {
            throw new VectorStoreException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = AzureAISearchConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this.Name,
                OperationName = OperationName
            };
        }
    }

    /// <summary>
    /// Run the given operation and wrap any <see cref="RequestFailedException"/> with <see cref="VectorStoreException"/>."/>
    /// </summary>
    /// <typeparam name="T">The response type of the operation.</typeparam>
    /// <param name="operationName">The type of database operation being run.</param>
    /// <param name="operation">The operation to run.</param>
    /// <returns>The result of the operation.</returns>
    private Task<T> RunOperationAsync<T>(string operationName, Func<Task<T>> operation) =>
        VectorStoreErrorHandler.RunOperationAsync<T, RequestFailedException>(
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
