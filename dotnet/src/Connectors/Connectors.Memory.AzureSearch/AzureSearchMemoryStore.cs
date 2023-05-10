// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Azure.Core;
using Azure.Search.Documents;
using Azure.Search.Documents.Models;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Memory.AzureSearch;

public class AzureSearchMemoryStore : AzureSearchBase, IMemoryStore
{
    /// <summary>
    /// Create a new instance of memory storage using Azure Cognitive Search.
    /// </summary>
    /// <param name="endpoint">Azure Cognitive Search URI, e.g. "https://contoso.search.windows.net"</param>
    /// <param name="apiKey">API Key</param>
    public AzureSearchMemoryStore(string endpoint, string apiKey)
        : base(endpoint, apiKey)
    {
    }

    /// <summary>
    /// Create a new instance of memory storage using Azure Cognitive Search.
    /// </summary>
    /// <param name="endpoint">Azure Cognitive Search URI, e.g. "https://contoso.search.windows.net"</param>
    /// <param name="credentials">Azure service</param>
    public AzureSearchMemoryStore(string endpoint, TokenCredential credentials)
        : base(endpoint, credentials)
    {
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

        return this.AdminClient.DeleteIndexAsync(normalizeIndexName, cancellationToken);
    }

    /// <inheritdoc />
    public Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken = default)
    {
        collectionName = this.NormalizeIndexName(collectionName);
        return this.UpsertRecordAsync(collectionName, AzureSearchRecord.FromMemoryRecord(record), cancellationToken);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        collectionName = this.NormalizeIndexName(collectionName);
        IList<AzureSearchRecord> azureSearchRecords = records.Select(AzureSearchRecord.FromMemoryRecord).ToList();
        List<string> result = await this.UpsertBatchAsync(collectionName, azureSearchRecords, cancellationToken).ConfigureAwait(false);
        foreach (var x in result) { yield return x; }
    }

    /// <inheritdoc />
    public async Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
        collectionName = this.NormalizeIndexName(collectionName);
        var client = this.GetSearchClient(collectionName);
        Response<AzureSearchRecord>? result;
        try
        {
            result = await client
                .GetDocumentAsync<AzureSearchRecord>(AzureSearchRecord.EncodeId(key), cancellationToken: cancellationToken)
                .ConfigureAwait(false);
        }
        catch (RequestFailedException e) when (e.Status == 404)
        {
            // Index not found, no data to return
            return null;
        }

        if (result?.Value == null)
        {
            throw new AzureCognitiveSearchMemoryException(
                AzureCognitiveSearchMemoryException.ErrorCodes.ReadFailure,
                "Memory read returned null");
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
        Embedding<float> embedding,
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
        Embedding<float> embedding,
        int limit,
        double minRelevanceScore = 0,
        bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        collectionName = this.NormalizeIndexName(collectionName);

        var client = this.GetSearchClient(collectionName);

        SearchQueryVector vectorQuery = new()
        {
            K = limit,
            Fields = AzureSearchRecord.EmbeddingField,
            Value = embedding.Vector.ToList()
        };

        SearchOptions options = new() { Vector = vectorQuery };
        Response<SearchResults<AzureSearchRecord>>? searchResult = null;
        try
        {
            searchResult = await client
                .SearchAsync<AzureSearchRecord>("*", options, cancellationToken: cancellationToken)
                .ConfigureAwait(false);
        }
        catch (RequestFailedException e) when (e.Status == 404)
        {
            // Index not found, no data to return
        }

        if (searchResult == null) { yield break; }

        await foreach (SearchResult<AzureSearchRecord>? doc in searchResult.Value.GetResultsAsync())
        {
            if (doc == null || doc.RerankerScore < minRelevanceScore) { continue; }

            MemoryRecord memoryRecord = doc.Document.ToMemoryRecord(withEmbeddings);

            yield return (memoryRecord, doc.RerankerScore ?? 0);
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

        var records = keys.Select(x => new List<AzureSearchRecord> { new(x) });

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
}
