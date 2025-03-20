// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Data.SqlClient;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

#pragma warning disable SKEXP0001

/// <summary>
/// An implementation of <see cref="IMemoryStore"/> backed by a SQL Server or Azure SQL database.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and SqlServerVectorStore")]
public class SqlServerMemoryStore : IMemoryStore, IDisposable
{
    internal const string DefaultSchema = "dbo";
    internal const int DefaultEmbeddingDimensionsCount = 1536;

    private readonly ISqlServerClient _sqlServerClient;
    private readonly SqlConnection? _connection;

    /// <summary>
    /// Initializes a new instance of the <see cref="SqlServerMemoryStore"/> class.
    /// </summary>
    /// <param name="connectionString">Database connection string.</param>
    /// <param name="schema">Database schema of collection tables.</param>
    /// <param name="embeddingDimensionsCount">Number of dimensions that stored embeddings will use</param>
    public SqlServerMemoryStore(string connectionString, string schema = DefaultSchema, int embeddingDimensionsCount = DefaultEmbeddingDimensionsCount)
    {
        this._connection = new SqlConnection(connectionString);
        this._sqlServerClient = new SqlServerClient(this._connection, schema, embeddingDimensionsCount);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="SqlServerMemoryStore"/> class.
    /// </summary>
    /// <param name="connection">Database connection.</param>
    /// <param name="schema">Database schema of collection tables.</param>
    /// <param name="embeddingDimensionsCount">Number of dimensions that stored embeddings will use</param>
    public SqlServerMemoryStore(SqlConnection connection, string schema = DefaultSchema, int embeddingDimensionsCount = DefaultEmbeddingDimensionsCount)
        : this(new SqlServerClient(connection, schema, embeddingDimensionsCount))
    { }

    /// <summary>
    /// Initializes a new instance of the <see cref="SqlServerMemoryStore"/> class.
    /// </summary>
    /// <param name="sqlServerClient">An instance of <see cref="ISqlServerClient"/>.</param>
    internal SqlServerMemoryStore(ISqlServerClient sqlServerClient)
    {
        this._sqlServerClient = sqlServerClient;
    }

    /// <inheritdoc/>
    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(collectionName);

        await this._sqlServerClient.CreateTableAsync(collectionName, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> GetCollectionsAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (var collection in this._sqlServerClient.GetTablesAsync(cancellationToken).ConfigureAwait(false))
        {
            yield return collection;
        }
    }

    /// <inheritdoc/>
    public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        return await this._sqlServerClient.DoesTableExistsAsync(collectionName, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        await this._sqlServerClient.DeleteTableAsync(collectionName, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        return await this.InternalUpsertAsync(collectionName, record, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        foreach (var record in records)
        {
            yield return await this.InternalUpsertAsync(collectionName, record, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public async Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        await foreach (var entry in this._sqlServerClient.ReadBatchAsync(collectionName, [key], withEmbedding, cancellationToken).ConfigureAwait(false))
        {
            return this.GetMemoryRecordFromEntry(entry);
        }
        return null;
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings = false, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        await foreach (var entry in this._sqlServerClient.ReadBatchAsync(collectionName, keys, withEmbeddings, cancellationToken).ConfigureAwait(false))
        {
            yield return this.GetMemoryRecordFromEntry(entry);
        }
    }

    /// <inheritdoc/>
    public async Task RemoveAsync(string collectionName, string key, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        await this._sqlServerClient.DeleteBatchAsync(collectionName, [key], cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        await this._sqlServerClient.DeleteBatchAsync(collectionName, keys, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(string collectionName, ReadOnlyMemory<float> embedding, int limit, double minRelevanceScore = 0, bool withEmbeddings = false, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        if (limit <= 0)
        {
            yield break;
        }

        await foreach (var (entry, cosineSimilarity) in this._sqlServerClient.GetNearestMatchesAsync(collectionName, embedding, limit, minRelevanceScore, withEmbeddings, cancellationToken).ConfigureAwait(false))
        {
            yield return (this.GetMemoryRecordFromEntry(entry), cosineSimilarity);
        }
    }

    /// <inheritdoc/>
    public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(string collectionName, ReadOnlyMemory<float> embedding, double minRelevanceScore = 0, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collectionName);

        await foreach (var item in this.GetNearestMatchesAsync(collectionName, embedding, 1, minRelevanceScore, withEmbedding, cancellationToken).ConfigureAwait(false))
        {
            return item;
        }
        return null;
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
            this._connection?.Dispose();
        }
    }

    private async Task<string> InternalUpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken)
    {
        record.Key = record.Metadata.Id;
        await this._sqlServerClient.UpsertAsync(collectionName, record.Key, record.GetSerializedMetadata(), record.Embedding, record.Timestamp, cancellationToken).ConfigureAwait(false);
        return record.Key;
    }

    private MemoryRecord GetMemoryRecordFromEntry(SqlServerMemoryEntry entry)
    {
        return MemoryRecord.FromJsonMetadata(
            entry.MetadataString,
            entry.Embedding ?? ReadOnlyMemory<float>.Empty,
            entry.Key,
            entry.Timestamp);
    }
}
