﻿// Copyright (c) Microsoft. All rights reserved.

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
        var memoryStore = new DuckDBMemoryStore(filename, null);
        return await InitialiseMemoryStoreAsync(memoryStore, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Connect a DuckDB database
    /// </summary>
    /// <param name="filename">Path to the database file. If file does not exist, it will be created.</param>
    /// <param name="vectorSize">Embedding vector size.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public static async Task<DuckDBMemoryStore> ConnectAsync(string filename, int vectorSize,
        CancellationToken cancellationToken = default)
    {
        var memoryStore = new DuckDBMemoryStore(filename, vectorSize);
        return await InitialiseMemoryStoreAsync(memoryStore, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Connect an in memory DuckDB database
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public static Task<DuckDBMemoryStore> ConnectAsync(
        CancellationToken cancellationToken = default)
    {
        return ConnectAsync(":memory:", cancellationToken);
    }

    /// <summary>
    /// Connect an in memory DuckDB database
    /// </summary>
    /// <param name="vectorSize">Embedding vector size.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public static Task<DuckDBMemoryStore> ConnectAsync(int vectorSize,
        CancellationToken cancellationToken = default)
    {
        return ConnectAsync(":memory:", vectorSize, cancellationToken);
    }

    /// <summary>
    /// Connect an in memory DuckDB database
    /// </summary>
    /// <param name="connection">An already established connection.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public static async Task<DuckDBMemoryStore> ConnectAsync(DuckDBConnection connection,
        CancellationToken cancellationToken = default)
    {
        var memoryStore = new DuckDBMemoryStore(connection);
        return await InitialiseMemoryStoreAsync(memoryStore, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Connect an in memory DuckDB database
    /// </summary>
    /// <param name="connection">An already established connection.</param>
    /// <param name="vectorSize">Embedding vector size.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public static async Task<DuckDBMemoryStore> ConnectAsync(DuckDBConnection connection, int vectorSize,
        CancellationToken cancellationToken = default)
    {
        var memoryStore = new DuckDBMemoryStore(connection, vectorSize);
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
        await foreach (var collection in this._dbConnector.GetCollectionsAsync(this._dbConnection, cancellationToken).ConfigureAwait(false))
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
            if (result is not null)
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
        await this._dbConnector.DeleteBatchAsync(this._dbConnection, collectionName, keys.ToArray(), cancellationToken).ConfigureAwait(false);
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

        List<(MemoryRecord Record, double Score)> embeddings = [];

        await foreach (var dbEntry in this._dbConnector.GetNearestMatchesAsync(this._dbConnection, collectionName, embedding.ToArray(), limit, minRelevanceScore, cancellationToken).ConfigureAwait(false))
        {
            var entry = MemoryRecord.FromJsonMetadata(
                json: dbEntry.MetadataString,
                withEmbeddings ? dbEntry.Embedding : [],
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
        if (!this._disposedValue)
        {
            this._dbConnection.Close();
            this._dbConnection.Dispose();

            this._disposedValue = true;
        }
    }

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
    /// <param name="vectorSize">Embedding vector size. If provided, the database will be used ARRAY type to store embeddings. If not, the database will fall back to LIST.</param>
    private DuckDBMemoryStore(string filename, int? vectorSize = null)
    {
        this._dbConnector = new Database(vectorSize);
        this._dbConnection = new DuckDBConnection($"Data Source={filename};");
        this._disposedValue = false;
    }

    /// <summary>
    /// Constructor
    /// </summary>
    /// <param name="connection"></param>
    /// <param name="vectorSize">Embedding vector size. If provided, the database will be used ARRAY type to store embeddings. If not, the database will fall back to LIST.</param>
    private DuckDBMemoryStore(DuckDBConnection connection, int? vectorSize = null)
    {
        this._dbConnector = new Database(vectorSize);
        this._dbConnection = connection;
        this._disposedValue = false;
    }

    private static string? ToTimestampString(DateTimeOffset? timestamp)
    {
        return timestamp?.ToString("u", CultureInfo.InvariantCulture);
    }

    private static DateTimeOffset? ParseTimestamp(string? str)
    {
        if (DateTimeOffset.TryParse(str, CultureInfo.InvariantCulture, DateTimeStyles.AssumeUniversal, out DateTimeOffset timestamp))
        {
            return timestamp;
        }

        return null;
    }

    private async Task<string> InternalUpsertAsync(DuckDBConnection connection, string collectionName, MemoryRecord record, CancellationToken cancellationToken)
    {
        record.Key = record.Metadata.Id;

        await this._dbConnector.UpdateOrInsertAsync(conn: connection,
            collectionName: collectionName,
            key: record.Key,
            metadata: record.GetSerializedMetadata(),
            embedding: record.Embedding.ToArray(),
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
