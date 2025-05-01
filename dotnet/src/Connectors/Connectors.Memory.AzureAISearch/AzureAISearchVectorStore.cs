// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Azure.Search.Documents.Indexes;
using Microsoft.Extensions.VectorData;
using static Microsoft.Extensions.VectorData.VectorStoreErrorHandler;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

/// <summary>
/// Class for accessing the list of collections in a Azure AI Search vector store.
/// </summary>
/// <remarks>
/// This class can be used with collections of any schema type, but requires you to provide schema information when getting a collection.
/// </remarks>
public sealed class AzureAISearchVectorStore : IVectorStore
{
    /// <summary>Metadata about vector store.</summary>
    private readonly VectorStoreMetadata _metadata;

    /// <summary>Azure AI Search client that can be used to manage the list of indices in an Azure AI Search Service.</summary>
    private readonly SearchIndexClient _searchIndexClient;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly AzureAISearchVectorStoreOptions _options;

    /// <summary>A general purpose definition that can be used to construct a collection when needing to proxy schema agnostic operations.</summary>
    private static readonly VectorStoreRecordDefinition s_generalPurposeDefinition = new() { Properties = [new VectorStoreKeyProperty("Key", typeof(string))] };

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureAISearchVectorStore"/> class.
    /// </summary>
    /// <param name="searchIndexClient">Azure AI Search client that can be used to manage the list of indices in an Azure AI Search Service.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public AzureAISearchVectorStore(SearchIndexClient searchIndexClient, AzureAISearchVectorStoreOptions? options = default)
    {
        Verify.NotNull(searchIndexClient);

        this._searchIndexClient = searchIndexClient;
        this._options = options ?? new AzureAISearchVectorStoreOptions();

        this._metadata = new()
        {
            VectorStoreSystemName = AzureAISearchConstants.VectorStoreSystemName,
            VectorStoreName = searchIndexClient.ServiceName
        };
    }

    /// <inheritdoc />
    public IVectorStoreCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
        where TKey : notnull
        where TRecord : notnull
        => new AzureAISearchVectorStoreRecordCollection<TKey, TRecord>(
            this._searchIndexClient,
            name,
            new AzureAISearchVectorStoreRecordCollectionOptions<TRecord>()
            {
                JsonSerializerOptions = this._options.JsonSerializerOptions,
                VectorStoreRecordDefinition = vectorStoreRecordDefinition,
                EmbeddingGenerator = this._options.EmbeddingGenerator
            });

    /// <inheritdoc />
    public async IAsyncEnumerable<string> ListCollectionNamesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        const string OperationName = "GetIndexNames";

        var indexNamesEnumerable = this._searchIndexClient.GetIndexNamesAsync(cancellationToken).ConfigureAwait(false);
        var errorHandlingEnumerable = new ConfiguredCancelableErrorHandlingAsyncEnumerable<string, RequestFailedException>(indexNamesEnumerable, this._metadata, OperationName);

#pragma warning disable CA2007 // Consider calling ConfigureAwait on the awaited task: False Positive
        await foreach (var item in errorHandlingEnumerable.ConfigureAwait(false))
#pragma warning restore CA2007 // Consider calling ConfigureAwait on the awaited task
        {
            yield return item;
        }
    }

    /// <inheritdoc />
    public Task<bool> CollectionExistsAsync(string name, CancellationToken cancellationToken = default)
    {
        var collection = this.GetCollection<object, Dictionary<string, object>>(name, s_generalPurposeDefinition);
        return collection.CollectionExistsAsync(cancellationToken);
    }

    /// <inheritdoc />
    public Task DeleteCollectionAsync(string name, CancellationToken cancellationToken = default)
    {
        var collection = this.GetCollection<object, Dictionary<string, object>>(name, s_generalPurposeDefinition);
        return collection.DeleteCollectionAsync(cancellationToken);
    }

    /// <inheritdoc />
    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreMetadata) ? this._metadata :
            serviceType == typeof(SearchIndexClient) ? this._searchIndexClient :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }
}
