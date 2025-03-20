// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Azure.Search.Documents.Indexes;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

#pragma warning disable SKEXP0020 // VectorStoreMetadata is experimental

/// <summary>
/// Class for accessing the list of collections in a Azure AI Search vector store.
/// </summary>
/// <remarks>
/// This class can be used with collections of any schema type, but requires you to provide schema information when getting a collection.
/// </remarks>
public class AzureAISearchVectorStore : IVectorStore
{
    /// <summary>Metadata about vector store.</summary>
    private readonly VectorStoreMetadata _metadata;

    /// <summary>Azure AI Search client that can be used to manage the list of indices in an Azure AI Search Service.</summary>
    private readonly SearchIndexClient _searchIndexClient;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly AzureAISearchVectorStoreOptions _options;

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
            VectorStoreSystemName = "azure.aisearch",
            DatabaseName = searchIndexClient.ServiceName
        };
    }

    /// <inheritdoc />
    public virtual IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
        where TKey : notnull
    {
#pragma warning disable CS0618 // IAzureAISearchVectorStoreRecordCollectionFactor is obsolete
        if (this._options.VectorStoreCollectionFactory is not null)
        {
            return this._options.VectorStoreCollectionFactory.CreateVectorStoreRecordCollection<TKey, TRecord>(this._searchIndexClient, name, vectorStoreRecordDefinition);
        }
#pragma warning restore CS0618

        if (typeof(TKey) != typeof(string))
        {
            throw new NotSupportedException("Only string keys are supported.");
        }

        var recordCollection = new AzureAISearchVectorStoreRecordCollection<TRecord>(
            this._searchIndexClient,
            name,
            new AzureAISearchVectorStoreRecordCollectionOptions<TRecord>()
            {
                JsonSerializerOptions = this._options.JsonSerializerOptions,
                VectorStoreRecordDefinition = vectorStoreRecordDefinition
            }) as IVectorStoreRecordCollection<TKey, TRecord>;

        return recordCollection!;
    }

    /// <inheritdoc />
    public virtual async IAsyncEnumerable<string> ListCollectionNamesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var indexNamesEnumerable = this._searchIndexClient.GetIndexNamesAsync(cancellationToken).ConfigureAwait(false);
        var indexNamesEnumerator = indexNamesEnumerable.GetAsyncEnumerator();

        var nextResult = await GetNextIndexNameAsync(indexNamesEnumerator, this._metadata.VectorStoreSystemName).ConfigureAwait(false);
        while (nextResult.more)
        {
            yield return nextResult.name;
            nextResult = await GetNextIndexNameAsync(indexNamesEnumerator, this._metadata.VectorStoreSystemName).ConfigureAwait(false);
        }
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

    /// <summary>
    /// Helper method to get the next index name from the enumerator with a try catch around the move next call to convert
    /// any <see cref="RequestFailedException"/> to <see cref="HttpOperationException"/>, since try catch is not supported
    /// around a yield return.
    /// </summary>
    /// <param name="enumerator">The enumerator to get the next result from.</param>
    /// <param name="vectorStoreSystemName">The vector store system name.</param>
    /// <returns>A value indicating whether there are more results and the current string if true.</returns>
    private static async Task<(string name, bool more)> GetNextIndexNameAsync(
        ConfiguredCancelableAsyncEnumerable<string>.Enumerator enumerator,
        string? vectorStoreSystemName)
    {
        const string OperationName = "GetIndexNames";

        try
        {
            var more = await enumerator.MoveNextAsync();
            return (enumerator.Current, more);
        }
        catch (AggregateException ex) when (ex.InnerException is RequestFailedException innerEx)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreType = vectorStoreSystemName,
                OperationName = OperationName
            };
        }
        catch (RequestFailedException ex)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreType = vectorStoreSystemName,
                OperationName = OperationName
            };
        }
    }
}
