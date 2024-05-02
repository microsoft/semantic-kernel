// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Azure.Cosmos;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Text;

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
            Serializer = new CosmosSystemTextJsonSerializer(JsonSerializerOptions.Default),
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
        var databaseResponse = await this._cosmosClient.CreateDatabaseIfNotExistsAsync(
            this._databaseName, cancellationToken: cancellationToken).ConfigureAwait(false);

        var containerProperties = new ContainerProperties(collectionName, "/key")
        {
            VectorEmbeddingPolicy = this._vectorEmbeddingPolicy,
            IndexingPolicy = this._indexingPolicy,
        };
        var containerResponse = await databaseResponse.Database.CreateContainerIfNotExistsAsync(
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
            .GetContainerQueryIterator<string>("SELECT VALUE(c.id) FROM c");

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
    public async Task DeleteCollectionAsync(
        string collectionName,
        CancellationToken cancellationToken = default)
    {
        await this._cosmosClient
            .GetDatabase(this._databaseName)
            .GetContainer(collectionName)
            .DeleteContainerAsync(cancellationToken: cancellationToken)
            .ConfigureAwait(false);
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
            .UpsertItemAsync(record, new PartitionKey(record.Key), cancellationToken: cancellationToken)
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
            if (withEmbeddings)
            {
                yield return item;
            }
            else
            {
                // TODO: Consider changing this into a select that doesn't return the embeddings.
                // Is that actually better? RU consumption of query, vs ReadMany and transmission of larger docs.
                yield return new MemoryRecord(item.Metadata, null, item.Key, item.Timestamp);
            }
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
        // It would be nice to "WHERE" on the similarity score to stay above the `minRelevanceScore`, but alas
        // queries don't support that.
        // TODO: Change this to use a `TOP @limit` instead of stopping client side.
        var queryDefinition = new QueryDefinition($"""
            SELECT x.id,x.key,x.metadata,x.timestamp{(withEmbeddings ? ",x.embedding" : "")},VectorDistance(x.embedding, @embedding) AS SimilarityScore
            FROM x
            ORDER BY VectorDistance(x.embedding, @embedding)
            """);
        queryDefinition.WithParameter("@embedding", embedding);
        queryDefinition.WithParameter("@limit", limit);

        var feedIterator = this._cosmosClient
         .GetDatabase(this._databaseName)
         .GetContainer(collectionName)
         .GetItemQueryIterator<MemoryRecordWithSimilarityScore>(queryDefinition);

        var count = 0;
        while (feedIterator.HasMoreResults)
        {
            foreach (var memoryRecord in await feedIterator.ReadNextAsync(cancellationToken).ConfigureAwait(false))
            {
                if (memoryRecord.SimilarityScore >= minRelevanceScore)
                {
                    yield return (memoryRecord, memoryRecord.SimilarityScore);
                    count++;
                    if (count == limit)
                    {
                        yield break;
                    }
                }
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

/// <summary>
/// Creates a new record with a similarity score.
/// </summary>
/// <param name="metadata"></param>
/// <param name="embedding"></param>
/// <param name="key"></param>
/// <param name="timestamp"></param>
public class MemoryRecordWithSimilarityScore(
    MemoryRecordMetadata metadata,
    ReadOnlyMemory<float> embedding,
    string? key,
    DateTimeOffset? timestamp = null) : MemoryRecord(metadata, embedding, key, timestamp)
{
    /// <summary>
    /// The similarity score returned.
    /// </summary>
    public double SimilarityScore { get; set; }
}
