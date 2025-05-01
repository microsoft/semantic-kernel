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
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

#pragma warning disable SKEXP0001 // IMemoryStore is experimental (but we're obsoleting)

/// <summary>
/// <see cref="AzureAISearchMemoryStore"/> is a memory store implementation using Azure AI Search.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being phased out, use Microsoft.Extensions.VectorData and AzureAISearchVectorStore")]
public partial class AzureAISearchMemoryStore : IMemoryStore
{
    /// <summary>
    /// Create a new instance of memory storage using Azure AI Search.
    /// </summary>
    /// <param name="endpoint">Azure AI Search URI, e.g. "https://contoso.search.windows.net"</param>
    /// <param name="apiKey">API Key</param>
    public AzureAISearchMemoryStore(string endpoint, string apiKey)
        : this(new SearchIndexClient(new Uri(endpoint), new AzureKeyCredential(apiKey), GetClientOptions()))
    {
    }

    /// <summary>
    /// Create a new instance of memory storage using Azure AI Search.
    /// </summary>
    /// <param name="endpoint">Azure AI Search URI, e.g. "https://contoso.search.windows.net"</param>
    /// <param name="credentials">Azure service</param>
    public AzureAISearchMemoryStore(string endpoint, TokenCredential credentials)
        : this(new SearchIndexClient(new Uri(endpoint), credentials, GetClientOptions()))
    {
    }

    /// <summary>
    /// Create a new instance of memory storage using Azure AI Search.
    /// </summary>
    /// <param name="searchIndexClient">Azure AI Search client that can be used to manage indexes on a Search service.</param>
    public AzureAISearchMemoryStore(SearchIndexClient searchIndexClient)
    {
        this._adminClient = searchIndexClient;
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
        return RunMemoryStoreOperationAsync(() => this.GetIndexesAsync(cancellationToken));
    }

    /// <inheritdoc />
    public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        var normalizedIndexName = this.NormalizeIndexName(collectionName);

        var indexes = RunMemoryStoreOperationAsync(() => this.GetIndexesAsync(cancellationToken));

        return await indexes
            .AnyAsync(index =>
                    string.Equals(index, collectionName, StringComparison.OrdinalIgnoreCase) ||
                    string.Equals(index, normalizedIndexName, StringComparison.OrdinalIgnoreCase),
                cancellationToken: cancellationToken
            )
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        var normalizedIndexName = this.NormalizeIndexName(collectionName);

        await RunMemoryStoreOperationAsync(() => this._adminClient.DeleteIndexAsync(normalizedIndexName, cancellationToken))
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken = default)
    {
        var normalizedIndexName = this.NormalizeIndexName(collectionName);

        return await RunMemoryStoreOperationAsync(() => this.UpsertRecordAsync(normalizedIndexName, AzureAISearchMemoryRecord.FromMemoryRecord(record), cancellationToken))
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var normalizedIndexName = this.NormalizeIndexName(collectionName);

        var searchRecords = records.Select(AzureAISearchMemoryRecord.FromMemoryRecord).ToList();

        var result = await RunMemoryStoreOperationAsync(() => this.UpsertBatchAsync(normalizedIndexName, searchRecords, cancellationToken))
            .ConfigureAwait(false);

        foreach (var x in result) { yield return x; }
    }

    /// <inheritdoc />
    public async Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
        var normalizedIndexName = this.NormalizeIndexName(collectionName);
        var client = this.GetSearchClient(normalizedIndexName);

        var encodedId = AzureAISearchMemoryRecord.EncodeId(key);

        Response<AzureAISearchMemoryRecord>? result;

        try
        {
            result = await RunMemoryStoreOperationAsync(() => client.GetDocumentAsync<AzureAISearchMemoryRecord>(encodedId, cancellationToken: cancellationToken))
                .ConfigureAwait(false);
        }
        catch (HttpOperationException e) when (e.StatusCode == System.Net.HttpStatusCode.NotFound)
        {
            // Index not found, no data to return
            return null;
        }

        if (result?.Value is null)
        {
            throw new KernelException("Memory read returned null");
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
            if (record is not null) { yield return record; }
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
        // Cosine similarity range: -1 .. +1
        minRelevanceScore = Math.Max(-1, Math.Min(1, minRelevanceScore));

        var normalizedIndexName = this.NormalizeIndexName(collectionName);

        var client = this.GetSearchClient(normalizedIndexName);

        VectorizedQuery vectorQuery = new(MemoryMarshal.TryGetArray(embedding, out var array) && array.Count == embedding.Length ? array.Array! : embedding.ToArray())
        {
            KNearestNeighborsCount = limit,
            Fields = { AzureAISearchMemoryRecord.EmbeddingField },
        };

        SearchOptions options = new()
        {
            VectorSearch = new()
            {
                Queries = { vectorQuery }
            },
        };

        Response<SearchResults<AzureAISearchMemoryRecord>>? searchResult = null;
        try
        {
            searchResult = await RunMemoryStoreOperationAsync(() => client.SearchAsync<AzureAISearchMemoryRecord>(null, options, cancellationToken: cancellationToken))
                .ConfigureAwait(false);
        }
        catch (HttpOperationException e) when (e.StatusCode == System.Net.HttpStatusCode.NotFound)
        {
            // Index not found, no data to return
        }

        if (searchResult is null) { yield break; }

        var minAzureSearchScore = CosineSimilarityToScore(minRelevanceScore);
        await foreach (SearchResult<AzureAISearchMemoryRecord>? doc in searchResult.Value.GetResultsAsync().ConfigureAwait(false))
        {
            if (doc is null || doc.Score < minAzureSearchScore) { continue; }

            MemoryRecord memoryRecord = doc.Document.ToMemoryRecord(withEmbeddings);

            yield return (memoryRecord, ScoreToCosineSimilarity(doc.Score ?? 0));
        }
    }

    /// <inheritdoc />
    public async Task RemoveAsync(string collectionName, string key, CancellationToken cancellationToken = default)
    {
        await this.RemoveBatchAsync(collectionName, [key], cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        var normalizedIndexName = this.NormalizeIndexName(collectionName);

        var records = keys.Select(x => new AzureAISearchMemoryRecord(x));

        var client = this.GetSearchClient(normalizedIndexName);

        try
        {
            await RunMemoryStoreOperationAsync(() => client.DeleteDocumentsAsync(records, cancellationToken: cancellationToken)).ConfigureAwait(false);
        }
        catch (HttpOperationException e) when (e.StatusCode == System.Net.HttpStatusCode.NotFound)
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
#if NET
    [GeneratedRegex(@"[\s|\\|/|.|_|:]")]
    private static partial Regex ReplaceIndexNameSymbolsRegex();
#else
    private static Regex ReplaceIndexNameSymbolsRegex() => s_replaceIndexNameSymbolsRegex;
    private static readonly Regex s_replaceIndexNameSymbolsRegex = new(@"[\s|\\|/|.|_|:]");
#endif

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
            throw new ArgumentOutOfRangeException(nameof(embeddingSize), "Invalid embedding size: the value must be greater than zero.");
        }

        const string ProfileName = "searchProfile";
        const string AlgorithmName = "searchAlgorithm";

        var newIndex = new SearchIndex(indexName)
        {
            Fields =
            [
                new SimpleField(AzureAISearchMemoryRecord.IdField, SearchFieldDataType.String) { IsKey = true },
                new VectorSearchField(AzureAISearchMemoryRecord.EmbeddingField, embeddingSize, ProfileName),
                new(AzureAISearchMemoryRecord.TextField, SearchFieldDataType.String) { IsFilterable = true, IsFacetable = true },
                new SimpleField(AzureAISearchMemoryRecord.DescriptionField, SearchFieldDataType.String) { IsFilterable = true, IsFacetable = true },
                new SimpleField(AzureAISearchMemoryRecord.AdditionalMetadataField, SearchFieldDataType.String) { IsFilterable = true, IsFacetable = true },
                new SimpleField(AzureAISearchMemoryRecord.ExternalSourceNameField, SearchFieldDataType.String) { IsFilterable = true, IsFacetable = true },
                new SimpleField(AzureAISearchMemoryRecord.IsReferenceField, SearchFieldDataType.Boolean) { IsFilterable = true, IsFacetable = true },
            ],
            VectorSearch = new VectorSearch
            {
                Algorithms =
                {
                    new HnswAlgorithmConfiguration(AlgorithmName)
                    {
                        Parameters = new HnswParameters { Metric = VectorSearchAlgorithmMetric.Cosine }
                    }
                },
                Profiles = { new VectorSearchProfile(ProfileName, AlgorithmName) }
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
        AzureAISearchMemoryRecord record,
        CancellationToken cancellationToken = default)
    {
        var list = await this.UpsertBatchAsync(indexName, new List<AzureAISearchMemoryRecord> { record }, cancellationToken).ConfigureAwait(false);
        return list.First();
    }

    private async Task<List<string>> UpsertBatchAsync(
        string indexName,
        List<AzureAISearchMemoryRecord> records,
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

        if (result is null || result.Value.Results.Count == 0)
        {
            throw new KernelException("Memory write returned null or an empty set");
        }

        return result.Value.Results.Select(x => x.Key).ToList();
    }

    /// <summary>
    /// Normalize index name to match Azure AI Search rules.
    /// The method doesn't handle all the error scenarios, leaving it to the service
    /// to throw an error for edge cases not handled locally.
    /// </summary>
    /// <param name="indexName">Value to normalize</param>
    /// <param name="parameterName">The name of the argument used with <paramref name="indexName"/>.</param>
    /// <returns>Normalized name</returns>
    private string NormalizeIndexName(string indexName, [CallerArgumentExpression(nameof(indexName))] string? parameterName = null)
    {
        if (indexName.Length > 128)
        {
            throw new ArgumentOutOfRangeException(parameterName, "The collection name is too long, it cannot exceed 128 chars.");
        }

#pragma warning disable CA1308 // The service expects a lowercase string
        indexName = indexName.ToLowerInvariant();
#pragma warning restore CA1308

        return ReplaceIndexNameSymbolsRegex().Replace(indexName.Trim(), "-");
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
        if (!this._clientsByIndex.TryGetValue(indexName, out SearchClient? client))
        {
            client = this._adminClient.GetSearchClient(indexName);
            this._clientsByIndex[indexName] = client;
        }

        return client;
    }

    /// <summary>
    /// Options used by the Azure AI Search client, e.g. User Agent.
    /// See also https://github.com/Azure/azure-sdk-for-net/blob/main/sdk/core/Azure.Core/src/DiagnosticsOptions.cs
    /// </summary>
    private static SearchClientOptions GetClientOptions()
    {
        return new SearchClientOptions
        {
            Diagnostics =
            {
                ApplicationId = HttpHeaderConstant.Values.UserAgent,
            },
        };
    }

    private static async Task<T> RunMemoryStoreOperationAsync<T>(Func<Task<T>> operation)
    {
        try
        {
            return await operation.Invoke().ConfigureAwait(false);
        }
        catch (RequestFailedException e)
        {
            throw e.ToHttpOperationException();
        }
    }

    private static async IAsyncEnumerable<T> RunMemoryStoreOperationAsync<T>(Func<IAsyncEnumerable<T>> operation)
    {
        IAsyncEnumerator<T> enumerator = operation.Invoke().GetAsyncEnumerator();

        await using (enumerator.ConfigureAwait(false))
        {
            while (true)
            {
                try
                {
                    if (!await enumerator.MoveNextAsync().ConfigureAwait(false))
                    {
                        break;
                    }
                }
                catch (RequestFailedException e)
                {
                    throw e.ToHttpOperationException();
                }

                yield return enumerator.Current;
            }
        }
    }

    private static double ScoreToCosineSimilarity(double score)
    {
        // Azure AI Search score formula. The min value is 0.333 for cosine similarity -1.
        score = Math.Max(score, 1.0 / 3);
        return 2 - (1 / score);
    }

    private static double CosineSimilarityToScore(double similarity)
    {
        return 1 / (2 - similarity);
    }

    #endregion
}
