// Copyright (c) Kevin BEAUGRAND. All rights reserved.

using Microsoft.SemanticKernel.Memory;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Connectors.MssqlServer;

/// <summary>
/// An implementation of <see cref="IMemoryStore"/> backed by a SQL server database.
/// </summary>
/// <remarks>The data is saved to a MSSQL server, specified in the connection string of the factory method.
/// The data persists between subsequent instances.
/// </remarks>
#pragma warning disable SKEXP0001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
public sealed class SqlServerMemoryStore : IMemoryStore, IDisposable
{
    private ISqlServerClient _dbClient;

    /// <summary>
    /// Connects to a SQL Server database using the provided connection string and schema, and returns a new instance of <see cref="SqlServerMemoryStore"/>.
    /// </summary>
    /// <param name="connectionString">The connection string to use for connecting to the SQL Server database.</param>
    /// <param name="config">The SQL server configuration.</param>
    /// <param name="cancellationToken">A cancellation token that can be used to cancel the asynchronous operation.</param>
    /// <returns>A new instance of <see cref="SqlServerMemoryStore"/> connected to the specified SQL Server database.</returns>
    public static async Task<SqlServerMemoryStore> ConnectAsync(string connectionString, SqlServerConfig? config = default, CancellationToken cancellationToken = default)
    {
        var client = new SqlServerClient(connectionString, config ?? new());

        await client.CreateTablesAsync(cancellationToken).ConfigureAwait(false);

        return new SqlServerMemoryStore(client);
    }

    /// <summary>
    /// Represents a memory store implementation that uses a SQL Server database as its backing store.
    /// </summary>
    public SqlServerMemoryStore(ISqlServerClient dbClient)
    {
        this._dbClient = dbClient;
    }

    /// <inheritdoc/>
    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        await this._dbClient.CreateCollectionAsync(collectionName, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        return await this._dbClient.DoesCollectionExistsAsync(collectionName, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> GetCollectionsAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (var collection in this._dbClient.GetCollectionsAsync(cancellationToken).ConfigureAwait(false))
        {
            yield return collection;
        }
    }

    /// <inheritdoc/>
    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        await this._dbClient.DeleteCollectionAsync(collectionName, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(collectionName))
        {
            throw new ArgumentNullException(nameof(collectionName));
        }

        SqlServerMemoryEntry? entry = await this._dbClient.ReadAsync(collectionName, key, withEmbedding, cancellationToken).ConfigureAwait(false);

        if (!entry.HasValue) { return null; }

        return this.GetMemoryRecordFromEntry(entry.Value);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(collectionName))
        {
            throw new ArgumentNullException(nameof(collectionName));
        }

        await foreach (SqlServerMemoryEntry entry in this._dbClient.ReadBatchAsync(collectionName, keys, withEmbeddings, cancellationToken).ConfigureAwait(false))
        {
            yield return this.GetMemoryRecordFromEntry(entry);
        }
    }

    /// <inheritdoc/>
    public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(string collectionName, ReadOnlyMemory<float> embedding, double minRelevanceScore = 0, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
        var nearest = this.GetNearestMatchesAsync(
                    collectionName: collectionName,
                    embedding: embedding,
                    limit: 1,
                    minRelevanceScore: minRelevanceScore,
                    withEmbeddings: withEmbedding,
                    cancellationToken: cancellationToken)
            .WithCancellation(cancellationToken);

        await foreach (var item in nearest)
        {
            return item;
        }

        return null;
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(string collectionName, ReadOnlyMemory<float> embedding, int limit, double minRelevanceScore = 0, bool withEmbeddings = false, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(collectionName))
        {
            throw new ArgumentNullException(nameof(collectionName));
        }

        if (limit <= 0)
        {
            yield break;
        }

        IAsyncEnumerable<(SqlServerMemoryEntry, double)> results = this._dbClient.GetNearestMatchesAsync(
            collectionName: collectionName,
            embedding: JsonSerializer.Serialize(embedding.ToArray()),
            limit: limit,
            minRelevanceScore: minRelevanceScore,
            withEmbeddings: withEmbeddings,
            cancellationToken: cancellationToken);

        await foreach ((SqlServerMemoryEntry entry, double cosineSimilarity) in results.ConfigureAwait(false))
        {
            yield return (this.GetMemoryRecordFromEntry(entry), cosineSimilarity);
        }
    }

    /// <inheritdoc/>
    public async Task RemoveAsync(string collectionName, string key, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(collectionName))
        {
            throw new ArgumentNullException(nameof(collectionName));
        }

        await this._dbClient.DeleteAsync(collectionName, key, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(collectionName))
        {
            throw new ArgumentNullException(nameof(collectionName));
        }

        await this._dbClient.DeleteBatchAsync(collectionName, keys, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(collectionName))
        {
            throw new ArgumentNullException(nameof(collectionName));
        }

        return await this.InternalUpsertAsync(collectionName, record, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> UpsertBatchAsync(
        string collectionName,
        IEnumerable<MemoryRecord> records,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(collectionName))
        {
            throw new ArgumentNullException(nameof(collectionName));
        }

        foreach (MemoryRecord record in records)
        {
            yield return await this.InternalUpsertAsync(collectionName, record, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc />
    private MemoryRecord GetMemoryRecordFromEntry(SqlServerMemoryEntry entry)
    {
        return MemoryRecord.FromJsonMetadata(
            json: entry.MetadataString,
            embedding: entry.Embedding ?? new ReadOnlyMemory<float>(),
            key: entry.Key,
            timestamp: entry.Timestamp
            );
    }

    /// <inheritdoc />
    private async Task<string> InternalUpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken)
    {
        record.Key = record.Metadata.Id;

        await this._dbClient.UpsertAsync(
            collectionName: collectionName,
            key: record.Key,
            metadata: record.GetSerializedMetadata(),
            embedding: JsonSerializer.Serialize(record.Embedding.ToArray()),
            timestamp: record.Timestamp,
            cancellationToken: cancellationToken).ConfigureAwait(false);

        return record.Key;
    }

    public void Dispose()
    {
        if (this._dbClient is not null)
        {
            this._dbClient.Dispose();
            this._dbClient = null!;
        }
    }
}
#pragma warning restore SKEXP0001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
