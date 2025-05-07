// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
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

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;

#pragma warning disable SKEXP0001 // IMemoryStore is experimental (but we're obsoleting)

/// <summary>
/// An implementation of <see cref="IMemoryStore"/> backed by a Azure Cosmos DB database.
/// Get more details about Azure Cosmos DB vector search  https://learn.microsoft.com/en-us/azure/cosmos-db/
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and AzureCosmosDBNoSQLVectorStore")]
public class AzureCosmosDBNoSQLMemoryStore : IMemoryStore, IDisposable
{
    private const string EmbeddingPath = "/embedding";

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
    /// <param name="dimensions">The number of dimensions the embedding vectors to be stored.</param>
    /// <param name="vectorDataType">The data type of the embedding vectors to be stored.</param>
    /// <param name="vectorIndexType">The type of index to use for the embedding vectors to be stored.</param>
    /// <param name="applicationName">The application name to use in requests.</param>
    public AzureCosmosDBNoSQLMemoryStore(
        string connectionString,
        string databaseName,
        ulong dimensions,
        VectorDataType vectorDataType,
        VectorIndexType vectorIndexType,
        string? applicationName = null)
        : this(
            new CosmosClient(
                connectionString,
                new CosmosClientOptions
                {
                    ApplicationName = applicationName ?? HttpHeaderConstant.Values.UserAgent,
                    UseSystemTextJsonSerializerWithOptions = JsonSerializerOptions.Default,
                }),
            databaseName,
            new VectorEmbeddingPolicy(
                [
                    new Embedding
                    {
                        DataType = vectorDataType,
                        Dimensions = (int)dimensions,
                        DistanceFunction = DistanceFunction.Cosine,
                        Path = EmbeddingPath,
                    }
                ]),
            new IndexingPolicy
            {
                VectorIndexes = new Collection<VectorIndexPath> {
                    new()
                    {
                        Path = EmbeddingPath,
                        Type = vectorIndexType,
                    },
                },
            })
    {
    }

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
                    UseSystemTextJsonSerializerWithOptions = JsonSerializerOptions.Default,
                }),
            databaseName,
            vectorEmbeddingPolicy,
            indexingPolicy)
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
    public AzureCosmosDBNoSQLMemoryStore(
        CosmosClient cosmosClient,
        string databaseName,
        VectorEmbeddingPolicy vectorEmbeddingPolicy,
        IndexingPolicy indexingPolicy)
    {
        var embedding = vectorEmbeddingPolicy.Embeddings.FirstOrDefault(e => e.Path == EmbeddingPath);
        if (embedding is null)
        {
            throw new InvalidOperationException($"""
                In order for {nameof(GetNearestMatchAsync)} to function, {nameof(vectorEmbeddingPolicy)} should
                contain an embedding path at {EmbeddingPath}. It's also recommended to include that path in the
                {nameof(indexingPolicy)} to improve performance and reduce cost for searches.
                """);
        }
        else if (embedding.DistanceFunction != DistanceFunction.Cosine)
        {
            throw new InvalidOperationException($"""
                In order for {nameof(GetNearestMatchAsync)} to reliably return relevance information, the {nameof(DistanceFunction)} should
                be specified as {nameof(DistanceFunction)}.{nameof(DistanceFunction.Cosine)}.
                """);
        }
        else if (embedding.DataType != VectorDataType.Float32)
        {
            throw new NotSupportedException($"""
                Only {nameof(VectorDataType)}.{nameof(VectorDataType.Float32)}
                are supported.
                """);
        }
        this._cosmosClient = cosmosClient;
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
        var queryDefinition = new QueryDefinition("SELECT VALUE(c.id) FROM c WHERE c.id = @collectionName");
        queryDefinition.WithParameter("@collectionName", collectionName);
        using var feedIterator = this.
            _cosmosClient
            .GetDatabase(this._databaseName)
            .GetContainerQueryIterator<string>(queryDefinition);

        while (feedIterator.HasMoreResults)
        {
            var next = await feedIterator.ReadNextAsync(cancellationToken).ConfigureAwait(false);
            foreach (var containerName in next.Resource)
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
        // In some cases we're expected to generate the key to use. Do so if one isn't provided.
        if (string.IsNullOrEmpty(record.Key))
        {
            record.Key = Guid.NewGuid().ToString();
        }

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
        // TODO: Consider using a query when `withEmbedding` is false to avoid passing it over the wire.
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
        var queryStart = $"""
            SELECT x.id,x.key,x.metadata,x.timestamp{(withEmbeddings ? ",x.embedding" : "")}
            FROM x
            WHERE
            """;
        // NOTE: Cosmos DB queries are limited to 512kB, so we'll break this into chunks
        // of around 500kB. We don't go all the way to 512kB so that we don't have to
        // remove the last clause we added once we go over.
        int keyIndex = 0;
        var keyList = keys.ToList();
        while (keyIndex < keyList.Count)
        {
            var length = queryStart.Length;
            var countThisBatch = 0;
            var whereClauses = new StringBuilder();
            for (int i = keyIndex; i < keyList.Count && length <= 500 * 1024; i++, countThisBatch++)
            {
                string keyId = $"@key{i:D}";
                var clause = $"(x.id = {keyId} AND x.key = {keyId})";
                whereClauses.Append(clause).Append(OR);
                length += clause.Length + OR.Length + 4 + keyId.Length + Encoding.UTF8.GetByteCount(keyList[keyIndex]);
            }
            whereClauses.Length -= OR.Length;

            var queryDefinition = new QueryDefinition(queryStart + whereClauses);
            for (int i = keyIndex; i < keyIndex + countThisBatch; i++)
            {
                queryDefinition.WithParameter($"@key{i:D}", keyList[i]);
            }

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

            keyIndex += countThisBatch;
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
                var relevanceScore = (memoryRecord.SimilarityScore + 1) / 2;
                if (relevanceScore >= minRelevanceScore)
                {
                    yield return (memoryRecord, relevanceScore);
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
#pragma warning disable CA1812 // 'MemoryRecordWithSimilarityScore' is an internal class that is apparently never instantiated. If so, remove the code from the assembly. If this class is intended to contain only static members, make it 'static' (Module in Visual Basic). (https://learn.microsoft.com/dotnet/fundamentals/code-analysis/quality-rules/ca1812)
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and AzureCosmosDBNoSQLVectorStore")]
internal sealed class MemoryRecordWithSimilarityScore(
#pragma warning restore CA1812
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
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and AzureCosmosDBNoSQLVectorStore")]
[DebuggerDisplay("{GetDebuggerDisplay()}")]
internal sealed class MemoryRecordWithId : MemoryRecord
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
