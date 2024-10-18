// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

/// <summary>
/// Internal interface for client managing postgres database operations.
/// </summary>
public interface IPostgresVectorStoreDbClient
{
    /// <summary>
    /// Check if a table exists.
    /// </summary>
    /// <param name="tableName">The name assigned to a table of entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    Task<bool> DoesTableExistsAsync(string tableName, CancellationToken cancellationToken = default);

    /// <summary>
    /// Get all tables.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A group of tables.</returns>
    IAsyncEnumerable<string> GetTablesAsync(CancellationToken cancellationToken = default);
    /// <summary>
    /// Create a table.
    /// </summary>
    /// <param name="tableName">The name assigned to a table of entries.</param>
    /// <param name="recordDefinition">The record definition of the table.</param>
    /// <param name="ifNotExists">Specifies whether to include IF NOT EXISTS in the command.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    Task CreateTableAsync(string tableName, VectorStoreRecordDefinition recordDefinition, bool ifNotExists = true, CancellationToken cancellationToken = default);

    /// <summary>
    /// Drop a table.
    /// </summary>
    /// <param name="tableName">The name assigned to a table of entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    Task DeleteTableAsync(string tableName, CancellationToken cancellationToken = default);

    /// <summary>
    /// Upsert entry into a table.
    /// </summary>
    /// <param name="tableName">The name assigned to a table of entries.</param>
    /// <param name="row">The row to upsert into the table.</param>
    /// <param name="keyColumn">The key column of the table.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    Task UpsertAsync(string tableName, Dictionary<string, object?> row, string keyColumn, CancellationToken cancellationToken = default);

    /// <summary>
    /// Upsert multiple entries into a table.
    /// </summary>
    /// <param name="tableName">The name assigned to a table of entries.</param>
    /// <param name="rows">The rows to upsert into the table.</param>
    /// <param name="keyColumn">The key column of the table.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    Task UpsertBatchAsync(string tableName, IEnumerable<Dictionary<string, object?>> rows, string keyColumn, CancellationToken cancellationToken = default);

    /// <summary>
    /// Get a entry by its key.
    /// </summary>
    /// <param name="tableName">The name assigned to a table of entries.</param>
    /// <param name="key">The key of the entry to get.</param>
    /// <param name="recordDefinition">The record definition of the table.</param>
    /// <param name="includeVectors">If true, the vectors will be included in the entry.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The row if the key is found, otherwise null.</returns>
    Task<Dictionary<string, object?>?> GetAsync<TKey>(string tableName, TKey key, VectorStoreRecordDefinition recordDefinition, bool includeVectors = false, CancellationToken cancellationToken = default)
        where TKey : notnull;

    /// <summary>
    /// Get multiple entries by their keys.
    /// </summary>
    /// <param name="tableName">The name assigned to a table of entries.</param>
    /// <param name="keys">The keys of the entries to get.</param>
    /// <param name="recordDefinition">The record definition of the table.</param>
    /// <param name="includeVectors">If true, the vectors will be included in the entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The rows that match the given keys.</returns>
    IAsyncEnumerable<Dictionary<string, object?>> GetBatchAsync<TKey>(string tableName, IEnumerable<TKey> keys, VectorStoreRecordDefinition recordDefinition, bool includeVectors = false, CancellationToken cancellationToken = default)
        where TKey : notnull;

    /// <summary>
    /// Delete a entry by its key.
    /// </summary>
    /// <param name="tableName">The name assigned to a table of entries.</param>
    /// <param name="keyColumn">The name of the key column.</param>
    /// <param name="key">The key of the entry to delete.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    Task DeleteAsync<TKey>(string tableName, string keyColumn, TKey key, CancellationToken cancellationToken = default);

    /// <summary>
    /// Delete multiple entries by their keys.
    /// </summary>
    /// <param name="tableName">The name assigned to a table of entries.</param>
    /// <param name="keyColumn">The name of the key column.</param>
    /// <param name="keys">The keys of the entries to delete.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    Task DeleteBatchAsync<TKey>(string tableName, string keyColumn, IEnumerable<TKey> keys, CancellationToken cancellationToken = default);

    // /// <summary>
    // /// Gets the nearest matches to the <see cref="Vector"/>.
    // /// </summary>
    // /// <param name="tableName">The name assigned to a table of entries.</param>
    // /// <param name="embedding">The <see cref="Vector"/> to compare the table's embeddings with.</param>
    // /// <param name="limit">The maximum number of similarity results to return.</param>
    // /// <param name="minRelevanceScore">The minimum relevance threshold for returned results.</param>
    // /// <param name="withEmbeddings">If true, the embeddings will be returned in the entries.</param>
    // /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    // /// <returns>An asynchronous stream of <see cref="PostgresMemoryEntry"/> objects that the nearest matches to the <see cref="Vector"/>.</returns>
    // IAsyncEnumerable<(PostgresMemoryEntry, double)> GetNearestMatchesAsync(string tableName, Vector embedding, int limit, double minRelevanceScore = 0, bool withEmbeddings = false, CancellationToken cancellationToken = default);

    // /// <summary>
    // /// Read a entry by its key.
    // /// </summary>
    // /// <param name="tableName">The name assigned to a table of entries.</param>
    // /// <param name="key">The key of the entry to read.</param>
    // /// <param name="withEmbeddings">If true, the embeddings will be returned in the entry.</param>
    // /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    // /// <returns></returns>
    // Task<PostgresMemoryEntry?> ReadAsync(string tableName, string key, bool withEmbeddings = false, CancellationToken cancellationToken = default);

    // /// <summary>
    // /// Read multiple entries by their keys.
    // /// </summary>
    // /// <param name="tableName">The name assigned to a table of entries.</param>
    // /// <param name="keys">The keys of the entries to read.</param>
    // /// <param name="withEmbeddings">If true, the embeddings will be returned in the entries.</param>
    // /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    // /// <returns>An asynchronous stream of <see cref="PostgresMemoryEntry"/> objects that match the given keys.</returns>
    // IAsyncEnumerable<PostgresMemoryEntry> ReadBatchAsync(string tableName, IEnumerable<string> keys, bool withEmbeddings = false, CancellationToken cancellationToken = default);

    // /// <summary>
    // /// Delete a entry by its key.
    // /// </summary>
    // /// <param name="tableName">The name assigned to a table of entries.</param>
    // /// <param name="key">The key of the entry to delete.</param>
    // /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    // /// <returns></returns>
    // Task DeleteAsync(string tableName, string key, CancellationToken cancellationToken = default);

    // /// <summary>
    // /// Delete multiple entries by their key.
    // /// </summary>
    // /// <param name="tableName">The name assigned to a table of entries.</param>
    // /// <param name="keys">The keys of the entries to delete.</param>
    // /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    // /// <returns></returns>
    // Task DeleteBatchAsync(string tableName, IEnumerable<string> keys, CancellationToken cancellationToken = default);
}
