// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq.Expressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Npgsql;
using Pgvector;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

/// <summary>
/// Internal interface for client managing postgres database operations.
/// </summary>
internal interface IPostgresVectorStoreDbClient
{
    /// <summary>
    /// The <see cref="NpgsqlDataSource"/> used to connect to the database.
    /// </summary>
    NpgsqlDataSource DataSource { get; }

    /// <summary>
    /// The name of the database.
    /// </summary>
    string? DatabaseName { get; }

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
    /// Create a table. Also creates an index on vector columns if the table has vector properties defined.
    /// </summary>
    /// <param name="tableName">The name assigned to a table of entries.</param>
    /// <param name="model">The collection model.</param>
    /// <param name="ifNotExists">Specifies whether to include IF NOT EXISTS in the command.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    Task CreateTableAsync(string tableName, VectorStoreRecordModel model, bool ifNotExists = true, CancellationToken cancellationToken = default);

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
    /// <param name="model">The collection model.</param>
    /// <param name="includeVectors">If true, the vectors will be included in the entry.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The row if the key is found, otherwise null.</returns>
    Task<Dictionary<string, object?>?> GetAsync<TKey>(string tableName, TKey key, VectorStoreRecordModel model, bool includeVectors = false, CancellationToken cancellationToken = default)
        where TKey : notnull;

    /// <summary>
    /// Get multiple entries by their keys.
    /// </summary>
    /// <param name="tableName">The name assigned to a table of entries.</param>
    /// <param name="keys">The keys of the entries to get.</param>
    /// <param name="model">The collection model.</param>
    /// <param name="includeVectors">If true, the vectors will be included in the entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The rows that match the given keys.</returns>
    IAsyncEnumerable<Dictionary<string, object?>> GetBatchAsync<TKey>(string tableName, IEnumerable<TKey> keys, VectorStoreRecordModel model, bool includeVectors = false, CancellationToken cancellationToken = default)
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

    /// <summary>
    /// Gets the nearest matches to the <see cref="Vector"/>.
    /// </summary>
    /// <param name="tableName">The name assigned to a table of entries.</param>
    /// <param name="model">The collection model.</param>
    /// <param name="vectorProperty">The vector property.</param>
    /// <param name="vectorValue">The <see cref="Vector"/> to compare the table's vector with.</param>
    /// <param name="limit">The maximum number of similarity results to return.</param>
    /// <param name="options">The options that control the behavior of the search.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An asynchronous stream of result objects that the nearest matches to the <see cref="Vector"/>.</returns>
    IAsyncEnumerable<(Dictionary<string, object?> Row, double Distance)> GetNearestMatchesAsync<TRecord>(string tableName, VectorStoreRecordModel model, VectorStoreRecordVectorPropertyModel vectorProperty, Vector vectorValue, int limit,
        VectorSearchOptions<TRecord> options, CancellationToken cancellationToken = default);

    IAsyncEnumerable<Dictionary<string, object?>> GetMatchingRecordsAsync<TRecord>(string tableName, VectorStoreRecordModel model,
        Expression<Func<TRecord, bool>> filter, int top, GetFilteredRecordOptions<TRecord> options, CancellationToken cancellationToken = default);
}
