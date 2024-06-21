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
/// Service for storing and retrieving vector records, that uses Azure AI Search as the underlying storage.
/// </summary>
/// <typeparam name="TRecord">The data model to use for adding, updating and retrieving data from storage.</typeparam>
public sealed class AzureAISearchVectorRecordStore<TRecord> : IVectorRecordStore<string, TRecord>
    where TRecord : class
{
    /// <summary>A set of types that a key on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedKeyTypes =
    [
        typeof(string)
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

    /// <summary>Azure AI Search client that can be used to manage the list of indices in an Azure AI Search Service.</summary>
    private readonly SearchIndexClient _searchIndexClient;

    /// <summary>The name of the key field for the collections that this class is used with.</summary>
    private readonly string _keyPropertyName;

    /// <summary>Azure AI Search clients that can be used to manage data in an Azure AI Search Service index.</summary>
    private readonly ConcurrentDictionary<string, SearchClient> _searchClientsByIndex = new();

    /// <summary>Optional configuration options for this class.</summary>
    private readonly AzureAISearchVectorRecordStoreOptions<TRecord> _options;

    /// <summary>The names of all non vector fields on the current model.</summary>
    private readonly List<string> _nonVectorPropertyNames;

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureAISearchVectorRecordStore{TRecord}"/> class.
    /// </summary>
    /// <param name="searchIndexClient">Azure AI Search client that can be used to manage the list of indices in an Azure AI Search Service.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    /// <exception cref="ArgumentNullException">Thrown when <paramref name="searchIndexClient"/> is null.</exception>
    /// <exception cref="ArgumentException">Thrown when options are misconfigured.</exception>
    public AzureAISearchVectorRecordStore(SearchIndexClient searchIndexClient, AzureAISearchVectorRecordStoreOptions<TRecord>? options = default)
    {
        // Verify.
        Verify.NotNull(searchIndexClient);

        // Assign.
        this._searchIndexClient = searchIndexClient;
        this._options = options ?? new AzureAISearchVectorRecordStoreOptions<TRecord>();

        // Verify custom mapper.
        if (this._options.MapperType == AzureAISearchRecordMapperType.JsonObjectCustomMapper && this._options.JsonObjectCustomMapper is null)
        {
            throw new ArgumentException($"The {nameof(AzureAISearchVectorRecordStoreOptions<TRecord>.JsonObjectCustomMapper)} option needs to be set if a {nameof(AzureAISearchVectorRecordStoreOptions<TRecord>.MapperType)} of {nameof(AzureAISearchRecordMapperType.JsonObjectCustomMapper)} has been chosen.", nameof(options));
        }

        // Enumerate public properties using configuration or attributes.
        (PropertyInfo keyProperty, List<PropertyInfo> dataProperties, List<PropertyInfo> vectorProperties) properties;
        if (this._options.VectorStoreRecordDefinition is not null)
        {
            properties = VectorStoreRecordPropertyReader.FindProperties(typeof(TRecord), this._options.VectorStoreRecordDefinition, supportsMultipleVectors: true);
        }
        else
        {
            properties = VectorStoreRecordPropertyReader.FindProperties(typeof(TRecord), supportsMultipleVectors: true);
        }

        // Validate property types and store for later use.
        VectorStoreRecordPropertyReader.VerifyPropertyTypes([properties.keyProperty], s_supportedKeyTypes, "Key");
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(properties.vectorProperties, s_supportedVectorTypes, "Vector");
        this._keyPropertyName = properties.keyProperty.Name;

        // Build the list of property names from the current model that are either key or data fields.
        this._nonVectorPropertyNames = properties.dataProperties.Concat([properties.keyProperty]).Select(x => x.Name).ToList();
    }

    /// <inheritdoc />
    public Task<TRecord?> GetAsync(string key, GetRecordOptions? options = default, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(key);

        // Create Options.
        var innerOptions = this.ConvertGetDocumentOptions(options);
        var collectionName = this.ChooseCollectionName(options?.CollectionName);

        // Get record.
        var searchClient = this.GetSearchClient(collectionName);
        return this.GetDocumentAndMapToDataModelAsync(searchClient, collectionName, key, innerOptions, cancellationToken);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<string> keys, GetRecordOptions? options = default, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        // Create Options
        var innerOptions = this.ConvertGetDocumentOptions(options);
        var collectionName = this.ChooseCollectionName(options?.CollectionName);

        // Get records in parallel.
        var searchClient = this.GetSearchClient(collectionName);
        var tasks = keys.Select(key => this.GetDocumentAndMapToDataModelAsync(searchClient, collectionName, key, innerOptions, cancellationToken));
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

        // Create options.
        var collectionName = this.ChooseCollectionName(options?.CollectionName);

        // Remove record.
        var searchClient = this.GetSearchClient(collectionName);
        return RunOperationAsync(
            collectionName,
            "DeleteDocuments",
            () => searchClient.DeleteDocumentsAsync(this._keyPropertyName, [key], new IndexDocumentsOptions(), cancellationToken));
    }

    /// <inheritdoc />
    public Task DeleteBatchAsync(IEnumerable<string> keys, DeleteRecordOptions? options = default, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        // Create options.
        var collectionName = this.ChooseCollectionName(options?.CollectionName);

        // Remove records.
        var searchClient = this.GetSearchClient(collectionName);
        return RunOperationAsync(
            collectionName,
            "DeleteDocuments",
            () => searchClient.DeleteDocumentsAsync(this._keyPropertyName, keys, new IndexDocumentsOptions(), cancellationToken));
    }

    /// <inheritdoc />
    public async Task<string> UpsertAsync(TRecord record, UpsertRecordOptions? options = default, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        // Create options.
        var collectionName = this.ChooseCollectionName(options?.CollectionName);
        var innerOptions = new IndexDocumentsOptions { ThrowOnAnyError = true };

        // Upsert record.
        var searchClient = this.GetSearchClient(collectionName);
        var results = await this.MapToStorageModelAndUploadDocumentAsync(searchClient, collectionName, [record], innerOptions, cancellationToken).ConfigureAwait(false);
        return results.Value.Results[0].Key;
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> UpsertBatchAsync(IEnumerable<TRecord> records, UpsertRecordOptions? options = default, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        // Create Options
        var collectionName = this.ChooseCollectionName(options?.CollectionName);
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
    private async Task<TRecord?> GetDocumentAndMapToDataModelAsync(
        SearchClient searchClient,
        string collectionName,
        string key,
        GetDocumentOptions innerOptions,
        CancellationToken cancellationToken)
    {
        // Use the user provided mapper.
        if (this._options.MapperType == AzureAISearchRecordMapperType.JsonObjectCustomMapper)
        {
            var jsonObject = await RunOperationAsync(
                collectionName,
                "GetDocument",
                () => GetDocumentWithNotFoundHandlingAsync<JsonObject>(searchClient, key, innerOptions, cancellationToken)).ConfigureAwait(false);

            if (jsonObject is null)
            {
                return null;
            }

            return RunModelConversion(
                collectionName,
                "GetDocument",
                () => this._options.JsonObjectCustomMapper!.MapFromStorageToDataModel(jsonObject));
        }

        // Use the built in Azure AI Search mapper.
        return await RunOperationAsync(
            collectionName,
            "GetDocument",
            () => GetDocumentWithNotFoundHandlingAsync<TRecord>(searchClient, key, innerOptions, cancellationToken)).ConfigureAwait(false);
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
        IEnumerable<TRecord> records,
        IndexDocumentsOptions innerOptions,
        CancellationToken cancellationToken)
    {
        // Use the user provided mapper.
        if (this._options.MapperType == AzureAISearchRecordMapperType.JsonObjectCustomMapper)
        {
            var jsonObjects = RunModelConversion(
                collectionName,
                "UploadDocuments",
                () => records.Select(this._options.JsonObjectCustomMapper!.MapFromDataToStorageModel));

            return RunOperationAsync(
                collectionName,
                "UploadDocuments",
                () => searchClient.UploadDocumentsAsync<JsonObject>(jsonObjects, innerOptions, cancellationToken));
        }

        // Use the built in Azure AI Search mapper.
        return RunOperationAsync(
            collectionName,
            "UploadDocuments",
            () => searchClient.UploadDocumentsAsync<TRecord>(records, innerOptions, cancellationToken));
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
    /// Choose the right collection name to use for the operation by using the one provided
    /// as part of the operation options, or the default one provided at construction time.
    /// </summary>
    /// <param name="operationCollectionName">The collection name provided on the operation options.</param>
    /// <returns>The collection name to use.</returns>
    private string ChooseCollectionName(string? operationCollectionName)
    {
        var collectionName = operationCollectionName ?? this._options.DefaultCollectionName;
        if (collectionName is null)
        {
#pragma warning disable CA2208 // Instantiate argument exceptions correctly
            throw new ArgumentException("Collection name must be provided in the operation options, since no default was provided at construction time.", "options");
#pragma warning restore CA2208 // Instantiate argument exceptions correctly
        }

        return collectionName;
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
    /// Get a document with the given key, and return null if it is not found.
    /// </summary>
    /// <typeparam name="T">The type to deserialize the document to.</typeparam>
    /// <param name="searchClient">The search client to use when fetching the document.</param>
    /// <param name="key">The key of the record to get.</param>
    /// <param name="innerOptions">The azure ai search sdk options for getting a document.</param>
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
    /// <param name="collectionName">The name of the collection the operation is being run on.</param>
    /// <param name="operationName">The type of database operation being run.</param>
    /// <param name="operation">The operation to run.</param>
    /// <returns>The result of the operation.</returns>
    private static async Task<T> RunOperationAsync<T>(string collectionName, string operationName, Func<Task<T>> operation)
    {
        try
        {
            return await operation.Invoke().ConfigureAwait(false);
        }
        catch (AggregateException ex) when (ex.InnerException is RequestFailedException innerEx)
        {
            var wrapperException = new VectorStoreOperationException("Call to vector store failed.", ex);

            // Using Open Telemetry standard for naming of these entries.
            // https://opentelemetry.io/docs/specs/semconv/attributes-registry/db/
            wrapperException.Data.Add("db.system", "AzureAISearch");
            wrapperException.Data.Add("db.collection.name", collectionName);
            wrapperException.Data.Add("db.operation.name", operationName);

            throw wrapperException;
        }
        catch (RequestFailedException ex)
        {
            var wrapperException = new VectorStoreOperationException("Call to vector store failed.", ex);

            // Using Open Telemetry standard for naming of these entries.
            // https://opentelemetry.io/docs/specs/semconv/attributes-registry/db/
            wrapperException.Data.Add("db.system", "AzureAISearch");
            wrapperException.Data.Add("db.collection.name", collectionName);
            wrapperException.Data.Add("db.operation.name", operationName);

            throw wrapperException;
        }
    }

    /// <summary>
    /// Run the given model conversion and wrap any exceptions with <see cref="VectorStoreRecordMappingException"/>.
    /// </summary>
    /// <typeparam name="T">The response type of the operation.</typeparam>
    /// <param name="collectionName">The name of the collection the operation is being run on.</param>
    /// <param name="operationName">The type of database operation being run.</param>
    /// <param name="operation">The operation to run.</param>
    /// <returns>The result of the operation.</returns>
    private static T RunModelConversion<T>(string collectionName, string operationName, Func<T> operation)
    {
        try
        {
            return operation.Invoke();
        }
        catch (Exception ex)
        {
            var wrapperException = new VectorStoreRecordMappingException("Failed to convert vector store record.", ex);

            // Using Open Telemetry standard for naming of these entries.
            // https://opentelemetry.io/docs/specs/semconv/attributes-registry/db/
            wrapperException.Data.Add("db.system", "AzureAISearch");
            wrapperException.Data.Add("db.collection.name", collectionName);
            wrapperException.Data.Add("db.operation.name", operationName);

            throw wrapperException;
        }
    }
}
