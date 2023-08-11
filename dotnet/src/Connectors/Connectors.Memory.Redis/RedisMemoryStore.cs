// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Memory;
using NRedisStack;
using NRedisStack.RedisStackCommands;
using NRedisStack.Search;
using NRedisStack.Search.Literals.Enums;
using StackExchange.Redis;

namespace Microsoft.SemanticKernel.Connectors.Memory.Redis;

/// <summary>
/// An implementation of <see cref="IMemoryStore"/> for Redis.
/// </summary>
/// <remarks>The embedded data is saved to the Redis server database specified in the constructor.
/// Similarity search capability is provided through the RediSearch module. Use RediSearch's "Index" to implement "Collection".
/// </remarks>
public sealed class RedisMemoryStore : IMemoryStore
{
    /// <summary>
    /// Create a new instance of semantic memory using Redis.
    /// </summary>
    /// <param name="database">The database of the redis server.</param>
    /// <param name="vectorSize">Embedding vector size</param>
    public RedisMemoryStore(IDatabase database, int vectorSize)
    {
        this._database = database;
        this._vectorSize = vectorSize;
        this._ft = database.FT();
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> GetCollectionsAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        foreach (var index in await this._ft._ListAsync().ConfigureAwait(false))
        {
            yield return ((string)index!);
        }
    }

    /// <inheritdoc />
    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        FTCreateParams ftCreateParams = FTCreateParams.CreateParams().On(IndexDataType.HASH).Prefix($"{collectionName}:");
        Schema schema = new Schema()
            .AddTextField("key")
            .AddTextField("metadata")
            .AddNumericField("timestamp")
            .AddVectorField("embedding", VECTOR_INDEX_ALGORITHM, new Dictionary<string, object> {
                    {"TYPE", VECTOR_TYPE},
                    {"DIM", this._vectorSize},
                    {"DISTANCE_METRIC", VECTOR_DISTANCE_METRIC},
                });

        await this._ft.CreateAsync(collectionName, ftCreateParams, schema).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        try
        {
            await this._ft.InfoAsync(collectionName).ConfigureAwait(false);
            return true;
        }
        catch (RedisServerException ex) when (ex.Message == MESSAGE_WHEN_INDEX_DOES_NOT_EXIST)
        {
            return false;
        }
    }

    /// <inheritdoc />
    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        // dd: If `true`, all documents will be deleted.
        await this._ft.DropIndexAsync(collectionName, dd: true).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
        return await this.InternalGetAsync(collectionName, key, withEmbedding, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        foreach (var key in keys)
        {
            var result = await this.InternalGetAsync(collectionName, key, withEmbeddings, cancellationToken).ConfigureAwait(false);
            if (result != null)
            {
                yield return result;
            }
        }
    }

    /// <inheritdoc />
    public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken = default)
    {
        record.Key = record.Metadata.Id;

        await this._database.HashSetAsync(GetRedisKey(collectionName, record.Key), new[] {
            new HashEntry("key", record.Key),
            new HashEntry("metadata", record.GetSerializedMetadata()),
            new HashEntry("embedding", MemoryMarshal.AsBytes(record.Embedding.Span).ToArray()),
            new HashEntry("timestamp", ToTimestampLong(record.Timestamp))
        }, flags: CommandFlags.None).ConfigureAwait(false);

        return record.Key;
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        foreach (var record in records)
        {
            yield return await this.UpsertAsync(collectionName, record, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc />
    public async Task RemoveAsync(string collectionName, string key, CancellationToken cancellationToken = default)
    {
        await this._database.KeyDeleteAsync(GetRedisKey(collectionName, key), flags: CommandFlags.None).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        await this._database.KeyDeleteAsync(keys.Select(key => GetRedisKey(collectionName, key)).ToArray(), flags: CommandFlags.None).ConfigureAwait(false);
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
        if (limit <= 0)
        {
            yield break;
        }

        var query = new Query($"*=>[KNN {limit} @embedding $embedding AS vector_score]")
                    .AddParam("embedding", MemoryMarshal.AsBytes(embedding.Span).ToArray())
                    .SetSortBy("vector_score")
                    .ReturnFields("key", "metadata", "embedding", "timestamp", "vector_score")
                    .Limit(0, limit)
                    .Dialect(QUERY_DIALECT);

        var results = await this._ft.SearchAsync(collectionName, query).ConfigureAwait(false);

        foreach (var document in results.Documents)
        {
            double similarity = this.GetSimilarity(document);
            if (similarity < minRelevanceScore)
            {
                yield break;
            }

            ReadOnlyMemory<float> convertedEmbedding = withEmbeddings && document["embedding"].HasValue
                ?
                MemoryMarshal.Cast<byte, float>((byte[])document["embedding"]!).ToArray()
                :
                ReadOnlyMemory<float>.Empty;

            yield return (MemoryRecord.FromJsonMetadata(
                    json: document["metadata"]!,
                    embedding: convertedEmbedding,
                    key: document["key"],
                    timestamp: ParseTimestamp((long?)document["timestamp"])), similarity);
        }
    }

    /// <inheritdoc/>
    public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(string collectionName, ReadOnlyMemory<float> embedding, double minRelevanceScore = 0, bool withEmbedding = false,
        CancellationToken cancellationToken = default)
    {
        return await this.GetNearestMatchesAsync(
            collectionName: collectionName,
            embedding: embedding,
            limit: 1,
            minRelevanceScore: minRelevanceScore,
            withEmbeddings: withEmbedding,
            cancellationToken: cancellationToken).FirstOrDefaultAsync(cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    #region constants  ================================================================================

    /// <summary>
    /// Vector similarity index algorithm. The default value is "HNSW".
    /// <see href="https://redis.io/docs/stack/search/reference/vectors/#create-a-vector-field"/>
    /// </summary>
    internal const Schema.VectorField.VectorAlgo VECTOR_INDEX_ALGORITHM = Schema.VectorField.VectorAlgo.HNSW;

    /// <summary>
    /// Vector type. Supported types are FLOAT32 and FLOAT64. The default value is "FLOAT32".
    /// </summary>
    internal const string VECTOR_TYPE = "FLOAT32";

    /// <summary>
    /// Supported distance metric, one of {L2, IP, COSINE}. The default value is "COSINE".
    /// </summary>
    internal const string VECTOR_DISTANCE_METRIC = "COSINE";

    /// <summary>
    /// Query dialect. To use a vector similarity query, specify DIALECT 2 or higher. The default value is "2".
    /// <see href="https://redis.io/docs/stack/search/reference/vectors/#querying-vector-fields"/>
    /// </summary>
    internal const int QUERY_DIALECT = 2;

    /// <summary>
    /// Message when index does not exist.
    /// <see href="https://github.com/RediSearch/RediSearch/blob/master/src/info_command.c#L96"/>
    /// </summary>
    internal const string MESSAGE_WHEN_INDEX_DOES_NOT_EXIST = "Unknown Index name";

    #endregion

    #region private ================================================================================

    private readonly IDatabase _database;
    private readonly int _vectorSize;
    private readonly SearchCommands _ft;

    private static long ToTimestampLong(DateTimeOffset? timestamp)
    {
        if (timestamp.HasValue)
        {
            return timestamp.Value.ToUnixTimeMilliseconds();
        }
        return -1;
    }

    private static DateTimeOffset? ParseTimestamp(long? timestamp)
    {
        if (timestamp.HasValue && timestamp > 0)
        {
            return DateTimeOffset.FromUnixTimeMilliseconds(timestamp.Value);
        }

        return null;
    }

    private static RedisKey GetRedisKey(string collectionName, string key)
    {
        return new RedisKey($"{collectionName}:{key}");
    }

    private async Task<MemoryRecord?> InternalGetAsync(string collectionName, string key, bool withEmbedding, CancellationToken cancellationToken)
    {
        HashEntry[] hashEntries = await this._database.HashGetAllAsync(GetRedisKey(collectionName, key), flags: CommandFlags.None).ConfigureAwait(false);

        if (hashEntries.Length == 0) { return null; }

        if (withEmbedding)
        {
            RedisValue embedding = hashEntries.FirstOrDefault(x => x.Name == "embedding").Value;
            return MemoryRecord.FromJsonMetadata(
                json: hashEntries.FirstOrDefault(x => x.Name == "metadata").Value!,
                embedding: embedding.HasValue ? MemoryMarshal.Cast<byte, float>((byte[])embedding!).ToArray() : ReadOnlyMemory<float>.Empty,
                key: hashEntries.FirstOrDefault(x => x.Name == "key").Value,
                timestamp: ParseTimestamp((long?)hashEntries.FirstOrDefault(x => x.Name == "timestamp").Value));
        }

        return MemoryRecord.FromJsonMetadata(
            json: hashEntries.FirstOrDefault(x => x.Name == "metadata").Value!,
            embedding: ReadOnlyMemory<float>.Empty,
            key: hashEntries.FirstOrDefault(x => x.Name == "key").Value,
            timestamp: ParseTimestamp((long?)hashEntries.FirstOrDefault(x => x.Name == "timestamp").Value));
    }

    private double GetSimilarity(Document document)
    {
        RedisValue vectorScoreValue = document["vector_score"];

        if (vectorScoreValue.IsNullOrEmpty || !vectorScoreValue.TryParse(out double vectorScore))
        {
            throw new SKException("Invalid or missing vector score value.");
        }

        return 1 - vectorScore;
    }

    #endregion
}
