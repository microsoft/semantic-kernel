// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Memory.Chroma;

public class ChromaMemoryStore : IMemoryStore
{
    public ChromaMemoryStore(string endpoint, ILogger? logger = null)
        : this(new ChromaClient(endpoint, logger), logger)
    { }

    public ChromaMemoryStore(HttpClient httpClient, string? endpoint = null, ILogger? logger = null)
        : this(new ChromaClient(httpClient, endpoint, logger), logger)
    { }

    public ChromaMemoryStore(IChromaClient client, ILogger? logger = null)
    {
        this._chromaClient = client;
        this._logger = logger ?? NullLogger<ChromaMemoryStore>.Instance;
    }

    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        await this._chromaClient.CreateCollectionAsync(collectionName, cancellationToken).ConfigureAwait(false);
    }

    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        try
        {
            await this._chromaClient.DeleteCollectionAsync(collectionName, cancellationToken).ConfigureAwait(false);
        }
        catch (ChromaClientException e) when (e.DeleteNonExistentCollectionException())
        {
            this._logger.LogError("Cannot delete non-existent collection {0}", collectionName);
            throw new ChromaMemoryStoreException($"Cannot delete non-existent collection {collectionName}", e);
        }
    }

    public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        var collection = await this._chromaClient.GetCollectionAsync(collectionName, cancellationToken).ConfigureAwait(false);

        return collection != null;
    }

    public Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
        throw new System.NotImplementedException();
    }

    public IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings = false, CancellationToken cancellationToken = default)
    {
        throw new System.NotImplementedException();
    }

    public IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancellationToken = default)
    {
        return this._chromaClient.ListCollectionsAsync(cancellationToken);
    }

    public Task<(MemoryRecord, double)?> GetNearestMatchAsync(string collectionName, Embedding<float> embedding, double minRelevanceScore = 0, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
        throw new System.NotImplementedException();
    }

    public IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(string collectionName, Embedding<float> embedding, int limit, double minRelevanceScore = 0, bool withEmbeddings = false, CancellationToken cancellationToken = default)
    {
        throw new System.NotImplementedException();
    }

    public Task RemoveAsync(string collectionName, string key, CancellationToken cancellationToken = default)
    {
        throw new System.NotImplementedException();
    }

    public Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        throw new System.NotImplementedException();
    }

    public Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken = default)
    {
        throw new System.NotImplementedException();
    }

    public IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records, CancellationToken cancellationToken = default)
    {
        throw new System.NotImplementedException();
    }

    #region private ================================================================================

    private readonly ILogger _logger;
    private readonly IChromaClient _chromaClient;

    #endregion
}
