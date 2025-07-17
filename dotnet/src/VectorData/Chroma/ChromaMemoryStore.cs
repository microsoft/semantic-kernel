﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.Chroma;

/// <summary>
/// An implementation of <see cref="IMemoryStore" /> for Chroma.
/// </summary>
public class ChromaMemoryStore : IMemoryStore
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ChromaMemoryStore"/> class.
    /// </summary>
    /// <param name="endpoint">Chroma server endpoint URL.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public ChromaMemoryStore(string endpoint, ILoggerFactory? loggerFactory = null)
        : this(new ChromaClient(endpoint, loggerFactory), loggerFactory)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChromaMemoryStore"/> class.
    /// </summary>
    /// <param name="httpClient">The <see cref="HttpClient"/> instance used for making HTTP requests.</param>
    /// <param name="endpoint">Chroma server endpoint URL.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public ChromaMemoryStore(HttpClient httpClient, string? endpoint = null, ILoggerFactory? loggerFactory = null)
        : this(new ChromaClient(httpClient, endpoint, loggerFactory), loggerFactory)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChromaMemoryStore"/> class.
    /// </summary>
    /// <param name="client">Instance of <see cref="IChromaClient"/> implementation.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public ChromaMemoryStore(IChromaClient client, ILoggerFactory? loggerFactory = null)
    {
        this._chromaClient = client;
        this._logger = loggerFactory?.CreateLogger(typeof(ChromaMemoryStore)) ?? NullLogger.Instance;
    }

    /// <inheritdoc />
    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        await this._chromaClient.CreateCollectionAsync(collectionName, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        try
        {
            await this._chromaClient.DeleteCollectionAsync(collectionName, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException e) when (VerifyCollectionDoesNotExistMessage(e.ResponseContent, collectionName))
        {
            this._logger.LogError("Cannot delete non-existent collection {0}", collectionName);
            throw new KernelException($"Cannot delete non-existent collection {collectionName}", e);
        }
    }

    /// <inheritdoc />
    public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        var collection = await this.GetCollectionAsync(collectionName, cancellationToken).ConfigureAwait(false);

        return collection is not null;
    }

    /// <inheritdoc />
    public async Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
        return await this.GetBatchAsync(collectionName, [key], withEmbedding, cancellationToken)
            .FirstOrDefaultAsync(cancellationToken)
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
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

    /// <inheritdoc />
    public IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancellationToken = default)
    {
        return this._chromaClient.ListCollectionsAsync(cancellationToken);
    }

    /// <inheritdoc />
    public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(string collectionName, ReadOnlyMemory<float> embedding, double minRelevanceScore = 0, bool withEmbedding = false, CancellationToken cancellationToken = default)
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

    /// <inheritdoc />
    public async IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(string collectionName, ReadOnlyMemory<float> embedding, int limit, double minRelevanceScore = 0, bool withEmbeddings = false, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        var collection = await this.GetCollectionOrThrowAsync(collectionName, cancellationToken).ConfigureAwait(false);

        ReadOnlyMemory<float>[] queryEmbeddings = [embedding];
        var include = this.GetEmbeddingIncludeTypes(withEmbeddings: withEmbeddings, withDistances: true);

        var queryResultModel = await this._chromaClient.QueryEmbeddingsAsync(collection.Id, queryEmbeddings, limit, include, cancellationToken).ConfigureAwait(false);

        var recordCount = queryResultModel.Ids?.FirstOrDefault()?.Count ?? 0;

        for (var recordIndex = 0; recordIndex < recordCount; recordIndex++)
        {
            (MemoryRecord memoryRecord, double similarityScore) = this.GetMemoryRecordFromQueryResultModel(queryResultModel, recordIndex);

            if (similarityScore >= minRelevanceScore)
            {
                yield return (memoryRecord, similarityScore);
            }
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
        Verify.NotNullOrWhiteSpace(collectionName);

        var collection = await this.GetCollectionOrThrowAsync(collectionName, cancellationToken).ConfigureAwait(false);

        await this._chromaClient.DeleteEmbeddingsAsync(collection.Id, keys.ToArray(), cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        var key = await this.UpsertBatchAsync(collectionName, [record], cancellationToken)
            .FirstOrDefaultAsync(cancellationToken)
            .ConfigureAwait(false);

        return key ?? string.Empty;
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        var collection = await this.GetCollectionOrThrowAsync(collectionName, cancellationToken).ConfigureAwait(false);

        var recordsArray = records.ToArray();
        var recordsLength = recordsArray.Length;

        var ids = new string[recordsLength];
        var embeddings = new ReadOnlyMemory<float>[recordsLength];
        var metadatas = new object[recordsLength];

        for (var i = 0; i < recordsLength; i++)
        {
            ids[i] = recordsArray[i].Metadata.Id;
            embeddings[i] = recordsArray[i].Embedding;
            metadatas[i] = recordsArray[i].Metadata;
        }

        await this._chromaClient.UpsertEmbeddingsAsync(collection.Id, ids, embeddings, metadatas, cancellationToken).ConfigureAwait(false);

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
    private readonly List<string> _defaultEmbeddingIncludeTypes = [IncludeMetadatas];

    private async Task<ChromaCollectionModel> GetCollectionOrThrowAsync(string collectionName, CancellationToken cancellationToken)
    {
        return
            await this.GetCollectionAsync(collectionName, cancellationToken).ConfigureAwait(false) ??
            throw new KernelException($"Collection {collectionName} does not exist");
    }

    private async Task<ChromaCollectionModel?> GetCollectionAsync(string collectionName, CancellationToken cancellationToken)
    {
        try
        {
            return await this._chromaClient.GetCollectionAsync(collectionName, cancellationToken).ConfigureAwait(false);
        }
        catch (HttpOperationException e) when (VerifyCollectionDoesNotExistMessage(e.ResponseContent, collectionName))
        {
            this._logger.LogDebug("Collection {0} does not exist", collectionName);

            return null;
        }
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

        return [.. includeList];
    }

    private MemoryRecord GetMemoryRecordFromEmbeddingsModel(ChromaEmbeddingsModel embeddingsModel, int recordIndex)
    {
        return this.GetMemoryRecordFromModel(embeddingsModel.Metadatas, embeddingsModel.Embeddings, embeddingsModel.Ids, recordIndex);
    }

    private (MemoryRecord, double) GetMemoryRecordFromQueryResultModel(ChromaQueryResultModel queryResultModel, int recordIndex)
    {
        var ids = queryResultModel.Ids?.FirstOrDefault();
        var embeddings = queryResultModel.Embeddings?.FirstOrDefault();
        var metadatas = queryResultModel.Metadatas?.FirstOrDefault();
        var distances = queryResultModel.Distances?.FirstOrDefault();

        var memoryRecord = this.GetMemoryRecordFromModel(metadatas, embeddings, ids, recordIndex);
        var similarityScore = this.GetSimilarityScore(distances, recordIndex);

        return (memoryRecord, similarityScore);
    }

    private MemoryRecord GetMemoryRecordFromModel(List<Dictionary<string, object>>? metadatas, List<float[]>? embeddings, List<string>? ids, int recordIndex)
    {
        var metadata = this.GetMetadataForMemoryRecord(metadatas, recordIndex);
        var embeddingsVector = this.GetEmbeddingForMemoryRecord(embeddings, recordIndex);
        var key = ids?[recordIndex];

        return MemoryRecord.FromMetadata(
            metadata: metadata,
            embedding: embeddingsVector,
            key: key);
    }

    private MemoryRecordMetadata GetMetadataForMemoryRecord(List<Dictionary<string, object>>? metadatas, int recordIndex)
    {
        var serializedMetadata = metadatas is not null ? JsonSerializer.Serialize(metadatas[recordIndex], JsonOptionsCache.Default) : string.Empty;

        return
            JsonSerializer.Deserialize<MemoryRecordMetadata>(serializedMetadata, JsonOptionsCache.Default) ??
            throw new KernelException("Unable to deserialize memory record metadata.");
    }

    private ReadOnlyMemory<float> GetEmbeddingForMemoryRecord(List<float[]>? embeddings, int recordIndex)
    {
        return embeddings is not null ? embeddings[recordIndex] : ReadOnlyMemory<float>.Empty;
    }

    private double GetSimilarityScore(List<double>? distances, int recordIndex)
    {
        var similarityScore = distances is not null ? 1.0 / (1.0 + distances[recordIndex]) : default;

        if (similarityScore < 0)
        {
            similarityScore = 0;
        }

        return similarityScore;
    }

    /// <summary>
    /// Checks if Chroma API error means that collection does not exist.
    /// </summary>
    /// <param name="responseContent">Response content.</param>
    /// <param name="collectionName">Collection name.</param>
    private static bool VerifyCollectionDoesNotExistMessage(string? responseContent, string collectionName)
    {
        return responseContent?.Contains(string.Format(CultureInfo.InvariantCulture, "Collection {0} does not exist", collectionName)) ?? false;
    }

    #endregion
}
