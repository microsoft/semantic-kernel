// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

/// <summary>
/// Interface for client managing SQL Server or Azure SQL database operations.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and SqlServerVectorStore")]
internal interface ISqlServerClient
{
    /// <summary>
    /// Create a table.
    /// </summary>
    /// <param name="tableName">The name assigned to a table of entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    Task CreateTableAsync(string tableName, CancellationToken cancellationToken = default);

    /// <summary>
    /// Get all tables.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A group of tables.</returns>
    IAsyncEnumerable<string> GetTablesAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Check if a table exists.
    /// </summary>
    /// <param name="tableName">The name assigned to a table of entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    Task<bool> DoesTableExistsAsync(string tableName, CancellationToken cancellationToken = default);

    /// <summary>
    /// Delete a table.
    /// </summary>
    /// <param name="tableName">The name assigned to a table of entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    Task DeleteTableAsync(string tableName, CancellationToken cancellationToken = default);

    /// <summary>
    /// Upsert entry into a table.
    /// </summary>
    /// <param name="tableName">The name assigned to a table of entries.</param>
    /// <param name="key">The key of the entry to upsert.</param>
    /// <param name="metadata">The metadata of the entry.</param>
    /// <param name="embedding">The embedding of the entry.</param>
    /// <param name="timestamp">The timestamp of the entry.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    Task UpsertAsync(string tableName, string key, string metadata, ReadOnlyMemory<float> embedding, DateTimeOffset? timestamp, CancellationToken cancellationToken = default);

    /// <summary>
    /// Read multiple entries by their keys.
    /// </summary>
    /// <param name="tableName">The name assigned to a table of entries.</param>
    /// <param name="keys">The keys of the entries to read.</param>
    /// <param name="withEmbeddings">If true, the embeddings will be returned in the entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An asynchronous stream of <see cref="SqlServerMemoryEntry"/> objects that match the given keys.</returns>
    IAsyncEnumerable<SqlServerMemoryEntry> ReadBatchAsync(string tableName, IEnumerable<string> keys, bool withEmbeddings = false, CancellationToken cancellationToken = default);

    /// <summary>
    /// Delete multiple entries by their key.
    /// </summary>
    /// <param name="tableName">The name assigned to a table of entries.</param>
    /// <param name="keys">The keys of the entries to delete.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    Task DeleteBatchAsync(string tableName, IEnumerable<string> keys, CancellationToken cancellationToken = default);

    /// <summary>
    /// Gets the nearest matches to the embedding.
    /// </summary>
    /// <param name="tableName">The name assigned to a table of entries.</param>
    /// <param name="embedding">The embedding to compare the table's embeddings with.</param>
    /// <param name="limit">The maximum number of similarity results to return.</param>
    /// <param name="minRelevanceScore">The minimum relevance threshold for returned results.</param>
    /// <param name="withEmbeddings">If true, the embeddings will be returned in the entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An asynchronous stream of <see cref="SqlServerMemoryEntry"/> objects that the nearest matches to the embedding.</returns>
    IAsyncEnumerable<(SqlServerMemoryEntry, double)> GetNearestMatchesAsync(string tableName, ReadOnlyMemory<float> embedding, int limit, double minRelevanceScore = 0, bool withEmbeddings = false, CancellationToken cancellationToken = default);
}
