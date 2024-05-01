// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Azure.Cosmos;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;

/// <summary>
/// An implementation of <see cref="IMemoryStore"/> backed by a Azure Cosmos DB database.
/// Get more details about Azure Cosmos DB vector search  https://learn.microsoft.com/en-us/azure/cosmos-db/
/// </summary>
public class AzureCosmosDBNoSQLMemoryStore : IMemoryStore, IDisposable
{
    private readonly CosmosClient _cosmosClient;
    private readonly VectorEmbeddingPolicy _vectorEmbeddingPolicy;
    private readonly IndexingPolicy _indexingPolicy;
    private readonly string _databaseName;

    /// <summary>
    /// Initiates a AzureCosmosDBNoSQLMemoryStore instance using a Azure Cosmos DB connection string
    /// and other properties required for vector search.
    /// </summary>
    /// <param name="connectionString">Connection string required to connect to Azure Cosmos DB.</param>
    /// <param name="databaseName">The database name to connect to.</param>
    /// <param name="vectorEmbeddingPolicy">Details about the <see cref="Embedding"/> to use.</param>
    /// <param name="indexingPolicy">The <see cref="IndexingPolicy"/> to use.</param>
    /// <param name="applicationName">The application name to use in requests.</param>
    public AzureCosmosDBNoSQLMemoryStore(
        string connectionString,
        string databaseName,
        VectorEmbeddingPolicy vectorEmbeddingPolicy,
        IndexingPolicy indexingPolicy,
        string? applicationName = null)
    {
        var options = new CosmosClientOptions
        {
            ApplicationName = applicationName ?? HttpHeaderConstant.Values.UserAgent,
        };
        this._cosmosClient = new CosmosClient(connectionString, options);
        this._databaseName = databaseName;
        this._vectorEmbeddingPolicy = vectorEmbeddingPolicy;
        this._indexingPolicy = indexingPolicy;
    }

    /// <summary>
    /// Initiates a AzureCosmosDBNoSQLMemoryStore instance using a <see cref="CosmosClient"/> instance
    /// and other properties required for vector search.
    /// </summary>
    public AzureCosmosDBNoSQLMemoryStore(
        CosmosClient cosmosClient,
        string databaseName,
        VectorEmbeddingPolicy vectorEmbeddingPolicy,
        IndexingPolicy indexingPolicy,
        string? applicationName = null)
    {
        this._cosmosClient = cosmosClient;
        this._cosmosClient.ClientOptions.ApplicationName = applicationName;
        this._databaseName = databaseName;
        this._vectorEmbeddingPolicy = vectorEmbeddingPolicy;
        this._indexingPolicy = indexingPolicy;
    }

    /// <inheritdoc/>
    public async Task CreateCollectionAsync(
        string collectionName,
        CancellationToken cancellationToken = default)
    {
        var databaseResponse = await this._cosmosClient.CreateDatabaseAsync(
            this._databaseName, cancellationToken: cancellationToken).ConfigureAwait(false);

        var containerProperties = new ContainerProperties(collectionName, "id")
        {
            VectorEmbeddingPolicy = this._vectorEmbeddingPolicy,
            IndexingPolicy = this._indexingPolicy,
        };
        var containerResponse = databaseResponse.Database.CreateContainerAsync(
            containerProperties,
            cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> GetCollectionsAsync(
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using var feedIterator = this.
            _cosmosClient
            .GetDatabase(this._databaseName)
            .GetContainerQueryIterator<string>("SELECT c.Id FROM c");

        while (feedIterator.HasMoreResults)
        {
            var next = await feedIterator.ReadNextAsync(cancellationToken).ConfigureAwait(false);
            foreach (var containerName in next.Resource)
            {
                yield return containerName;
            }
        }
    }

    /// <inheritdoc/>
    public async Task<bool> DoesCollectionExistAsync(
        string collectionName,
        CancellationToken cancellationToken = default)
    {
        await foreach (
            var existingCollectionName in this.GetCollectionsAsync(cancellationToken)
                .ConfigureAwait(false)
        )
        {
            if (existingCollectionName == collectionName)
            {
                return true;
            }
        }
        return false;
    }

    /// <inheritdoc/>
    public Task DeleteCollectionAsync(
        string collectionName,
        CancellationToken cancellationToken = default)
    {
        return this._cosmosClient
            .GetDatabase(this._databaseName)
            .GetContainer(collectionName)
            .DeleteContainerAsync(cancellationToken: cancellationToken);
    }

    /// <inheritdoc/>
    public async Task<string> UpsertAsync(
        string collectionName,
        MemoryRecord record,
        CancellationToken cancellationToken = default)
    {
        var result = await this._cosmosClient
            .GetDatabase(this._databaseName)
            .GetContainer(collectionName)
            .UpsertItemAsync(record, cancellationToken: cancellationToken)
            .ConfigureAwait(false);

        return record.Key;
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> UpsertBatchAsync(
        string collectionName,
        IEnumerable<MemoryRecord> records,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        foreach (var record in records)
        {
            yield return await this.UpsertAsync(collectionName, record, cancellationToken)
                .ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public async Task<MemoryRecord?> GetAsync(
        string collectionName,
        string key,
        bool withEmbedding = false,
        CancellationToken cancellationToken = default)
    {
        var result = await this._cosmosClient
         .GetDatabase(this._databaseName)
         .GetContainer(collectionName)
         .ReadItemAsync<MemoryRecord>(key, new PartitionKey(key), cancellationToken: cancellationToken)
         .ConfigureAwait(false);

        return result.Resource;
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(
        string collectionName,
        IEnumerable<string> keys,
        bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var items = keys.Select(k => (k, new PartitionKey(k))).ToList();
        var feedResponse = await this._cosmosClient
            .GetDatabase(this._databaseName)
            .GetContainer(collectionName)
            .ReadManyItemsAsync<MemoryRecord>(items, cancellationToken: cancellationToken)
            .ConfigureAwait(false);

        foreach (var item in feedResponse.Resource)
        {
            yield return item;
        }
    }

    /// <inheritdoc/>
    public async Task RemoveAsync(
        string collectionName,
        string key,
        CancellationToken cancellationToken = default)
    {
        var response = await this._cosmosClient
            .GetDatabase(this._databaseName)
            .GetContainer(collectionName)
            .DeleteItemAsync<MemoryRecord>(key, new PartitionKey(key), cancellationToken: cancellationToken)
            .ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task RemoveBatchAsync(
        string collectionName,
        IEnumerable<string> keys,
        CancellationToken cancellationToken = default)
    {
        foreach (var key in keys)
        {
            var response = await this._cosmosClient
                .GetDatabase(this._databaseName)
                .GetContainer(collectionName)
                .DeleteItemAsync<MemoryRecord>(key, new PartitionKey(key), cancellationToken: cancellationToken)
                .ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(
        string collectionName,
        ReadOnlyMemory<float> embedding,
        double minRelevanceScore = 0,
        bool withEmbedding = false,
        CancellationToken cancellationToken = default)
    {
        await foreach (var item in this.GetNearestMatchesAsync(collectionName, embedding, limit: 1, minRelevanceScore, withEmbedding, cancellationToken).ConfigureAwait(false))
        {
            return item;
        }

        return null;
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(
        string collectionName,
        ReadOnlyMemory<float> embedding,
        int limit,
        double minRelevanceScore = 0,
        bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var queryDefinition = new QueryDefinition("""
            SELECT x, VectorSimilarity(x.Embedding, @embedding)  AS SimilarityScore
            FROM x
            ORDER BY VectorSimilarity(x.Embedding, @embedding)
            WHERE SimilarityScore >= @minRelevanceScore
            TOP @limit
            """);
        queryDefinition.WithParameter("embedding", embedding);
        queryDefinition.WithParameter("limit", limit);
        queryDefinition.WithParameter("minRelevanceScore", minRelevanceScore);

        var feedIterator = this._cosmosClient
         .GetDatabase(this._databaseName)
         .GetContainer(collectionName)
         .GetItemQueryIterator<MemoryRecord>(queryDefinition);

        while (feedIterator.HasMoreResults)
        {
            foreach (var memoryRecord in await feedIterator.ReadNextAsync(cancellationToken).ConfigureAwait(false))
            {
                // TODO: Get the similarity score out too.
                yield return (memoryRecord, 0.0);
            }
        }
    }

    /// <summary>
    /// Disposes the <see cref="AzureCosmosDBNoSQLMemoryStore"/> instance.
    /// </summary>
    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    /// <summary>
    /// Disposes the resources used by the <see cref="AzureCosmosDBNoSQLMemoryStore"/> instance.
    /// </summary>
    /// <param name="disposing">True to release both managed and unmanaged resources; false to release only unmanaged resources.</param>
    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._cosmosClient.Dispose();
        }
    }
}
