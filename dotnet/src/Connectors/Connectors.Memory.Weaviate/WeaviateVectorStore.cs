// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

#pragma warning disable SKEXP0020 // VectorStoreMetadata is experimental

/// <summary>
/// Class for accessing the list of collections in a Weaviate vector store.
/// </summary>
/// <remarks>
/// This class can be used with collections of any schema type, but requires you to provide schema information when getting a collection.
/// </remarks>
public class WeaviateVectorStore : IVectorStore
{
    /// <summary>Metadata about vector store.</summary>
    private readonly VectorStoreMetadata _metadata;

    /// <summary><see cref="HttpClient"/> that is used to interact with Weaviate API.</summary>
    private readonly HttpClient _httpClient;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly WeaviateVectorStoreOptions _options;

    /// <summary>
    /// Initializes a new instance of the <see cref="WeaviateVectorStore"/> class.
    /// </summary>
    /// <param name="httpClient">
    /// <see cref="HttpClient"/> that is used to interact with Weaviate API.
    /// <see cref="HttpClient.BaseAddress"/> should point to remote or local cluster and API key can be configured via <see cref="HttpClient.DefaultRequestHeaders"/>.
    /// It's also possible to provide these parameters via <see cref="WeaviateVectorStoreOptions"/>.
    /// </param>
    /// <param name="options">Optional configuration options for this class.</param>
    public WeaviateVectorStore(HttpClient httpClient, WeaviateVectorStoreOptions? options = null)
    {
        Verify.NotNull(httpClient);

        this._httpClient = httpClient;
        this._options = options ?? new();

        this._metadata = new()
        {
            VectorStoreSystemName = "weaviate"
        };
    }

    /// <inheritdoc />
    /// <remarks>The collection name must start with a capital letter and contain only ASCII letters and digits.</remarks>
    public virtual IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
        where TKey : notnull
    {
#pragma warning disable CS0618 // IWeaviateVectorStoreRecordCollectionFactory is obsolete
        if (this._options.VectorStoreCollectionFactory is not null)
        {
            return this._options.VectorStoreCollectionFactory.CreateVectorStoreRecordCollection<TKey, TRecord>(
                this._httpClient,
                name,
                vectorStoreRecordDefinition);
        }
#pragma warning restore CS0618

        if (typeof(TKey) != typeof(Guid))
        {
            throw new NotSupportedException($"Only {nameof(Guid)} key is supported.");
        }

        var recordCollection = new WeaviateVectorStoreRecordCollection<TRecord>(
            this._httpClient,
            name,
            new()
            {
                VectorStoreRecordDefinition = vectorStoreRecordDefinition,
                Endpoint = this._options.Endpoint,
                ApiKey = this._options.ApiKey
            }) as IVectorStoreRecordCollection<TKey, TRecord>;

        return recordCollection!;
    }

    /// <inheritdoc />
    public virtual async IAsyncEnumerable<string> ListCollectionNamesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using var request = new WeaviateGetCollectionsRequest().Build();
        WeaviateGetCollectionsResponse collectionsResponse;

        try
        {
            var httpResponse = await this._httpClient.SendAsync(request, HttpCompletionOption.ResponseContentRead, cancellationToken).ConfigureAwait(false);
            var httpResponseContent = await httpResponse.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);

            collectionsResponse = JsonSerializer.Deserialize<WeaviateGetCollectionsResponse>(httpResponseContent)!;
        }
        catch (Exception e)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", e)
            {
                VectorStoreType = WeaviateConstants.DatabaseName,
                OperationName = "ListCollectionNames"
            };
        }

        if (collectionsResponse?.Collections is not null)
        {
            foreach (var collection in collectionsResponse.Collections)
            {
                yield return collection.CollectionName;
            }
        }
    }

    /// <inheritdoc />
    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreMetadata) ? this._metadata :
            serviceType == typeof(HttpClient) ? this._httpClient :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }
}
