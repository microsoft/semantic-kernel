// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Azure.Core;
using Azure.Search.Documents;
using Azure.Search.Documents.Indexes;
using Azure.Search.Documents.Indexes.Models;
using Azure.Search.Documents.Models;

namespace Microsoft.SemanticKernel.Connectors.Memory.AzureSearch;

public class AzureSearchBase
{
    private readonly ConcurrentDictionary<string, SearchClient> _clientsByIndex = new();

    /// <summary>
    /// Index names cannot contain special chars. We use this rule to replace a few common ones
    /// with an underscore and reduce the chance of errors. If other special chars are used, we leave it
    /// to the service to throw an error.
    /// Note:
    /// - replacing chars introduces a small chance of conflicts, e.g. "the-user" and "the_user".
    /// - we should consider whether making this optional and leave it to the developer to handle.
    /// </summary>
    private static readonly Regex s_replaceIndexNameSymbolsRegex = new(@"[\s|\\|/|.|_|:]");

    private protected readonly SearchIndexClient AdminClient;

    private protected AzureSearchBase(string endpoint, string apiKey)
    {
        AzureKeyCredential credentials = new(apiKey);
        this.AdminClient = new SearchIndexClient(new Uri(endpoint), credentials);
    }

    private protected AzureSearchBase(string endpoint, TokenCredential credentials)
    {
        this.AdminClient = new SearchIndexClient(new Uri(endpoint), credentials);
    }

    /// <summary>
    /// Create a new search index.
    /// </summary>
    /// <param name="indexName">Index name</param>
    /// <param name="embeddingSize">Size of the embedding vector</param>
    /// <param name="cancellationToken">Task cancellation token</param>
    private protected Task<Response<SearchIndex>> CreateIndexAsync(
        string indexName,
        int embeddingSize,
        CancellationToken cancellationToken = default)
    {
        if (embeddingSize < 1)
        {
            throw new AzureCognitiveSearchMemoryException(
                AzureCognitiveSearchMemoryException.ErrorCodes.InvalidEmbeddingSize,
                "Invalid embedding size: the value must be greater than zero.");
        }

        var configName = "searchConfig";
        var newIndex = new SearchIndex(indexName)
        {
            Fields = new List<SearchField>()
            {
                new SimpleField("Id", SearchFieldDataType.String) { IsKey = true },
                new SearchField("Embedding", SearchFieldDataType.Collection(SearchFieldDataType.Single))
                {
                    IsSearchable = true,
                    Dimensions = embeddingSize,
                    VectorSearchConfiguration = configName
                },
                new SimpleField("Text", SearchFieldDataType.String) { IsFilterable = true, IsFacetable = true },
                new SimpleField("Description", SearchFieldDataType.String) { IsFilterable = true, IsFacetable = true },
                new SimpleField("AdditionalMetadata", SearchFieldDataType.String) { IsFilterable = true, IsFacetable = true },
                new SimpleField("ExternalSourceName", SearchFieldDataType.String) { IsFilterable = true, IsFacetable = true },
                new SimpleField("IsReference", SearchFieldDataType.Boolean) { IsFilterable = true, IsFacetable = true },
            },
            VectorSearch = new VectorSearch
            {
                AlgorithmConfigurations =
                {
                    new VectorSearchAlgorithmConfiguration(configName, "hnsw")
                    {
                        HnswParameters = new HnswParameters { Metric = VectorSearchAlgorithmMetric.Cosine }
                    }
                }
            }
        };

        return this.AdminClient.CreateIndexAsync(newIndex, cancellationToken);
    }

    private protected async IAsyncEnumerable<string> GetIndexesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var indexes = this.AdminClient.GetIndexesAsync(cancellationToken).ConfigureAwait(false);
        await foreach (SearchIndex? index in indexes)
        {
            yield return index.Name;
        }
    }

    private protected async Task<string> UpsertRecordAsync(
        string indexName,
        AzureSearchRecord record,
        CancellationToken cancellationToken = default)
    {
        var list = await this.UpsertBatchAsync(indexName, new List<AzureSearchRecord> { record }, cancellationToken).ConfigureAwait(false);
        return list.First();
    }

    private protected async Task<List<string>> UpsertBatchAsync(
        string indexName,
        IList<AzureSearchRecord> records,
        CancellationToken cancellationToken = default)
    {
        var keys = new List<string>();

        if (records.Count < 1) { return keys; }

        var embeddingSize = records[0].Embedding.Count;

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
            throw new AzureCognitiveSearchMemoryException(
                AzureCognitiveSearchMemoryException.ErrorCodes.WriteFailure,
                "Memory write returned null or an empty set");
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
    private protected string NormalizeIndexName(string indexName)
    {
        if (indexName.Length > 128)
        {
            throw new AzureCognitiveSearchMemoryException(
                AzureCognitiveSearchMemoryException.ErrorCodes.InvalidIndexName,
                "The collection name is too long, it cannot exceed 128 chars.");
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
    private protected SearchClient GetSearchClient(string indexName)
    {
        // Search an available client from the local cache
        if (!this._clientsByIndex.TryGetValue(indexName, out SearchClient client))
        {
            client = this.AdminClient.GetSearchClient(indexName);
            this._clientsByIndex[indexName] = client;
        }

        return client;
    }
}
