// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Azure.Cosmos;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Memory;

#if NET6_0_OR_GREATER
using System.Globalization;
#endif

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
    /// <param name="vectorEmbeddingPolicy">The <see cref="VectorEmbeddingPolicy" /> to use if a collection is created. NOTE that embeddings will be stored in a property named 'embedding'.</param>
    /// <param name="indexingPolicy">The <see cref="IndexingPolicy"/> to use if a collection is created. NOTE that embeddings will be stored in a property named 'embedding'.</param>
    /// <param name="applicationName">The application name to use in requests.</param>
    public AzureCosmosDBNoSQLMemoryStore(
        string connectionString,
        string databaseName,
        VectorEmbeddingPolicy vectorEmbeddingPolicy,
        IndexingPolicy indexingPolicy,
        string? applicationName = null)
        : this(
            new CosmosClient(
                connectionString,
                new CosmosClientOptions
                {
                    ApplicationName = applicationName ?? HttpHeaderConstant.Values.UserAgent,
                    Serializer = new CosmosSystemTextJsonSerializer(JsonSerializerOptions.Default),
                }),
            databaseName,
            vectorEmbeddingPolicy,
            indexingPolicy,
            applicationName)
    {
    }

    /// <summary>
    /// Initiates a AzureCosmosDBNoSQLMemoryStore instance using a <see cref="CosmosClient"/> instance
    /// and other properties required for vector search.
    /// </summary>
    /// <param name="cosmosClient">An existing <see cref="CosmosClient"/> to use. NOTE: This must support serializing with
    /// System.Text.Json, not the default Cosmos serializer.</param>
    /// <param name="databaseName">The database name to operate against.</param>
    /// <param name="vectorEmbeddingPolicy">The <see cref="VectorEmbeddingPolicy" /> to use if a collection is created. NOTE that embeddings will be stored in a property named 'embedding'.</param>
    /// <param name="indexingPolicy">The <see cref="IndexingPolicy"/> to use if a collection is created. NOTE that embeddings will be stored in a property named 'embedding'.</param>
    /// <param name="applicationName">The application name to use in requests.</param>
    public AzureCosmosDBNoSQLMemoryStore(
        CosmosClient cosmosClient,
        string databaseName,
        VectorEmbeddingPolicy vectorEmbeddingPolicy,
        IndexingPolicy indexingPolicy,
        string? applicationName = null)
    {
        if (!vectorEmbeddingPolicy.Embeddings.Any(e => e.Path == "/embedding"))
        {
            throw new InvalidOperationException($"""
                In order for {nameof(GetNearestMatchAsync)} to function, {nameof(vectorEmbeddingPolicy)} should
                contain an embedding path at /embedding. It's also recommended to include a that path in the
                {nameof(indexingPolicy)} to improve performance and reduce cost for searches.
                """);
        }
        this._cosmosClient = cosmosClient;
        this._databaseName = databaseName;
        this._vectorEmbeddingPolicy = vectorEmbeddingPolicy;
        this._indexingPolicy = indexingPolicy;

        if (!string.IsNullOrWhiteSpace(applicationName))
        {
            this._cosmosClient.ClientOptions.ApplicationName = applicationName;
        }
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
            .UpsertItemAsync(new MemoryRecordWithId(record), new PartitionKey(record.Key), cancellationToken: cancellationToken)
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
        const string OR = " OR ";

        // Optimistically create the entire query string.
        var whereClause = string.Join(OR, keys.Select(k => $"(x.id = \"{k}\" AND x.key = \"{k}\")"));
        var queryDefinition = new QueryDefinition($"""
            SELECT x.id,x.key,x.metadata,x.timestamp{(withEmbeddings ? ",x.embedding" : "")}
            FROM x
            WHERE {whereClause}
            """);

        // NOTE: Cosmos DB queries are limited to 512kB, so if this is larger than that, break it into segments.
        var byteCount = Encoding.UTF8.GetByteCount(whereClause);
        var ratio = byteCount / ((float)(512 * 1024));
        if (ratio < 1)
        {
            var feedIterator = this._cosmosClient
                .GetDatabase(this._databaseName)
                .GetContainer(collectionName)
                .GetItemQueryIterator<MemoryRecord>(queryDefinition);

            while (feedIterator.HasMoreResults)
            {
                foreach (var memoryRecord in await feedIterator.ReadNextAsync(cancellationToken).ConfigureAwait(false))
                {
                    yield return memoryRecord;
                }
            }
        }
        else
        {
            // We're in the very large case, we'll need to split this into multiple queries.
            // We add one to catch any fractional piece left in the last segment
            var segments = (int)(ratio + 1);
            var keyList = keys.ToList();
            var keysPerQuery = keyList.Count / segments;
            // Make a guess as to how long this query will be. We need at least 26 chars for each "OR" block, so
            // put a few extra for the values of the keys.
            var estimatedWhereLength = 30 * keysPerQuery;
            var localWhere = new StringBuilder(estimatedWhereLength);
            for (var i = 0; i < segments; i++)
            {
                localWhere.Clear();
                for (var q = i * keysPerQuery; q < (i + 1) * keysPerQuery && q < keyList.Count; q++)
                {
                    var k = keyList[q];
#if NET6_0_OR_GREATER
                    localWhere.Append(CultureInfo.InvariantCulture, $"(x.id = \"{k}\" AND x.key = \"{k}\")").Append(OR);
#else
                    localWhere.Append($"(x.id = \"{k}\" AND x.key = \"{k}\")").Append(OR);
#endif
                }

                if (localWhere.Length >= OR.Length)
                {
                    localWhere.Length -= OR.Length;

                    var localQueryDefinition = new QueryDefinition($"""
                        SELECT x.id,x.key,x.metadata,x.timestamp{(withEmbeddings ? ",x.embedding" : "")}
                        FROM x
                        WHERE {localWhere}
                        """);
                    var feedIterator = this._cosmosClient
                        .GetDatabase(this._databaseName)
                        .GetContainer(collectionName)
                        .GetItemQueryIterator<MemoryRecord>(localQueryDefinition);

                    while (feedIterator.HasMoreResults)
                    {
                        foreach (var memoryRecord in await feedIterator.ReadNextAsync(cancellationToken).ConfigureAwait(false))
                        {
                            yield return memoryRecord;
                        }
                    }
                }
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
        var queryDefinition = new QueryDefinition($"""
            SELECT TOP @limit x.id,x.key,x.metadata,x.timestamp,{(withEmbeddings ? "x.embedding," : "")}VectorDistance(x.embedding, @embedding) AS SimilarityScore
            FROM x
            ORDER BY VectorDistance(x.embedding, @embedding)
            """);
        queryDefinition.WithParameter("@embedding", embedding);
        queryDefinition.WithParameter("@limit", limit);

        var feedIterator = this._cosmosClient
         .GetDatabase(this._databaseName)
         .GetContainer(collectionName)
         .GetItemQueryIterator<MemoryRecordWithSimilarityScore>(queryDefinition);

        while (feedIterator.HasMoreResults)
        {
            foreach (var memoryRecord in await feedIterator.ReadNextAsync(cancellationToken).ConfigureAwait(false))
            {
                if (memoryRecord.SimilarityScore >= minRelevanceScore)
                {
                    yield return (memoryRecord, memoryRecord.SimilarityScore);
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
[DebuggerDisplay("{GetDebuggerDisplay()}")]
internal class MemoryRecordWithSimilarityScore(
    MemoryRecordMetadata metadata,
    ReadOnlyMemory<float> embedding,
    string? key,
    DateTimeOffset? timestamp = null) : MemoryRecord(metadata, embedding, key, timestamp)
{
    /// <summary>
    /// The similarity score returned.
    /// </summary>
    public double SimilarityScore { get; set; }

    private string GetDebuggerDisplay()
    {
        return $"{this.Key} - {this.SimilarityScore}";
    }
}

/// <summary>
/// Creates a new record that also serializes an "id" property.
/// </summary>
[DebuggerDisplay("{GetDebuggerDisplay()}")]
internal class MemoryRecordWithId : MemoryRecord
{
    /// <summary>
    /// Creates a new record that also serializes an "id" property.
    /// </summary>
    public MemoryRecordWithId(MemoryRecord source)
        : base(source.Metadata, source.Embedding, source.Key, source.Timestamp)
    {
    }

    /// <summary>
    /// Creates a new record that also serializes an "id" property.
    /// </summary>
    [JsonConstructor]
    public MemoryRecordWithId(
        MemoryRecordMetadata metadata,
        ReadOnlyMemory<float> embedding,
        string? key,
        DateTimeOffset? timestamp = null)
        : base(metadata, embedding, key, timestamp)
    {
    }

    /// <summary>
    /// Serializes the <see cref="DataEntryBase.Key"/>property as "id".
    /// We do this because Azure Cosmos DB requires a property named "id" for
    /// each item.
    /// </summary>
    [JsonInclude]
    [JsonPropertyName("id")]
    public string Id => this.Key;

    private string GetDebuggerDisplay()
    {
        return this.Key;
    }
}
