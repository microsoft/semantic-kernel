// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Data.SqlClient;
using Microsoft.SemanticKernel.Connectors.SqlServer.Classic.Core;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.SqlServer.Classic;

/// <summary>
/// An implementation of <see cref="IMemoryStore"/> backed by a SQL server database.
/// </summary>
/// <remarks>The data is saved to a MSSQL server, specified in the connection string of the factory method.
/// The data persists between subsequent instances.
/// </remarks>
#pragma warning disable SKEXP0001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
public class SqlServerMemoryStore : IMemoryStore, IDisposable
{
    private readonly SqlServerClient _dbClient;

    /// <summary>
    /// Initializes a new instance of the <see cref="SqlServerMemoryStore"/> class.
    /// </summary>
    /// <param name="connectionString">The connection string.</param>
    /// <param name="config">The SQL memoryDB configuration.</param>
    public SqlServerMemoryStore(string connectionString, SqlServerClassicConfig? config = default)
    {
        this._dbClient = new SqlServerClient(new SqlConnection(connectionString), config ?? new());
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
            embedding: JsonSerializer.Serialize(embedding),
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
            embedding: entry.Embedding ?? ReadOnlyMemory<float>.Empty,
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
            embedding: JsonSerializer.Serialize(record.Embedding),
            timestamp: record.Timestamp,
            cancellationToken: cancellationToken).ConfigureAwait(false);

        return record.Key;
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    /// <summary>
    /// Disposes resources.
    /// </summary>
    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._dbClient?.Dispose();
        }
    }
}
#pragma warning restore SKEXP0001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
