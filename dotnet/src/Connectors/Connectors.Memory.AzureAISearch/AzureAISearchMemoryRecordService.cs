// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Azure.Search.Documents;
using Azure.Search.Documents.Indexes;
using Azure.Search.Documents.Models;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

/// <summary>
/// Service for storing and retrieving memory records, that uses Azure AI Search as the underlying storage.
/// </summary>
/// <typeparam name="TDataModel">The data model to use for adding, updating and retrieving data from storage.</typeparam>
public sealed class AzureAISearchMemoryRecordService<TDataModel> : IMemoryRecordService<string, TDataModel>
    where TDataModel : class
{
    /// <summary>A set of types that a key on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedKeyTypes =
    [
        typeof(string)
    ];

    /// <summary>A set of types that vectors on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedVectorTypes =
    [
        typeof(ReadOnlyMemory<float>),
        typeof(ReadOnlyMemory<float>?)
    ];

    /// <summary>Azure AI Search client that can be used to manage the list of indices in an Azure AI Search Service.</summary>
    private readonly SearchIndexClient _searchIndexClient;

    /// <summary>The name of the collection to use with this store if none is provided for any individual operation.</summary>
    private readonly string _defaultCollectionName;

    /// <summary>The name of the key field for the collections that this class is used with.</summary>
    private readonly string _keyPropertyName;

    /// <summary>Azure AI Search clients that can be used to manage data in an Azure AI Search Service index.</summary>
    private readonly ConcurrentDictionary<string, SearchClient> _searchClientsByIndex = new();

    /// <summary>Optional configuration options for this class.</summary>
    private readonly AzureAISearchMemoryRecordServiceOptions<TDataModel> _options;

    /// <summary>The names of all non vector fields on the current model.</summary>
    private readonly List<string> _nonVectorPropertyNames;

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureAISearchMemoryRecordService{TDataModel}"/> class.
    /// </summary>
    /// <param name="searchIndexClient">Azure AI Search client that can be used to manage the list of indices in an Azure AI Search Service.</param>
    /// <param name="defaultCollectionName">The name of the collection to use with this store if none is provided for any individual operation.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    /// <exception cref="ArgumentNullException">Thrown when <paramref name="searchIndexClient"/> is null.</exception>
    /// <exception cref="ArgumentException">Thrown when <paramref name="defaultCollectionName"/> is null or whitespace.</exception>
    public AzureAISearchMemoryRecordService(SearchIndexClient searchIndexClient, string defaultCollectionName, AzureAISearchMemoryRecordServiceOptions<TDataModel>? options = default)
    {
        // Verify.
        Verify.NotNull(searchIndexClient);
        Verify.NotNullOrWhiteSpace(defaultCollectionName);

        // Assign.
        this._searchIndexClient = searchIndexClient;
        this._defaultCollectionName = defaultCollectionName;
        this._options = options ?? new AzureAISearchMemoryRecordServiceOptions<TDataModel>();

        // Verify custom mapper.
        if (this._options.MapperType == AzureAISearchMemoryRecordMapperType.JsonObjectCustomMapper && this._options.JsonObjectCustomMapper is null)
        {
            throw new ArgumentException($"The {nameof(AzureAISearchMemoryRecordServiceOptions<TDataModel>.JsonObjectCustomMapper)} option needs to be set if a {nameof(AzureAISearchMemoryRecordServiceOptions<TDataModel>.MapperType)} of {nameof(AzureAISearchMemoryRecordMapperType.JsonObjectCustomMapper)} has been chosen.", nameof(options));
        }

        // Enumerate public properties using configuration or attributes.
        (PropertyInfo keyProperty, List<PropertyInfo> dataProperties, List<PropertyInfo> vectorProperties) properties;
        if (this._options.MemoryRecordDefinition is not null)
        {
            properties = MemoryServiceModelPropertyReader.FindProperties(typeof(TDataModel), this._options.MemoryRecordDefinition, supportsMultipleVectors: true);
        }
        else
        {
            properties = MemoryServiceModelPropertyReader.FindProperties(typeof(TDataModel), supportsMultipleVectors: true);
        }

        // Validate property types and store for later use.
        MemoryServiceModelPropertyReader.VerifyPropertyTypes([properties.keyProperty], s_supportedKeyTypes, "Key");
        MemoryServiceModelPropertyReader.VerifyPropertyTypes(properties.vectorProperties, s_supportedVectorTypes, "Vector");
        this._keyPropertyName = properties.keyProperty.Name;

        // Build the list of property names from the current model that are either key or data fields.
        this._nonVectorPropertyNames = properties.dataProperties.Concat([properties.keyProperty]).Select(x => x.Name).ToList();
    }

    /// <inheritdoc />
    public Task<TDataModel?> GetAsync(string key, GetRecordOptions? options = default, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(key);

        // Create Options.
        var innerOptions = this.ConvertGetDocumentOptions(options);
        var collectionName = options?.CollectionName ?? this._defaultCollectionName;

        // Get record.
        var searchClient = this.GetSearchClient(collectionName);
        return this.GetDocumentAndMapToDataModelAsync(searchClient, collectionName, key, innerOptions, cancellationToken);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TDataModel?> GetBatchAsync(IEnumerable<string> keys, Memory.GetRecordOptions? options = default, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        // Create Options
        var innerOptions = this.ConvertGetDocumentOptions(options);
        var collectionName = options?.CollectionName ?? this._defaultCollectionName;

        // Get records in parallel.
        var searchClient = this.GetSearchClient(collectionName);
        var tasks = keys.Select(key => this.GetDocumentAndMapToDataModelAsync(searchClient, collectionName, key, innerOptions, cancellationToken));
        var results = await Task.WhenAll(tasks).ConfigureAwait(false);
        foreach (var result in results) { yield return result; }
    }

    /// <inheritdoc />
    public Task DeleteAsync(string key, DeleteRecordOptions? options = default, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(key);

        // Create options.
        var collectionName = options?.CollectionName ?? this._defaultCollectionName;

        // Remove record.
        var searchClient = this.GetSearchClient(collectionName);
        return RunOperationAsync(
            () => searchClient.DeleteDocumentsAsync(this._keyPropertyName, [key], new IndexDocumentsOptions(), cancellationToken),
            collectionName,
            "DeleteDocuments");
    }

    /// <inheritdoc />
    public Task DeleteBatchAsync(IEnumerable<string> keys, DeleteRecordOptions? options = default, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        // Create options.
        var collectionName = options?.CollectionName ?? this._defaultCollectionName;

        // Remove records.
        var searchClient = this.GetSearchClient(collectionName);
        return RunOperationAsync(
            () => searchClient.DeleteDocumentsAsync(this._keyPropertyName, keys, new IndexDocumentsOptions(), cancellationToken),
            collectionName,
            "DeleteDocuments");
    }

    /// <inheritdoc />
    public async Task<string> UpsertAsync(TDataModel record, UpsertRecordOptions? options = default, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        // Create options.
        var collectionName = options?.CollectionName ?? this._defaultCollectionName;
        var innerOptions = new IndexDocumentsOptions { ThrowOnAnyError = true };

        // Upsert record.
        var searchClient = this.GetSearchClient(collectionName);
        var results = await this.MapToStorageModelAndUploadDocumentAsync(searchClient, collectionName, [record], innerOptions, cancellationToken).ConfigureAwait(false);
        return results.Value.Results[0].Key;
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> UpsertBatchAsync(IEnumerable<TDataModel> records, UpsertRecordOptions? options = default, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        // Create Options
        var collectionName = options?.CollectionName ?? this._defaultCollectionName;
        var innerOptions = new IndexDocumentsOptions { ThrowOnAnyError = true };

        // Upsert records
        var searchClient = this.GetSearchClient(collectionName);
        var results = await this.MapToStorageModelAndUploadDocumentAsync(searchClient, collectionName, records, innerOptions, cancellationToken).ConfigureAwait(false);

        // Get results
        var resultKeys = results.Value.Results.Select(x => x.Key).ToList();
        foreach (var resultKey in resultKeys) { yield return resultKey; }
    }

    /// <summary>
    /// Get the document with the given key and map it to the data model using the configured mapper type.
    /// </summary>
    /// <param name="searchClient">The search client to use when fetching the document.</param>
    /// <param name="collectionName">The name of the collection to retrieve the record from.</param>
    /// <param name="key">The key of the record to get.</param>
    /// <param name="innerOptions">The azure ai search sdk options for getting a document.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The retrieved document, mapped to the consumer data model.</returns>
    private async Task<TDataModel?> GetDocumentAndMapToDataModelAsync(
        SearchClient searchClient,
        string collectionName,
        string key,
        GetDocumentOptions innerOptions,
        CancellationToken cancellationToken)
    {
        // Use the user provided mapper.
        if (this._options.MapperType == AzureAISearchMemoryRecordMapperType.JsonObjectCustomMapper)
        {
            var jsonObject = await RunOperationAsync(
                () => searchClient.GetDocumentAsync<JsonObject>(key, innerOptions, cancellationToken),
                collectionName,
                "GetDocument").ConfigureAwait(false);

            return RunModelConversion(
                () => this._options.JsonObjectCustomMapper!.MapFromStorageToDataModel(jsonObject),
                collectionName,
                "GetDocument");
        }

        // Use the built in Azure AI Search mapper.
        return await RunOperationAsync(
            () => searchClient.GetDocumentAsync<TDataModel>(key, innerOptions, cancellationToken),
            collectionName,
            "GetDocument").ConfigureAwait(false);
    }

    /// <summary>
    /// Map the data model to the storage model and upload the document.
    /// </summary>
    /// <param name="searchClient">The search client to use when uploading the document.</param>
    /// <param name="collectionName">The name of the collection to upsert the records to.</param>
    /// <param name="records">The records to upload.</param>
    /// <param name="innerOptions">The azure ai search sdk options for uploading a document.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The document upload result.</returns>
    private Task<Response<IndexDocumentsResult>> MapToStorageModelAndUploadDocumentAsync(
        SearchClient searchClient,
        string collectionName,
        IEnumerable<TDataModel> records,
        IndexDocumentsOptions innerOptions,
        CancellationToken cancellationToken)
    {
        // Use the user provided mapper.
        if (this._options.MapperType == AzureAISearchMemoryRecordMapperType.JsonObjectCustomMapper)
        {
            var jsonObjects = RunModelConversion(
                () => records.Select(this._options.JsonObjectCustomMapper!.MapFromDataToStorageModel),
                collectionName,
                "UploadDocuments");

            return RunOperationAsync(
                () => searchClient.UploadDocumentsAsync<JsonObject>(jsonObjects, innerOptions, cancellationToken),
                collectionName,
                "UploadDocuments");
        }

        // Use the built in Azure AI Search mapper.
        return RunOperationAsync(
            () => searchClient.UploadDocumentsAsync<TDataModel>(records, innerOptions, cancellationToken),
            collectionName,
            "UploadDocuments");
    }

    /// <summary>
    /// Get a search client for the index specified.
    /// Note: the index might not exist, but we avoid checking everytime and the extra latency.
    /// </summary>
    /// <param name="indexName">Index name</param>
    /// <returns>Search client ready to read/write</returns>
    private SearchClient GetSearchClient(string indexName)
    {
        // Check the local cache first, if not found create a new one.
        if (!this._searchClientsByIndex.TryGetValue(indexName, out SearchClient? client))
        {
            client = this._searchIndexClient.GetSearchClient(indexName);
            this._searchClientsByIndex[indexName] = client;
        }

        return client;
    }

    /// <summary>
    /// Convert the public <see cref="GetRecordOptions"/> options model to the azure ai search <see cref="GetDocumentOptions"/> options model.
    /// </summary>
    /// <param name="options">The public options model.</param>
    /// <returns>The azure ai search options model.</returns>
    private GetDocumentOptions ConvertGetDocumentOptions(GetRecordOptions? options)
    {
        var innerOptions = new GetDocumentOptions();
        if (options?.IncludeVectors is false)
        {
            innerOptions.SelectedFields.AddRange(this._nonVectorPropertyNames);
        }

        return innerOptions;
    }

    /// <summary>
    /// Run the given operation and wrap any <see cref="RequestFailedException"/> with <see cref="HttpOperationException"/>."/>
    /// </summary>
    /// <typeparam name="T">The response type of the operation.</typeparam>
    /// <param name="operation">The operation to run.</param>
    /// <param name="collectionName">The name of the collection the operation is being run on.</param>
    /// <param name="operationName">The type of database operation being run.</param>
    /// <returns>The result of the operation.</returns>
    private static async Task<T> RunOperationAsync<T>(Func<Task<T>> operation, string collectionName, string operationName)
    {
        try
        {
            return await operation.Invoke().ConfigureAwait(false);
        }
        catch (RequestFailedException ex)
        {
            var wrapperException = new MemoryServiceOperationException("Call to memory service failed.", ex);

            wrapperException.Data.Add("db.system", "AzureAISearch");
            wrapperException.Data.Add("db.collection.name", collectionName);
            wrapperException.Data.Add("db.operation.name", operationName);

            throw wrapperException;
        }
    }

    /// <summary>
    /// Run the given model conversion and wrap any exceptions with <see cref="MemoryModelException"/>.
    /// </summary>
    /// <typeparam name="T">The response type of the operation.</typeparam>
    /// <param name="operation">The operation to run.</param>
    /// <param name="collectionName">The name of the collection the operation is being run on.</param>
    /// <param name="operationName">The type of database operation being run.</param>
    /// <returns>The result of the operation.</returns>
    private static T RunModelConversion<T>(Func<T> operation, string collectionName, string operationName)
    {
        try
        {
            return operation.Invoke();
        }
        catch (Exception ex)
        {
            var wrapperException = new MemoryModelException("Failed to convert memory model.", ex);

            wrapperException.Data.Add("db.system", "AzureAISearch");
            wrapperException.Data.Add("db.collection.name", collectionName);
            wrapperException.Data.Add("db.operation.name", operationName);

            throw wrapperException;
        }
    }
}
