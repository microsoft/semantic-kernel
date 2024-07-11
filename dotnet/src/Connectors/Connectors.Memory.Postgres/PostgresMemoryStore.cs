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
using Npgsql;
using Pgvector;

namespace Microsoft.SemanticKernel.Connectors.Memory.Postgres;

/// <summary>
/// An implementation of <see cref="IMemoryStore"/> backed by a Postgres database with pgvector extension.
/// </summary>
/// <remarks>The embedded data is saved to the Postgres database specified in the constructor.
/// Similarity search capability is provided through the pgvector extension. Use Postgres's "Table" to implement "Collection".
/// </remarks>
public class PostgresMemoryStore : IMemoryStore
{
    internal const string DefaultSchema = "public";

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresMemoryStore"/> class.
    /// </summary>
    /// <param name="dataSource">Postgres data source.</param>
    /// <param name="vectorSize">Embedding vector size.</param>
    /// <param name="schema">Database schema of collection tables. The default value is "public".</param>
    public PostgresMemoryStore(NpgsqlDataSource dataSource, int vectorSize, string schema = DefaultSchema)
        : this(new PostgresDbClient(dataSource, schema, vectorSize))
    {
    }

    public PostgresMemoryStore(IPostgresDbClient postgresDbClient)
    {
        this._postgresDbClient = postgresDbClient;
    }

    /// <inheritdoc/>
    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        await this._postgresDbClient.CreateTableAsync(collectionName, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        return await this._postgresDbClient.DoesTableExistsAsync(collectionName, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> GetCollectionsAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (string collection in this._postgresDbClient.GetTablesAsync(cancellationToken).ConfigureAwait(false))
        {
            yield return collection;
        }
    }

    /// <inheritdoc/>
    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        await this._postgresDbClient.DeleteTableAsync(collectionName, cancellationToken).ConfigureAwait(false);
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

    /// <inheritdoc/>
    public async Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        PostgresMemoryEntry? entry = await this._postgresDbClient.ReadAsync(collectionName, key, withEmbedding, cancellationToken).ConfigureAwait(false);

        if (!entry.HasValue) { return null; }

        return this.GetMemoryRecordFromEntry(entry.Value);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        await foreach (PostgresMemoryEntry entry in this._postgresDbClient.ReadBatchAsync(collectionName, keys, withEmbeddings, cancellationToken).ConfigureAwait(false))
        {
            yield return this.GetMemoryRecordFromEntry(entry);
        }
    }

    /// <inheritdoc/>
    public async Task RemoveAsync(string collectionName, string key, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        await this._postgresDbClient.DeleteAsync(collectionName, key, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        await this._postgresDbClient.DeleteBatchAsync(collectionName, keys, cancellationToken).ConfigureAwait(false);
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
        Verify.NotNullOrWhiteSpace(collectionName);

        if (limit <= 0)
        {
            yield break;
        }

        IAsyncEnumerable<(PostgresMemoryEntry, double)> results = this._postgresDbClient.GetNearestMatchesAsync(
            tableName: collectionName,
            embedding: new Vector(GetOrCreateArray(embedding)),
            limit: limit,
            minRelevanceScore: minRelevanceScore,
            withEmbeddings: withEmbeddings,
            cancellationToken: cancellationToken);

        await foreach ((PostgresMemoryEntry entry, double cosineSimilarity) in results.ConfigureAwait(false))
        {
            yield return (this.GetMemoryRecordFromEntry(entry), cosineSimilarity);
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

    #region private ================================================================================

    private readonly IPostgresDbClient _postgresDbClient;

    private async Task<string> InternalUpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken)
    {
        record.Key = record.Metadata.Id;

        await this._postgresDbClient.UpsertAsync(
            tableName: collectionName,
            key: record.Key,
            metadata: record.GetSerializedMetadata(),
            embedding: new Vector(GetOrCreateArray(record.Embedding)),
            timestamp: record.Timestamp?.UtcDateTime,
            cancellationToken: cancellationToken).ConfigureAwait(false);

        return record.Key;
    }

    private MemoryRecord GetMemoryRecordFromEntry(PostgresMemoryEntry entry)
    {
        return MemoryRecord.FromJsonMetadata(
            json: entry.MetadataString,
            embedding: entry.Embedding?.ToArray() ?? ReadOnlyMemory<float>.Empty,
            key: entry.Key,
            timestamp: entry.Timestamp?.ToLocalTime());
    }

    private static float[] GetOrCreateArray(ReadOnlyMemory<float> memory) =>
        MemoryMarshal.TryGetArray(memory, out ArraySegment<float> array) &&
        array.Count == array.Array!.Length ?
            array.Array :
            memory.ToArray();

    #endregion
}
