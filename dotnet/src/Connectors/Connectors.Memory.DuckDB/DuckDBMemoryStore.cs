// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using DuckDB.NET.Data;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.DuckDB;

/// <summary>
/// An implementation of <see cref="IMemoryStore"/> backed by a DuckDB database.
/// </summary>
/// <remarks>The data is saved to a database file, specified in the constructor.
/// The data persists between subsequent instances. Only one instance may access the file at a time.
/// The caller is responsible for deleting the file.</remarks>
public sealed class DuckDBMemoryStore : IMemoryStore, IDisposable
{
    /// <summary>
    /// Connect a DuckDB database
    /// </summary>
    /// <param name="filename">Path to the database file. If file does not exist, it will be created.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public static async Task<DuckDBMemoryStore> ConnectAsync(string filename,
        CancellationToken cancellationToken = default)
    {
        var memoryStore = new DuckDBMemoryStore(filename);
        return await InitialiseMemoryStoreAsync(memoryStore, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Connect a in memory DuckDB database
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public static Task<DuckDBMemoryStore> ConnectAsync(
        CancellationToken cancellationToken = default)
    {
        return ConnectAsync(":memory:", cancellationToken);
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
    public Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        return Database.CreateCollectionAsync(this._dbConnection, collectionName, cancellationToken);
    }

    /// <inheritdoc/>
    public Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        return Database.DoesCollectionExistsAsync(this._dbConnection, collectionName, cancellationToken);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> GetCollectionsAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (var collection in Database.GetCollectionsAsync(this._dbConnection, cancellationToken))
        {
            yield return collection;
        }
    }

    /// <inheritdoc/>
    public Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        return Database.DeleteCollectionAsync(this._dbConnection, collectionName, cancellationToken);
    }

    /// <inheritdoc/>
    public Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken = default)
    {
        return InternalUpsertAsync(this._dbConnection, collectionName, record, cancellationToken);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        foreach (var record in records)
        {
            yield return await InternalUpsertAsync(this._dbConnection, collectionName, record, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
        return InternalGetAsync(this._dbConnection, collectionName, key, withEmbedding, cancellationToken);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        foreach (var key in keys)
        {
            var result = await InternalGetAsync(this._dbConnection, collectionName, key, withEmbeddings, cancellationToken).ConfigureAwait(false);
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
    public Task RemoveAsync(string collectionName, string key, CancellationToken cancellationToken = default)
    {
        return Database.DeleteAsync(this._dbConnection, collectionName, key, cancellationToken);
    }

    /// <inheritdoc/>
    public Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        return Task.WhenAll(keys.Select(k => Database.DeleteAsync(this._dbConnection, collectionName, k, cancellationToken)));
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

        List<(MemoryRecord Record, double Score)> embeddings = new();

        await foreach (var dbEntry in Database.GetNearestMatchesAsync(this._dbConnection, collectionName, embedding.ToArray(), limit, minRelevanceScore, cancellationToken))
        {
            var entry = MemoryRecord.FromJsonMetadata(
                json: dbEntry.MetadataString,
                withEmbeddings ? dbEntry.Embedding : Array.Empty<float>(),
                dbEntry.Key,
                ParseTimestamp(dbEntry.Timestamp));
            embeddings.Add(new(entry, dbEntry.Score));
        }

        foreach (var item in embeddings.OrderByDescending(l => l.Score).Take(limit))
        {
            yield return (item.Record, item.Score);
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

    /// <summary>
    /// Disposes the resources used by the <see cref="DuckDBMemoryStore"/> instance.
    /// </summary>
    /// <param name="disposing">True to release both managed and unmanaged resources; false to release only unmanaged resources.</param>
    private void Dispose(bool disposing)
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

    private readonly DuckDBConnection _dbConnection;
    private bool _disposedValue;

    private static async Task<DuckDBMemoryStore> InitialiseMemoryStoreAsync(DuckDBMemoryStore memoryStore, CancellationToken cancellationToken = default)
    {
        await memoryStore._dbConnection.OpenAsync(cancellationToken).ConfigureAwait(false);
        await Database.CreateTableAsync(memoryStore._dbConnection, cancellationToken).ConfigureAwait(false);
        return memoryStore;
    }

    /// <summary>
    /// Constructor
    /// </summary>
    /// <param name="filename">DuckDB db filename.</param>
    private DuckDBMemoryStore(string filename)
    {
        this._dbConnection = new DuckDBConnection($"Data Source={filename};");
        this._disposedValue = false;
    }

    /// <summary>
    /// Constructor
    /// </summary>
    /// <param name="connection"></param>
    private DuckDBMemoryStore(DuckDBConnection connection)
    {
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

    private static async Task<string> InternalUpsertAsync(DuckDBConnection connection, string collectionName, MemoryRecord record, CancellationToken cancellationToken)
    {
        record.Key = record.Metadata.Id;

        await Database.UpdateOrInsertAsync(conn: connection,
            collectionName: collectionName,
            key: record.Key,
            metadata: record.GetSerializedMetadata(),
            embedding: record.Embedding.ToArray(),
            timestamp: ToTimestampString(record.Timestamp),
            cancellationToken: cancellationToken).ConfigureAwait(false);

        return record.Key;
    }

    private static async Task<MemoryRecord?> InternalGetAsync(
        DuckDBConnection connection,
        string collectionName,
        string key, bool withEmbedding,
        CancellationToken cancellationToken)
    {
        DatabaseEntry? entry = await Database.ReadAsync(connection, collectionName, key, cancellationToken).ConfigureAwait(false);

        if (!entry.HasValue) { return null; }

        if (withEmbedding)
        {
            return MemoryRecord.FromJsonMetadata(
                json: entry.Value.MetadataString,
                entry.Value.Embedding,
                entry.Value.Key,
                ParseTimestamp(entry.Value.Timestamp));
        }

        return MemoryRecord.FromJsonMetadata(
            json: entry.Value.MetadataString,
            ReadOnlyMemory<float>.Empty,
            entry.Value.Key,
            ParseTimestamp(entry.Value.Timestamp));
    }

    #endregion
}
