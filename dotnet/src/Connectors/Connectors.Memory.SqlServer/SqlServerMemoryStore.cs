// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Memory.SqlServer;

/// <summary>
/// An implementation of <see cref="IMemoryStore"/> backed by a SQL server database.
/// </summary>
/// <remarks>The data is saved to a MSSQL server, specified in the connection string of the factory method.
/// The data persists between subsequent instances.
/// </remarks>
public sealed class SqlServerMemoryStore : IMemoryStore
{
    public const string DefaultSchema = "dbo";

    private readonly ISqlServerClient _dbClient;

    public static async Task<SqlServerMemoryStore> ConnectAsync(string connectionString, string schema = DefaultSchema, CancellationToken cancellationToken = default)
    {
        var client = new SqlServerClient(connectionString, schema);

        await client.CreateTables(cancellationToken).ConfigureAwait(false);

        return new SqlServerMemoryStore(client);
    }

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
        await foreach (var collection in this._dbClient.GetCollectionsAsync(cancellationToken))
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
        Verify.NotNullOrWhiteSpace(collectionName);

        SqlServerMemoryEntry? entry = await this._dbClient.ReadAsync(collectionName, key, withEmbedding, cancellationToken).ConfigureAwait(false);

        if (!entry.HasValue) { return null; }

        return this.GetMemoryRecordFromEntry(entry.Value);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        await foreach (SqlServerMemoryEntry entry in this._dbClient.ReadBatchAsync(collectionName, keys, withEmbeddings, cancellationToken).ConfigureAwait(false))
        {
            yield return this.GetMemoryRecordFromEntry(entry);
        }
    }

    /// <inheritdoc/>
    public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(string collectionName, Embedding<float> embedding, double minRelevanceScore = 0, bool withEmbedding = false, CancellationToken cancellationToken = default)
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
    public async IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(string collectionName, Embedding<float> embedding, int limit, double minRelevanceScore = 0, bool withEmbeddings = false, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        if (limit <= 0)
        {
            yield break;
        }

        IAsyncEnumerable<(SqlServerMemoryEntry, double)> results = this._dbClient.GetNearestMatchesAsync(
            collectionName: collectionName,
            embedding: JsonSerializer.Serialize(embedding.Vector.ToArray()),
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
        Verify.NotNullOrWhiteSpace(collectionName);

        await this._dbClient.DeleteAsync(collectionName, key, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        await this._dbClient.DeleteBatchAsync(collectionName, keys, cancellationToken).ConfigureAwait(false);
    }


    /// <inheritdoc/>
    public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        return await this.InternalUpsertAsync(collectionName, record, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        foreach (MemoryRecord record in records)
        {
            yield return await this.InternalUpsertAsync(collectionName, record, cancellationToken).ConfigureAwait(false);
        }
    }

    private MemoryRecord GetMemoryRecordFromEntry(SqlServerMemoryEntry entry)
    {
        return MemoryRecord.FromJsonMetadata(
            json: entry.MetadataString,
            embedding: entry.Embedding,
            key: entry.Key,
            timestamp: entry.Timestamp
            );
    }

    private async Task<string> InternalUpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken)
    {
        record.Key = record.Metadata.Id;

        await this._dbClient.UpsertAsync(
            collectionName: collectionName,
            key: record.Key,
            metadata: record.GetSerializedMetadata(),
            embedding: JsonSerializer.Serialize(record.Embedding.Vector.ToArray()),
            timestamp: record.Timestamp,
            cancellationToken: cancellationToken).ConfigureAwait(false);

        return record.Key;
    }
}
