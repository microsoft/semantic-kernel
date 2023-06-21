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
using Microsoft.SemanticKernel.Connectors.Memory.Chroma.Http.ApiSchema;
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

        var ids = keys.ToArray();
        var include = this.GetEmbeddingIncludeTypes(withEmbeddings: withEmbeddings);

        var embeddingsModel = await this._chromaClient.GetEmbeddingsAsync(collection.Id, ids, include, cancellationToken).ConfigureAwait(false);

        var recordCount = embeddingsModel.Ids?.Count ?? 0;

        for (var recordIndex = 0; recordIndex < recordCount; recordIndex++)
        {
            yield return this.GetMemoryRecordFromEmbeddingsModel(embeddingsModel, recordIndex);
        }
    }

    public IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancellationToken = default)
    {
        return this._chromaClient.ListCollectionsAsync(cancellationToken);
    }

    public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(string collectionName, Embedding<float> embedding, double minRelevanceScore = 0, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
        var results = this.GetNearestMatchesAsync(
            collectionName,
            embedding,
            minRelevanceScore: minRelevanceScore,
            limit: 1,
            withEmbeddings: withEmbedding,
            cancellationToken: cancellationToken);

        (MemoryRecord memoryRecord, double similarityScore) = await results.FirstOrDefaultAsync(cancellationToken).ConfigureAwait(false);

        return (memoryRecord, similarityScore);
    }

    public async IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(string collectionName, Embedding<float> embedding, int limit, double minRelevanceScore = 0, bool withEmbeddings = false, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        var collection = await this.GetCollectionOrThrowAsync(collectionName, cancellationToken).ConfigureAwait(false);

        var queryEmbeddings = new float[][] { embedding.Vector.ToArray() };
        var nResults = limit;
        var include = this.GetEmbeddingIncludeTypes(withEmbeddings: withEmbeddings, withDistances: true);

        var queryResultModel = await this._chromaClient.QueryEmbeddingsAsync(collection.Id, queryEmbeddings, nResults, include, cancellationToken).ConfigureAwait(false);

        var recordCount = queryResultModel.Ids?.Count ?? 0;

        for (var recordIndex = 0; recordIndex < recordCount; recordIndex++)
        {
            (MemoryRecord memoryRecord, double similarityScore) = this.GetMemoryRecordFromQueryResultModel(queryResultModel, recordIndex);

            if (similarityScore >= minRelevanceScore)
            {
                yield return (memoryRecord, similarityScore);
            }
        }
    }

    public async Task RemoveAsync(string collectionName, string key, CancellationToken cancellationToken = default)
    {
        await this.RemoveBatchAsync(collectionName, new[] { key }, cancellationToken).ConfigureAwait(false);
    }

    public async Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        var collection = await this.GetCollectionOrThrowAsync(collectionName, cancellationToken).ConfigureAwait(false);

        await this._chromaClient.DeleteEmbeddingsAsync(collection.Id, keys.ToArray(), cancellationToken).ConfigureAwait(false);
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

        var ids = new string[recordsLength];
        var embeddings = new float[recordsLength][];
        var metadatas = new object[recordsLength];

        for (var i = 0; i < recordsLength; i++)
        {
            ids[i] = recordsArray[i].Metadata.Id;
            embeddings[i] = recordsArray[i].Embedding.Vector.ToArray();
            metadatas[i] = recordsArray[i].Metadata;
        }

        await this._chromaClient.AddEmbeddingsAsync(collection.Id, ids, embeddings, metadatas, cancellationToken).ConfigureAwait(false);

        foreach (var record in recordsArray)
        {
            yield return record.Metadata.Id;
        }
    }

    #region private ================================================================================

    private const string IncludeMetadatas = "metadatas";
    private const string IncludeEmbeddings = "embeddings";
    private const string IncludeDistances = "distances";

    private readonly ILogger _logger;
    private readonly IChromaClient _chromaClient;
    private readonly List<string> _defaultEmbeddingIncludeTypes = new() { IncludeMetadatas };

    private async Task<ChromaCollectionModel> GetCollectionOrThrowAsync(string collectionName, CancellationToken cancellationToken)
    {
        return
            await this._chromaClient.GetCollectionAsync(collectionName, cancellationToken).ConfigureAwait(false) ??
            throw new ChromaMemoryStoreException($"Collection {collectionName} does not exist");
    }

    private string[] GetEmbeddingIncludeTypes(bool withEmbeddings = false, bool withDistances = false)
    {
        var includeList = new List<string>(this._defaultEmbeddingIncludeTypes);

        if (withEmbeddings)
        {
            includeList.Add(IncludeEmbeddings);
        }

        if (withDistances)
        {
            includeList.Add(IncludeDistances);
        }

        return includeList.ToArray();
    }

    private MemoryRecord GetMemoryRecordFromEmbeddingsModel(ChromaEmbeddingsModel embeddingsModel, int recordIndex)
    {
        return this.GetMemoryRecordFromModel(embeddingsModel.Metadatas, embeddingsModel.Embeddings, embeddingsModel.Ids, recordIndex);
    }

    private (MemoryRecord, double) GetMemoryRecordFromQueryResultModel(ChromaQueryResultModel queryResultModel, int recordIndex)
    {
        var memoryRecord = this.GetMemoryRecordFromModel(queryResultModel.Metadatas, queryResultModel.Embeddings, queryResultModel.Ids, recordIndex);
        var similarityScore = this.GetSimilarityScore(queryResultModel.Distances, recordIndex);

        return (memoryRecord, similarityScore);
    }

    private MemoryRecord GetMemoryRecordFromModel(List<Dictionary<string, object>>? metadatas, List<float[]>? embeddings, List<string>? ids, int recordIndex)
    {
        var metadata = this.GetMetadataForMemoryRecord(metadatas, recordIndex);
        var embeddingsVector = this.GetEmbeddingForMemoryRecord(embeddings, recordIndex);
        var key = ids?[recordIndex];

        return MemoryRecord.FromJsonMetadata(
            json: metadata,
            embedding: embeddingsVector,
            key: key);
    }

    private string GetMetadataForMemoryRecord(List<Dictionary<string, object>>? metadatas, int recordIndex)
    {
        return metadatas != null ? JsonSerializer.Serialize(metadatas[recordIndex]) : string.Empty;
    }

    private Embedding<float> GetEmbeddingForMemoryRecord(List<float[]>? embeddings, int recordIndex)
    {
        return embeddings != null ? new Embedding<float>(embeddings[recordIndex]) : Embedding<float>.Empty;
    }

    private double GetSimilarityScore(List<double>? distances, int recordIndex)
    {
        var similarityScore = distances != null ? 1 - distances[recordIndex] : default;

        if (similarityScore < 0)
        {
            similarityScore = 0;
        }

        return similarityScore;
    }

    #endregion
}
