// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory;
using Npgsql;
using Pgvector;
using Pgvector.Npgsql;

namespace Microsoft.SemanticKernel.Connectors.Memory.Postgres;

/// <summary>
/// An implementation of <see cref="IMemoryStore"/> backed by a Postgres database with pgvector extension.
/// </summary>
public class PostgresMemoryStore : IMemoryStore, IDisposable
{
    /// <summary>
    /// Connect a Postgres database
    /// </summary>
    /// <param name="connectionString">Database connection string. If table does not exist, it will be created.</param>
    /// <param name="vectorSize">Embedding vector size</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public static async Task<PostgresMemoryStore> ConnectAsync(string connectionString, int vectorSize,
        CancellationToken cancellationToken = default)
    {
        var dataSourceBuilder = new NpgsqlDataSourceBuilder(connectionString);
        // Use pgvector
        dataSourceBuilder.UseVector();

        var memoryStore = new PostgresMemoryStore(dataSourceBuilder.Build());
        using NpgsqlConnection dbConnection = await memoryStore._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        await memoryStore._dbConnector.CreatePgVectorExtensionAsync(dbConnection, cancellationToken).ConfigureAwait(false);
        await memoryStore._dbConnector.CreateTableAsync(dbConnection, vectorSize, cancellationToken).ConfigureAwait(false);
        await memoryStore._dbConnector.CreateIndexAsync(dbConnection, cancellationToken).ConfigureAwait(false);
        return memoryStore;
    }

    /// <inheritdoc/>
    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        using NpgsqlConnection dbConnection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        await this._dbConnector.CreateCollectionAsync(dbConnection, collectionName, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        using NpgsqlConnection dbConnection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        return await this._dbConnector.DoesCollectionExistsAsync(dbConnection, collectionName, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> GetCollectionsAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using NpgsqlConnection dbConnection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        await foreach (var collection in this._dbConnector.GetCollectionsAsync(dbConnection, cancellationToken).ConfigureAwait(false))
        {
            yield return collection;
        }
    }

    /// <inheritdoc/>
    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        using NpgsqlConnection dbConnection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        await this._dbConnector.DeleteCollectionAsync(dbConnection, collectionName, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken = default)
    {
        using NpgsqlConnection dbConnection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        return await this.InternalUpsertAsync(dbConnection, collectionName, record, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using NpgsqlConnection dbConnection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        foreach (var record in records)
        {
            yield return await this.InternalUpsertAsync(dbConnection, collectionName, record, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public async Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
        using NpgsqlConnection dbConnection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        return await this.InternalGetAsync(dbConnection, collectionName, key, withEmbedding, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using NpgsqlConnection dbConnection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        foreach (var key in keys)
        {
            var result = await this.InternalGetAsync(dbConnection, collectionName, key, withEmbeddings, cancellationToken).ConfigureAwait(false);
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
        using NpgsqlConnection dbConnection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        await this._dbConnector.DeleteAsync(dbConnection, collectionName, key, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        using NpgsqlConnection dbConnection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        foreach (var key in keys)
        {
            await this._dbConnector.DeleteAsync(dbConnection, collectionName, key, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
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

        using NpgsqlConnection dbConnection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        IAsyncEnumerable<(DatabaseEntry, double)> results = this._dbConnector.GetNearestMatchesAsync(
            dbConnection,
            collectionName: collectionName,
            embeddingFilter: new Vector(embedding.Vector.ToArray()),
            limit: limit,
            minRelevanceScore: minRelevanceScore,
            withEmbeddings: withEmbeddings,
            cancellationToken: cancellationToken);

        await foreach (var (entry, cosineSimilarity) in results.ConfigureAwait(false))
        {
            MemoryRecord record = MemoryRecord.FromJsonMetadata(
                json: entry.MetadataString,
                withEmbeddings && entry.Embedding != null ? new Embedding<float>(entry.Embedding!.ToArray()) : Embedding<float>.Empty,
                entry.Key,
                ParseTimestamp(entry.Timestamp));
            yield return (record, cosineSimilarity);
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
                this._dataSource.Dispose();
            }

            this._disposedValue = true;
        }
    }

    #endregion

    #region private ================================================================================

    private readonly Database _dbConnector;
    private readonly NpgsqlDataSource _dataSource;
    private bool _disposedValue;

    /// <summary>
    /// Constructor
    /// </summary>
    /// <param name="dataSource">Postgres data source.</param>
    private PostgresMemoryStore(NpgsqlDataSource dataSource)
    {
        this._dataSource = dataSource;
        this._dbConnector = new Database();
        this._disposedValue = false;
    }

    private static long? ToTimestampLong(DateTimeOffset? timestamp)
    {
        return timestamp?.ToUnixTimeMilliseconds();
    }

    private static DateTimeOffset? ParseTimestamp(long? timestamp)
    {
        if (timestamp.HasValue)
        {
            return DateTimeOffset.FromUnixTimeMilliseconds(timestamp.Value);
        }

        return null;
    }

    private async Task<string> InternalUpsertAsync(NpgsqlConnection connection, string collectionName, MemoryRecord record, CancellationToken cancellationToken)
    {
        record.Key = record.Metadata.Id;

        await this._dbConnector.UpsertAsync(
            conn: connection,
            collectionName: collectionName,
            key: record.Key,
            metadata: record.GetSerializedMetadata(),
            embedding: new Vector(record.Embedding.Vector.ToArray()),
            timestamp: ToTimestampLong(record.Timestamp),
            cancellationToken: cancellationToken).ConfigureAwait(false);

        return record.Key;
    }

    private async Task<MemoryRecord?> InternalGetAsync(NpgsqlConnection connection, string collectionName, string key, bool withEmbedding, CancellationToken cancellationToken)
    {
        DatabaseEntry? entry = await this._dbConnector.ReadAsync(connection, collectionName, key, withEmbedding, cancellationToken).ConfigureAwait(false);

        if (!entry.HasValue) { return null; }

        if (withEmbedding)
        {
            return MemoryRecord.FromJsonMetadata(
                json: entry.Value.MetadataString,
                embedding: entry.Value.Embedding != null ? new Embedding<float>(entry.Value.Embedding.ToArray()) : Embedding<float>.Empty,
                entry.Value.Key,
                ParseTimestamp(entry.Value.Timestamp));
        }

        return MemoryRecord.FromJsonMetadata(
            json: entry.Value.MetadataString,
            Embedding<float>.Empty,
            entry.Value.Key,
            ParseTimestamp(entry.Value.Timestamp));
    }

    #endregion
}
