// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Memory;
using NRedisStack;
using NRedisStack.RedisStackCommands;
using NRedisStack.Search;
using NRedisStack.Search.Literals.Enums;
using StackExchange.Redis;
using static NRedisStack.Search.Schema.VectorField;

namespace Microsoft.SemanticKernel.Connectors.Redis;

#pragma warning disable SKEXP0001 // IMemoryStore is experimental (but we're obsoleting)

/// <summary>
/// An implementation of <see cref="IMemoryStore"/> for Redis.
/// </summary>
/// <remarks>The embedded data is saved to the Redis server database specified in the constructor.
/// Similarity search capability is provided through the RediSearch module. Use RediSearch's "Index" to implement "Collection".
/// </remarks>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and RedisVectorStore")]
public class RedisMemoryStore : IMemoryStore, IDisposable
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
        int vectorSize = DefaultVectorSize,
        VectorAlgo vectorIndexAlgorithm = DefaultIndexAlgorithm,
        VectorDistanceMetric vectorDistanceMetric = DefaultDistanceMetric,
        int queryDialect = DefaultQueryDialect)
    {
        if (vectorSize <= 0)
        {
            throw new ArgumentException(
                $"Invalid vector size: {vectorSize}. Vector size must be a positive integer.", nameof(vectorSize));
        }

        this._database = database;
        this._vectorSize = vectorSize;
        this._ft = database.FT();
        this._vectorIndexAlgorithm = vectorIndexAlgorithm;
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
        int vectorSize = DefaultVectorSize,
        VectorAlgo vectorIndexAlgorithm = DefaultIndexAlgorithm,
        VectorDistanceMetric vectorDistanceMetric = DefaultDistanceMetric,
        int queryDialect = DefaultQueryDialect)
    {
        if (vectorSize <= 0)
        {
            throw new ArgumentException(
                $"Invalid vector size: {vectorSize}. Vector size must be a positive integer.", nameof(vectorSize));
        }

        this._connection = ConnectionMultiplexer.Connect(connectionString);
        this._database = this._connection.GetDatabase();
        this._vectorSize = vectorSize;
        this._ft = this._database.FT();
        this._vectorIndexAlgorithm = vectorIndexAlgorithm;
        this._vectorDistanceMetric = vectorDistanceMetric.ToString();
        this._queryDialect = queryDialect;
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
            .AddVectorField("embedding", this._vectorIndexAlgorithm, new Dictionary<string, object> {
                    {"TYPE", DefaultVectorType},
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
        catch (RedisServerException ex) when (ex.Message.Equals(IndexDoesNotExistErrorMessage, StringComparison.OrdinalIgnoreCase))
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
            if (result is not null)
            {
                yield return result;
            }
        }
    }

    /// <inheritdoc />
    public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken = default)
    {
        record.Key = record.Metadata.Id;

        await this._database.HashSetAsync(GetRedisKey(collectionName, record.Key), [
            new HashEntry("key", record.Key),
            new HashEntry("metadata", record.GetSerializedMetadata()),
            new HashEntry("embedding", this.ConvertEmbeddingToBytes(record.Embedding)),
            new HashEntry("timestamp", ToTimestampLong(record.Timestamp))
        ], flags: CommandFlags.None).ConfigureAwait(false);

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

    /// <summary>
    /// Disposes the <see cref="RedisMemoryStore"/> instance.
    /// </summary>
    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    /// <summary>
    /// Disposes the resources used by the <see cref="RedisMemoryStore"/> instance.
    /// </summary>
    /// <param name="disposing">True to release both managed and unmanaged resources; false to release only unmanaged resources.</param>
    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._connection?.Dispose();
        }
    }

    #region private ================================================================================

    /// <summary>
    /// Vector similarity index algorithm. Supported algorithms are {FLAT, HNSW}. The default value is "HNSW".
    /// <see href="https://redis.io/docs/interact/search-and-query/search/vectors/#create-a-vector-field"/>
    /// </summary>
    private const VectorAlgo DefaultIndexAlgorithm = VectorAlgo.HNSW;

    /// <summary>
    /// Vector type. Available values are {FLOAT32, FLOAT64}.
    /// Value "FLOAT32" is used by default based on <see cref="MemoryRecord.Embedding"/> <see cref="float"/> type.
    /// </summary>
    private const string DefaultVectorType = "FLOAT32";

    /// <summary>
    /// Supported distance metrics are {L2, IP, COSINE}. The default value is "COSINE".
    /// </summary>
    private const VectorDistanceMetric DefaultDistanceMetric = VectorDistanceMetric.COSINE;

    /// <summary>
    /// Query dialect. To use a vector similarity query, specify DIALECT 2 or higher. The default value is "2".
    /// <see href="https://redis.io/docs/interact/search-and-query/search/vectors/#querying-vector-fields"/>
    /// </summary>
    private const int DefaultQueryDialect = 2;

    /// <summary>
    /// Embedding vector size.
    /// </summary>
    private const int DefaultVectorSize = 1536;

    /// <summary>
    /// Message when index does not exist.
    /// <see href="https://github.com/RediSearch/RediSearch/blob/master/src/info_command.c#L97"/>
    /// </summary>
    private const string IndexDoesNotExistErrorMessage = "Unknown index name";

    private readonly IDatabase _database;
    private readonly int _vectorSize;
    private readonly SearchCommands _ft;
    private readonly ConnectionMultiplexer? _connection;
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
        cancellationToken.ThrowIfCancellationRequested();

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
            throw new KernelException("Invalid or missing vector score value.");
        }

        return 1 - vectorScore;
    }

    private byte[] ConvertEmbeddingToBytes(ReadOnlyMemory<float> embedding)
    {
        return MemoryMarshal.AsBytes(embedding.Span).ToArray();
    }

    #endregion
}
