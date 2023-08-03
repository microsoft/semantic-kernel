// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;
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
    /// <param name="database">The database of the Redis server.</param>
    /// <param name="vectorSize">Embedding vector size, defaults to 1536</param>
    /// <param name="vectorIndexAlgorithm">Indexing algorithm for vectors, defaults to "HNSW"</param>
    /// <param name="vectorDistanceMetric">Metric for measuring vector distances, defaults to "COSINE"</param>
    /// <param name="queryDialect">Query dialect, must be 2 or greater for vector similarity searching, defaults to 2</param>
    public RedisMemoryStore(
        IDatabase database,
        int vectorSize = VectorSize,
        VectorIndexAlgorithms vectorIndexAlgorithm = VectorIndexAlgorithm,
        VectorDistanceMetrics vectorDistanceMetric = VectorDistanceMetric,
        int queryDialect = QueryDialect)
    {
        if (vectorSize <= 0)
        {
            throw new ArgumentException("Vector size must be a positive integer.");
        }

        if (!Enum.TryParse<Schema.VectorField.VectorAlgo>(vectorIndexAlgorithm.ToString(), out this._vectorIndexAlgorithm))
        {
            throw new ArgumentException("Unsupported vector indexing algorithm.");
        }

        this._database = database;
        this._vectorSize = vectorSize;
        this._ft = database.FT();
        this._vectorDistanceMetric = vectorDistanceMetric.ToString();
        this._queryDialect = queryDialect;
    }

    /// <summary>
    /// Create a new instance of semantic memory using Redis.
    /// </summary>
    /// <param name="connectionString">Provide connection URL to a Redis instance</param>
    /// <param name="vectorSize">Embedding vector size, defaults to 1536</param>
    /// <param name="vectorIndexAlgorithm">Indexing algorithm for vectors, defaults to "HNSW"</param>
    /// <param name="vectorDistanceMetric">Metric for measuring vector distances, defaults to "COSINE"</param>
    /// <param name="queryDialect">Query dialect, must be 2 or greater for vector similarity searching, defaults to 2</param>
    public RedisMemoryStore(
        string connectionString,
        int vectorSize = VectorSize,
        VectorIndexAlgorithms vectorIndexAlgorithm = VectorIndexAlgorithm,
        VectorDistanceMetrics vectorDistanceMetric = VectorDistanceMetric,
        int queryDialect = QueryDialect)
        : this(ConnectionMultiplexer.Connect(connectionString).GetDatabase(), vectorSize, vectorIndexAlgorithm, vectorDistanceMetric, queryDialect)
    { }

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
            .AddVectorField("embedding", this._vectorIndexAlgorithm, new Dictionary<string, object> {
                    {"TYPE", VectorType},
                    {"DIM", this._vectorSize},
                    {"DISTANCE_METRIC", this._vectorDistanceMetric},
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
        catch (RedisServerException ex) when (ex.Message.Equals(IndexDoesNotExistErrorMessage, StringComparison.Ordinal))
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
            new HashEntry("embedding", this.ConvertEmbeddingToBytes(record.Embedding)),
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
        Embedding<float> embedding,
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
                    .AddParam("embedding", this.ConvertEmbeddingToBytes(embedding))
                    .SetSortBy("vector_score")
                    .ReturnFields("key", "metadata", "embedding", "timestamp", "vector_score")
                    .Limit(0, limit)
                    .Dialect(this._queryDialect);

        var results = await this._ft.SearchAsync(collectionName, query).ConfigureAwait(false);

        foreach (var document in results.Documents)
        {
            double similarity = this.GetSimilarity(document);
            if (similarity < minRelevanceScore)
            {
                yield break;
            }

            Embedding<float> convertedEmbedding = withEmbeddings && document["embedding"].HasValue
                ?
                new Embedding<float>(MemoryMarshal.Cast<byte, float>((byte[])document["embedding"]!).ToArray())
                :
                Embedding<float>.Empty;

            yield return (MemoryRecord.FromJsonMetadata(
                    json: document["metadata"]!,
                    embedding: convertedEmbedding,
                    key: document["key"],
                    timestamp: ParseTimestamp((long?)document["timestamp"])), similarity);
        }
    }

    /// <inheritdoc/>
    public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(string collectionName, Embedding<float> embedding, double minRelevanceScore = 0, bool withEmbedding = false,
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

    #region private ================================================================================

    /// <summary>
    /// Vector similarity index algorithm. Supported algorithms are {FLAT, HNSW}. The default value is "HNSW".
    /// <see href="https://redis.io/docs/interact/search-and-query/search/vectors/#create-a-vector-field"/>
    /// </summary>
    private const VectorIndexAlgorithms VectorIndexAlgorithm = VectorIndexAlgorithms.HNSW;

    /// <summary>
    /// Vector type. Available values are {FLOAT32, FLOAT64}.
    /// Value "FLOAT32" is used by default based on <see cref="MemoryRecord.Embedding"/> <see cref="float"/> type.
    /// </summary>
    private const string VectorType = "FLOAT32";

    /// <summary>
    /// Supported distance metrics are {L2, IP, COSINE}. The default value is "COSINE".
    /// </summary>
    private const VectorDistanceMetrics VectorDistanceMetric = VectorDistanceMetrics.COSINE;

    /// <summary>
    /// Query dialect. To use a vector similarity query, specify DIALECT 2 or higher. The default value is "2".
    /// <see href="https://redis.io/docs/interact/search-and-query/search/vectors/#querying-vector-fields"/>
    /// </summary>
    private const int QueryDialect = 2;

    /// <summary>
    /// Embedding vector size.
    /// </summary>
    private const int VectorSize = 1536;

    /// <summary>
    /// Message when index does not exist.
    /// <see href="https://github.com/RediSearch/RediSearch/blob/master/src/info_command.c#L97"/>
    /// </summary>
    private const string IndexDoesNotExistErrorMessage = "Unknown Index name";

    private readonly IDatabase _database;
    private readonly int _vectorSize;
    private readonly SearchCommands _ft;
    private readonly Schema.VectorField.VectorAlgo _vectorIndexAlgorithm;
    private readonly string _vectorDistanceMetric;
    private readonly int _queryDialect;

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
                embedding: embedding.HasValue ? new Embedding<float>(MemoryMarshal.Cast<byte, float>((byte[])embedding!).ToArray()) : Embedding<float>.Empty,
                key: hashEntries.FirstOrDefault(x => x.Name == "key").Value,
                timestamp: ParseTimestamp((long?)hashEntries.FirstOrDefault(x => x.Name == "timestamp").Value));
        }

        return MemoryRecord.FromJsonMetadata(
            json: hashEntries.FirstOrDefault(x => x.Name == "metadata").Value!,
            embedding: Embedding<float>.Empty,
            key: hashEntries.FirstOrDefault(x => x.Name == "key").Value,
            timestamp: ParseTimestamp((long?)hashEntries.FirstOrDefault(x => x.Name == "timestamp").Value));
    }

    private double GetSimilarity(Document document)
    {
        RedisValue vectorScoreValue = document["vector_score"];

        if (vectorScoreValue.IsNullOrEmpty || !vectorScoreValue.TryParse(out double vectorScore))
        {
            throw new RedisMemoryStoreException("Invalid or missing vector score value.");
        }

        return 1 - vectorScore;
    }

    private byte[] ConvertEmbeddingToBytes(Embedding<float> embedding)
    {
        return MemoryMarshal.Cast<float, byte>(embedding.AsReadOnlySpan()).ToArray();
    }

    #endregion
}
