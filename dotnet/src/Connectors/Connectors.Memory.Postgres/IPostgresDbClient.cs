// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Pgvector;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

/// <summary>
/// Interface for client managing postgres database operations for <see cref="PostgresMemoryStore"/>.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and PostgresVectorStore")]
public interface IPostgresDbClient
{
    /// <summary>
    /// Check if a table exists.
    /// </summary>
    /// <param name="tableName">The name assigned to a table of entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    Task<bool> DoesTableExistsAsync(string tableName, CancellationToken cancellationToken = default);

    /// <summary>
    /// Create a table.
    /// </summary>
    /// <param name="tableName">The name assigned to a table of entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    Task CreateTableAsync(string tableName, CancellationToken cancellationToken = default);

    /// <summary>
    /// Get all tables.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A group of tables.</returns>
    IAsyncEnumerable<string> GetTablesAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Delete a table.
    /// </summary>
    /// <param name="tableName">The name assigned to a table of entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    Task DeleteTableAsync(string tableName, CancellationToken cancellationToken = default);

    /// <summary>
    /// Upsert entry into a table.
    /// </summary>
    /// <param name="tableName">The name assigned to a table of entries.</param>
    /// <param name="key">The key of the entry to upsert.</param>
    /// <param name="metadata">The metadata of the entry.</param>
    /// <param name="embedding">The embedding of the entry.</param>
    /// <param name="timestamp">The timestamp of the entry. Its 'DateTimeKind' must be <see cref="DateTimeKind.Utc"/></param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    Task UpsertAsync(string tableName, string key, string? metadata, Vector? embedding, DateTime? timestamp, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets the nearest matches to the <see cref="Vector"/>.
    /// </summary>
    /// <param name="tableName">The name assigned to a table of entries.</param>
    /// <param name="embedding">The <see cref="Vector"/> to compare the table's embeddings with.</param>
    /// <param name="limit">The maximum number of similarity results to return.</param>
    /// <param name="minRelevanceScore">The minimum relevance threshold for returned results.</param>
    /// <param name="withEmbeddings">If true, the embeddings will be returned in the entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An asynchronous stream of <see cref="PostgresMemoryEntry"/> objects that the nearest matches to the <see cref="Vector"/>.</returns>
    IAsyncEnumerable<(PostgresMemoryEntry, double)> GetNearestMatchesAsync(string tableName, Vector embedding, int limit, double minRelevanceScore = 0, bool withEmbeddings = false, CancellationToken cancellationToken = default);

    /// <summary>
    /// Read a entry by its key.
    /// </summary>
    /// <param name="tableName">The name assigned to a table of entries.</param>
    /// <param name="key">The key of the entry to read.</param>
    /// <param name="withEmbeddings">If true, the embeddings will be returned in the entry.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    Task<PostgresMemoryEntry?> ReadAsync(string tableName, string key, bool withEmbeddings = false, CancellationToken cancellationToken = default);

    /// <summary>
    /// Read multiple entries by their keys.
    /// </summary>
    /// <param name="tableName">The name assigned to a table of entries.</param>
    /// <param name="keys">The keys of the entries to read.</param>
    /// <param name="withEmbeddings">If true, the embeddings will be returned in the entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An asynchronous stream of <see cref="PostgresMemoryEntry"/> objects that match the given keys.</returns>
    IAsyncEnumerable<PostgresMemoryEntry> ReadBatchAsync(string tableName, IEnumerable<string> keys, bool withEmbeddings = false, CancellationToken cancellationToken = default);

    /// <summary>
    /// Delete a entry by its key.
    /// </summary>
    /// <param name="tableName">The name assigned to a table of entries.</param>
    /// <param name="key">The key of the entry to delete.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    Task DeleteAsync(string tableName, string key, CancellationToken cancellationToken = default);

    /// <summary>
    /// Delete multiple entries by their key.
    /// </summary>
    /// <param name="tableName">The name assigned to a table of entries.</param>
    /// <param name="keys">The keys of the entries to delete.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    Task DeleteBatchAsync(string tableName, IEnumerable<string> keys, CancellationToken cancellationToken = default);
}
