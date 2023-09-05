// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using DuckDB.NET.Data;
using Microsoft.SemanticKernel.AI.Embeddings.VectorOperations;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.Memory.DuckDB;

/// <summary>
/// An implementation of <see cref="IMemoryStore"/> backed by a DuckDB database.
/// </summary>
/// <remarks>The data is saved to a database file, specified in the constructor.
/// The data persists between subsequent instances. Only one instance may access the file at a time.
/// The caller is responsible for deleting the file.</remarks>
public class DuckDBMemoryStore : IMemoryStore, IDisposable
{
    /// <summary>
    /// Connect a DuckDB database
    /// </summary>
    /// <param name="filename">Path to the database file. If file does not exist, it will be created.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public static async Task<DuckDBMemoryStore> ConnectAsync(string filename,
        CancellationToken cancellationToken = default)
    {
        var memoryStore = new DuckDBMemoryStore($"Data Source={filename}");
        return await InitialiseMemoryStoreAsync(memoryStore, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Connect a in memory DuckDB database
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public static async Task<DuckDBMemoryStore> ConnectAsync(
        CancellationToken cancellationToken = default)
    {
        var memoryStore = new DuckDBMemoryStore(":memory:");
        return await InitialiseMemoryStoreAsync(memoryStore, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Connect a in memory DuckDB database
    /// </summary>
    /// <param name="connection">An already established connection.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public static async Task<DuckDBMemoryStore> ConnectAsync(DuckDBConnection connection,
        CancellationToken cancellationToken = default)
    {
        var memoryStore = new DuckDBMemoryStore(connection);
        return await InitialiseMemoryStoreAsync(memoryStore, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        await this._dbConnector.CreateCollectionAsync(this._dbConnection, collectionName, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        return await this._dbConnector.DoesCollectionExistsAsync(this._dbConnection, collectionName, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> GetCollectionsAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (var collection in this._dbConnector.GetCollectionsAsync(this._dbConnection, cancellationToken))
        {
            yield return collection;
        }
    }

    /// <inheritdoc/>
    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        await this._dbConnector.DeleteCollectionAsync(this._dbConnection, collectionName, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken = default)
    {
        return await this.InternalUpsertAsync(this._dbConnection, collectionName, record, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        foreach (var record in records)
        {
            yield return await this.InternalUpsertAsync(this._dbConnection, collectionName, record, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public async Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
        return await this.InternalGetAsync(this._dbConnection, collectionName, key, withEmbedding, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        foreach (var key in keys)
        {
            var result = await this.InternalGetAsync(this._dbConnection, collectionName, key, withEmbeddings, cancellationToken).ConfigureAwait(false);
            if (result != null)
            {
                yield return result;
            }
            else
            {
                yield break;
            }
        }
    }

    /// <inheritdoc/>
    public async Task RemoveAsync(string collectionName, string key, CancellationToken cancellationToken = default)
    {
        await this._dbConnector.DeleteAsync(this._dbConnection, collectionName, key, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        await Task.WhenAll(keys.Select(k => this._dbConnector.DeleteAsync(this._dbConnection, collectionName, k, cancellationToken))).ConfigureAwait(false);
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
        if (limit <= 0)
        {
            yield break;
        }

        var collectionMemories = new List<MemoryRecord>();
        List<(MemoryRecord, double)> embeddings = new();

        await foreach (var record in this.GetAllAsync(collectionName, cancellationToken))
        {
            if (record != null)
            {
                double similarity = embedding
                    .Span
                    .CosineSimilarity(record.Embedding.Span);
                if (similarity >= minRelevanceScore)
                {
                    var entry = withEmbeddings ? record : MemoryRecord.FromMetadata(record.Metadata, ReadOnlyMemory<float>.Empty, record.Key, record.Timestamp);
                    embeddings.Add(new(entry, similarity));
                }
            }
        }

        foreach (var item in embeddings.OrderByDescending(l => l.Item2).Take(limit))
        {
            yield return (item.Item1, item.Item2);
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
            cancellationToken: cancellationToken).FirstOrDefaultAsync(cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    #region protected ================================================================================

    protected virtual void Dispose(bool disposing)
    {
        if (!this._disposedValue)
        {
            if (disposing)
            {
                this._dbConnection.Close();
                this._dbConnection.Dispose();
            }

            this._disposedValue = true;
        }
    }

    #endregion

    #region private ================================================================================

    private readonly Database _dbConnector;
    private readonly DuckDBConnection _dbConnection;
    private bool _disposedValue;

    private static async Task<DuckDBMemoryStore> InitialiseMemoryStoreAsync(DuckDBMemoryStore memoryStore, CancellationToken cancellationToken = default)
    {
        await memoryStore._dbConnection.OpenAsync(cancellationToken).ConfigureAwait(false);
        await memoryStore._dbConnector.CreateTableAsync(memoryStore._dbConnection, cancellationToken).ConfigureAwait(false);
        return memoryStore;
    }

    /// <summary>
    /// Constructor
    /// </summary>
    /// <param name="filename">DuckDB db filename.</param>
    private DuckDBMemoryStore(string filename)
    {
        this._dbConnector = new Database();
        this._dbConnection = new DuckDBConnection($"Data Source={filename};");
        this._disposedValue = false;
    }

    /// <summary>
    /// Constructor
    /// </summary>
    private DuckDBMemoryStore()
    {
        this._dbConnector = new Database();
        this._dbConnection = new DuckDBConnection("Data Source=:memory:;");
        this._disposedValue = false;
    }

    /// <summary>
    /// Constructor
    /// </summary>
    /// <param name="connection"></param>
    private DuckDBMemoryStore(DuckDBConnection connection)
    {
        this._dbConnector = new Database();
        this._dbConnection = connection;
        this._disposedValue = false;
    }

    private static string? ToTimestampString(DateTimeOffset? timestamp)
    {
        return timestamp?.ToString("u", CultureInfo.InvariantCulture);
    }

    private static DateTimeOffset? ParseTimestamp(string? str)
    {
        if (!string.IsNullOrEmpty(str)
            && DateTimeOffset.TryParse(str, CultureInfo.InvariantCulture, DateTimeStyles.AssumeUniversal, out DateTimeOffset timestamp))
        {
            return timestamp;
        }

        return null;
    }

    private async IAsyncEnumerable<MemoryRecord> GetAllAsync(string collectionName, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        // delete empty entry in the database if it exists (see CreateCollection)
        await this._dbConnector.DeleteEmptyAsync(this._dbConnection, collectionName, cancellationToken).ConfigureAwait(false);

        await foreach (DatabaseEntry dbEntry in this._dbConnector.ReadAllAsync(this._dbConnection, collectionName, cancellationToken))
        {
            var dbEntryEmbeddingString = dbEntry.EmbeddingString;
            ReadOnlyMemory<float> vector = JsonSerializer.Deserialize<ReadOnlyMemory<float>>(dbEntryEmbeddingString, s_jsonSerializerOptions);

            var record = MemoryRecord.FromJsonMetadata(dbEntry.MetadataString, vector, dbEntry.Key, ParseTimestamp(dbEntry.Timestamp));

            yield return record;
        }
    }

    private async Task<string> InternalUpsertAsync(DuckDBConnection connection, string collectionName, MemoryRecord record, CancellationToken cancellationToken)
    {
        record.Key = record.Metadata.Id;

        await this._dbConnector.UpdateOrInsertAsync(conn: connection,
            collection: collectionName,
            key: record.Key,
            metadata: record.GetSerializedMetadata(),
            embedding: JsonSerializer.Serialize(record.Embedding, s_jsonSerializerOptions),
            timestamp: ToTimestampString(record.Timestamp),
            cancellationToken: cancellationToken).ConfigureAwait(false);

        return record.Key;
    }

    private async Task<MemoryRecord?> InternalGetAsync(
        DuckDBConnection connection,
        string collectionName,
        string key, bool withEmbedding,
        CancellationToken cancellationToken)
    {
        DatabaseEntry? entry = await this._dbConnector.ReadAsync(connection, collectionName, key, cancellationToken).ConfigureAwait(false);

        if (!entry.HasValue) { return null; }

        if (withEmbedding)
        {
            return MemoryRecord.FromJsonMetadata(
                json: entry.Value.MetadataString,
                JsonSerializer.Deserialize<ReadOnlyMemory<float>>(entry.Value.EmbeddingString, s_jsonSerializerOptions),
                entry.Value.Key,
                ParseTimestamp(entry.Value.Timestamp));
        }

        return MemoryRecord.FromJsonMetadata(
            json: entry.Value.MetadataString,
            ReadOnlyMemory<float>.Empty,
            entry.Value.Key,
            ParseTimestamp(entry.Value.Timestamp));
    }

    private static readonly JsonSerializerOptions s_jsonSerializerOptions = CreateSerializerOptions();

    private static JsonSerializerOptions CreateSerializerOptions()
    {
        var jso = new JsonSerializerOptions();
        jso.Converters.Add(new ReadOnlyMemoryConverter());
        return jso;
    }

    #endregion
}
