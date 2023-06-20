// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Diagnostics;
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
        Verify.NotNullOrWhiteSpace(collectionName);

        await this._chromaClient.CreateCollectionAsync(collectionName, cancellationToken).ConfigureAwait(false);
    }

    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

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
        Verify.NotNullOrWhiteSpace(collectionName);

        var collection = await this._chromaClient.GetCollectionAsync(collectionName, cancellationToken).ConfigureAwait(false);

        return collection != null;
    }

    public async Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
        return await this.GetBatchAsync(collectionName, new[] { key }, withEmbedding, cancellationToken)
            .FirstOrDefaultAsync(cancellationToken)
            .ConfigureAwait(false);
    }

    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings = false, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        var collection = await this.GetCollectionOrThrowAsync(collectionName, cancellationToken).ConfigureAwait(false);

        string[] ids = keys.ToArray();
        string[] include = this.GetEmbeddingIncludeTypes(withEmbeddings);

        var embeddings = await this._chromaClient.GetEmbeddingsAsync(collection.Id, ids, include, cancellationToken).ConfigureAwait(false);

        var resultCount = embeddings.Ids?.Count ?? 0;

        for (var i = 0; i < resultCount; i++)
        {
            var metadata = embeddings.Metadatas != null ? JsonSerializer.Serialize(embeddings.Metadatas[i]) : string.Empty;
            var embeddingsVector = embeddings.Embeddings != null ? new Embedding<float>(embeddings.Embeddings[i]) : Embedding<float>.Empty;
            var key = embeddings.Ids?[i];

            yield return MemoryRecord.FromJsonMetadata(
                json: metadata,
                embedding: embeddingsVector,
                key: key);
        }
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

    public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        var key = await this.UpsertBatchAsync(collectionName, new[] { record }, cancellationToken)
            .FirstOrDefaultAsync(cancellationToken)
            .ConfigureAwait(false);

        return key ?? string.Empty;
    }

    public async IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        var collection = await this.GetCollectionOrThrowAsync(collectionName, cancellationToken).ConfigureAwait(false);

        var recordsArray = records.ToArray();
        var recordsLength = recordsArray.Length;

        string[] ids = new string[recordsLength];
        float[][] embeddings = new float[recordsLength][];
        object[] metadatas = new object[recordsLength];

        for (var i = 0; i < recordsLength; i++)
        {
            ids[i] = recordsArray[i].Key;
            embeddings[i] = recordsArray[i].Embedding.Vector.ToArray();
            metadatas[i] = recordsArray[i].Metadata;
        }

        await this._chromaClient.AddEmbeddingsAsync(collection.Id, ids, embeddings, metadatas, cancellationToken).ConfigureAwait(false);

        foreach (var record in recordsArray)
        {
            yield return record.Key;
        }
    }

    #region private ================================================================================

    private const string IncludeMetadatas = "metadatas";
    private const string IncludeEmbeddings = "embeddings";

    private readonly ILogger _logger;
    private readonly IChromaClient _chromaClient;
    private readonly List<string> _defaultEmbeddingIncludeTypes = new() { IncludeMetadatas };

    private async Task<ChromaCollectionModel> GetCollectionOrThrowAsync(string collectionName, CancellationToken cancellationToken)
    {
        return
            await this._chromaClient.GetCollectionAsync(collectionName, cancellationToken).ConfigureAwait(false) ??
            throw new ChromaMemoryStoreException($"Collection {collectionName} does not exist");
    }

    private string[] GetEmbeddingIncludeTypes(bool withEmbeddings)
    {
        var includeList = new List<string>(this._defaultEmbeddingIncludeTypes);

        if (withEmbeddings)
        {
            includeList.Add(IncludeEmbeddings);
        }

        return includeList.ToArray();
    }

    #endregion
}
