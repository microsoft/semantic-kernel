// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Azure.Core;
using Azure.Search.Documents;
using Azure.Search.Documents.Indexes;
using Azure.Search.Documents.Indexes.Models;
using Azure.Search.Documents.Models;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Memory.AzureCognitiveSearch;

/// <summary>
/// AzureCognitiveSearchMemoryStore is a memory store implementation using Azure Cognitive Search.
/// </summary>
public class AzureCognitiveSearchMemoryStore : IMemoryStore
{
    /// <summary>
    /// Create a new instance of memory storage using Azure Cognitive Search.
    /// </summary>
    /// <param name="endpoint">Azure Cognitive Search URI, e.g. "https://contoso.search.windows.net"</param>
    /// <param name="apiKey">API Key</param>
    public AzureCognitiveSearchMemoryStore(string endpoint, string apiKey)
    {
        AzureKeyCredential credentials = new(apiKey);
        this._adminClient = new SearchIndexClient(new Uri(endpoint), credentials, GetClientOptions());
    }

    /// <summary>
    /// Create a new instance of memory storage using Azure Cognitive Search.
    /// </summary>
    /// <param name="endpoint">Azure Cognitive Search URI, e.g. "https://contoso.search.windows.net"</param>
    /// <param name="credentials">Azure service</param>
    public AzureCognitiveSearchMemoryStore(string endpoint, TokenCredential credentials)
    {
        this._adminClient = new SearchIndexClient(new Uri(endpoint), credentials, GetClientOptions());
    }

    /// <inheritdoc />
    public Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        // Indexes are created when sending a record. The creation requires the size of the embeddings.
        return Task.CompletedTask;
    }

    /// <inheritdoc />
    public IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancellationToken = default)
    {
        return this.GetIndexesAsync(cancellationToken);
    }

    /// <inheritdoc />
    public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        string normalizeIndexName = this.NormalizeIndexName(collectionName);

        return await this.GetIndexesAsync(cancellationToken)
            .AnyAsync(index => string.Equals(index, collectionName, StringComparison.OrdinalIgnoreCase)
                                || string.Equals(index, normalizeIndexName, StringComparison.OrdinalIgnoreCase),
                cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        string normalizeIndexName = this.NormalizeIndexName(collectionName);

        return this._adminClient.DeleteIndexAsync(normalizeIndexName, cancellationToken);
    }

    /// <inheritdoc />
    public Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken = default)
    {
        collectionName = this.NormalizeIndexName(collectionName);
        return this.UpsertRecordAsync(collectionName, AzureCognitiveSearchMemoryRecord.FromMemoryRecord(record), cancellationToken);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        collectionName = this.NormalizeIndexName(collectionName);
        IList<AzureCognitiveSearchMemoryRecord> searchRecords = records.Select(AzureCognitiveSearchMemoryRecord.FromMemoryRecord).ToList();
        List<string> result = await this.UpsertBatchAsync(collectionName, searchRecords, cancellationToken).ConfigureAwait(false);
        foreach (var x in result) { yield return x; }
    }

    /// <inheritdoc />
    public async Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
        collectionName = this.NormalizeIndexName(collectionName);
        var client = this.GetSearchClient(collectionName);
        Response<AzureCognitiveSearchMemoryRecord>? result;
        try
        {
            result = await client
                .GetDocumentAsync<AzureCognitiveSearchMemoryRecord>(AzureCognitiveSearchMemoryRecord.EncodeId(key), cancellationToken: cancellationToken)
                .ConfigureAwait(false);
        }
        catch (RequestFailedException e) when (e.Status == 404)
        {
            // Index not found, no data to return
            return null;
        }

        if (result?.Value == null)
        {
            throw new SKException("Memory read returned null");
        }

        return result.Value.ToMemoryRecord();
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(
        string collectionName,
        IEnumerable<string> keys,
        bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        foreach (var key in keys)
        {
            var record = await this.GetAsync(collectionName, key, withEmbeddings, cancellationToken).ConfigureAwait(false);
            if (record != null) { yield return record; }
        }
    }

    /// <inheritdoc />
    public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(
        string collectionName,
        ReadOnlyMemory<float> embedding,
        double minRelevanceScore = 0,
        bool withEmbedding = false,
        CancellationToken cancellationToken = default)
    {
        return await this.GetNearestMatchesAsync(collectionName, embedding, 1, minRelevanceScore, withEmbedding, cancellationToken)
            .FirstOrDefaultAsync(cancellationToken)
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(
        string collectionName,
        ReadOnlyMemory<float> embedding,
        int limit,
        double minRelevanceScore = 0,
        bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        collectionName = this.NormalizeIndexName(collectionName);

        var client = this.GetSearchClient(collectionName);

        SearchQueryVector vectorQuery = new()
        {
            KNearestNeighborsCount = limit,
            Fields = AzureCognitiveSearchMemoryRecord.EmbeddingField,
            Value = MemoryMarshal.TryGetArray(embedding, out var array) && array.Count == embedding.Length ? array.Array! : embedding.ToArray(),
        };

        SearchOptions options = new() { Vector = vectorQuery };
        Response<SearchResults<AzureCognitiveSearchMemoryRecord>>? searchResult = null;
        try
        {
            searchResult = await client
                .SearchAsync<AzureCognitiveSearchMemoryRecord>(null, options, cancellationToken: cancellationToken)
                .ConfigureAwait(false);
        }
        catch (RequestFailedException e) when (e.Status == 404)
        {
            // Index not found, no data to return
        }

        if (searchResult == null) { yield break; }

        await foreach (SearchResult<AzureCognitiveSearchMemoryRecord>? doc in searchResult.Value.GetResultsAsync())
        {
            if (doc == null || doc.Score < minRelevanceScore) { continue; }

            MemoryRecord memoryRecord = doc.Document.ToMemoryRecord(withEmbeddings);

            yield return (memoryRecord, doc.Score ?? 0);
        }
    }

    /// <inheritdoc />
    public Task RemoveAsync(string collectionName, string key, CancellationToken cancellationToken = default)
    {
        return this.RemoveBatchAsync(collectionName, new[] { key }, cancellationToken);
    }

    /// <inheritdoc />
    public async Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        collectionName = this.NormalizeIndexName(collectionName);

        var records = keys.Select(x => new List<AzureCognitiveSearchMemoryRecord> { new(x) });

        var client = this.GetSearchClient(collectionName);
        try
        {
            await client.DeleteDocumentsAsync(records, cancellationToken: cancellationToken).ConfigureAwait(false);
        }
        catch (RequestFailedException e) when (e.Status == 404)
        {
            // Index not found, no data to delete
        }
    }

    #region private

    /// <summary>
    /// Index names cannot contain special chars. We use this rule to replace a few common ones
    /// with an underscore and reduce the chance of errors. If other special chars are used, we leave it
    /// to the service to throw an error.
    /// Note:
    /// - replacing chars introduces a small chance of conflicts, e.g. "the-user" and "the_user".
    /// - we should consider whether making this optional and leave it to the developer to handle.
    /// </summary>
    private static readonly Regex s_replaceIndexNameSymbolsRegex = new(@"[\s|\\|/|.|_|:]");

    private readonly ConcurrentDictionary<string, SearchClient> _clientsByIndex = new();

    private readonly SearchIndexClient _adminClient;

    /// <summary>
    /// Create a new search index.
    /// </summary>
    /// <param name="indexName">Index name</param>
    /// <param name="embeddingSize">Size of the embedding vector</param>
    /// <param name="cancellationToken">Task cancellation token</param>
    private Task<Response<SearchIndex>> CreateIndexAsync(
        string indexName,
        int embeddingSize,
        CancellationToken cancellationToken = default)
    {
        if (embeddingSize < 1)
        {
            throw new SKException("Invalid embedding size: the value must be greater than zero.");
        }

        var configName = "searchConfig";
        var newIndex = new SearchIndex(indexName)
        {
            Fields = new List<SearchField>
            {
                new SimpleField(AzureCognitiveSearchMemoryRecord.IdField, SearchFieldDataType.String) { IsKey = true },
                new SearchField(AzureCognitiveSearchMemoryRecord.EmbeddingField, SearchFieldDataType.Collection(SearchFieldDataType.Single))
                {
                    IsSearchable = true,
                    VectorSearchDimensions = embeddingSize,
                    VectorSearchConfiguration = configName
                },
                new SearchField(AzureCognitiveSearchMemoryRecord.TextField, SearchFieldDataType.String) { IsFilterable = true, IsFacetable = true },
                new SimpleField(AzureCognitiveSearchMemoryRecord.DescriptionField, SearchFieldDataType.String) { IsFilterable = true, IsFacetable = true },
                new SimpleField(AzureCognitiveSearchMemoryRecord.AdditionalMetadataField, SearchFieldDataType.String) { IsFilterable = true, IsFacetable = true },
                new SimpleField(AzureCognitiveSearchMemoryRecord.ExternalSourceNameField, SearchFieldDataType.String) { IsFilterable = true, IsFacetable = true },
                new SimpleField(AzureCognitiveSearchMemoryRecord.IsReferenceField, SearchFieldDataType.Boolean) { IsFilterable = true, IsFacetable = true },
            },
            VectorSearch = new VectorSearch
            {
                AlgorithmConfigurations =
                {
                    new HnswVectorSearchAlgorithmConfiguration(configName)
                    {
                        Parameters = new HnswParameters { Metric = VectorSearchAlgorithmMetric.Cosine }
                    }
                }
            }
        };

        return this._adminClient.CreateIndexAsync(newIndex, cancellationToken);
    }

    private async IAsyncEnumerable<string> GetIndexesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var indexes = this._adminClient.GetIndexesAsync(cancellationToken).ConfigureAwait(false);
        await foreach (SearchIndex? index in indexes)
        {
            yield return index.Name;
        }
    }

    private async Task<string> UpsertRecordAsync(
        string indexName,
        AzureCognitiveSearchMemoryRecord record,
        CancellationToken cancellationToken = default)
    {
        var list = await this.UpsertBatchAsync(indexName, new List<AzureCognitiveSearchMemoryRecord> { record }, cancellationToken).ConfigureAwait(false);
        return list.First();
    }

    private async Task<List<string>> UpsertBatchAsync(
        string indexName,
        IList<AzureCognitiveSearchMemoryRecord> records,
        CancellationToken cancellationToken = default)
    {
        var keys = new List<string>();

        if (records.Count < 1) { return keys; }

        var embeddingSize = records[0].Embedding.Length;

        var client = this.GetSearchClient(indexName);

        Task<Response<IndexDocumentsResult>> UpsertCode()
        {
            return client.IndexDocumentsAsync(
                IndexDocumentsBatch.Upload(records),
                new IndexDocumentsOptions { ThrowOnAnyError = true },
                cancellationToken: cancellationToken);
        }

        Response<IndexDocumentsResult>? result;
        try
        {
            result = await UpsertCode().ConfigureAwait(false);
        }
        catch (RequestFailedException e) when (e.Status == 404)
        {
            await this.CreateIndexAsync(indexName, embeddingSize, cancellationToken).ConfigureAwait(false);
            result = await UpsertCode().ConfigureAwait(false);
        }

        if (result == null || result.Value.Results.Count == 0)
        {
            throw new SKException("Memory write returned null or an empty set");
        }

        return result.Value.Results.Select(x => x.Key).ToList();
    }

    /// <summary>
    /// Normalize index name to match ACS rules.
    /// The method doesn't handle all the error scenarios, leaving it to the service
    /// to throw an error for edge cases not handled locally.
    /// </summary>
    /// <param name="indexName">Value to normalize</param>
    /// <returns>Normalized name</returns>
    private string NormalizeIndexName(string indexName)
    {
        if (indexName.Length > 128)
        {
            throw new SKException("The collection name is too long, it cannot exceed 128 chars.");
        }

#pragma warning disable CA1308 // The service expects a lowercase string
        indexName = indexName.ToLowerInvariant();
#pragma warning restore CA1308

        return s_replaceIndexNameSymbolsRegex.Replace(indexName.Trim(), "-");
    }

    /// <summary>
    /// Get a search client for the index specified.
    /// Note: the index might not exist, but we avoid checking everytime and the extra latency.
    /// </summary>
    /// <param name="indexName">Index name</param>
    /// <returns>Search client ready to read/write</returns>
    private SearchClient GetSearchClient(string indexName)
    {
        // Search an available client from the local cache
        if (!this._clientsByIndex.TryGetValue(indexName, out SearchClient client))
        {
            client = this._adminClient.GetSearchClient(indexName);
            this._clientsByIndex[indexName] = client;
        }

        return client;
    }

    /// <summary>
    /// Options used by the Azure Cognitive Search client, e.g. User Agent.
    /// See also https://github.com/Azure/azure-sdk-for-net/blob/main/sdk/core/Azure.Core/src/DiagnosticsOptions.cs
    /// </summary>
    private static SearchClientOptions GetClientOptions()
    {
        return new SearchClientOptions
        {
            Diagnostics =
            {
                IsTelemetryEnabled = Telemetry.IsTelemetryEnabled,
                ApplicationId = Telemetry.HttpUserAgent,
            },
        };
    }

    #endregion
}
