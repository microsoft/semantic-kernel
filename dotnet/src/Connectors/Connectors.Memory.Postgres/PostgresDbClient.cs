// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Npgsql;
using NpgsqlTypes;
using Pgvector;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

/// <summary>
/// An implementation of a client for Postgres. This class is used to managing postgres database operations for <see cref="PostgresMemoryStore"/>.
/// </summary>
[System.Diagnostics.CodeAnalysis.SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities", Justification = "We need to build the full table name using schema and collection, it does not support parameterized passing.")]
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and PostgresVectorStore")]
public class PostgresDbClient : IPostgresDbClient
{
    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresDbClient"/> class.
    /// </summary>
    /// <param name="dataSource">Postgres data source.</param>
    /// <param name="schema">Schema of collection tables.</param>
    /// <param name="vectorSize">Embedding vector size.</param>
    public PostgresDbClient(NpgsqlDataSource dataSource, string schema, int vectorSize)
    {
        this._dataSource = dataSource;
        this._schema = schema;
        this._vectorSize = vectorSize;
    }

    /// <inheritdoc />
    public async Task<bool> DoesTableExistsAsync(string tableName, CancellationToken cancellationToken = default)
    {
        NpgsqlConnection connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        await using (connection)
        {
            using NpgsqlCommand cmd = connection.CreateCommand();
            cmd.CommandText = $@"
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = @schema
                    AND table_type = 'BASE TABLE'
                    AND table_name = '{tableName}'";
            cmd.Parameters.AddWithValue("@schema", this._schema);

            using NpgsqlDataReader dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
            if (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                return dataReader.GetString(dataReader.GetOrdinal("table_name")) == tableName;
            }

            return false;
        }
    }

    /// <inheritdoc />
    public async Task CreateTableAsync(string tableName, CancellationToken cancellationToken = default)
    {
        NpgsqlConnection connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        await using (connection)
        {
            using NpgsqlCommand cmd = connection.CreateCommand();
            cmd.CommandText = $@"
                CREATE TABLE IF NOT EXISTS {this.GetFullTableName(tableName)} (
                    key TEXT NOT NULL,
                    metadata JSONB,
                    embedding vector({this._vectorSize}),
                    timestamp TIMESTAMP WITH TIME ZONE,
                    PRIMARY KEY (key))";
            await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> GetTablesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        NpgsqlConnection connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        await using (connection)
        {
            using NpgsqlCommand cmd = connection.CreateCommand();
            cmd.CommandText = @"
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = @schema
                    AND table_type = 'BASE TABLE'";
            cmd.Parameters.AddWithValue("@schema", this._schema);

            using NpgsqlDataReader dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
            while (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                yield return dataReader.GetString(dataReader.GetOrdinal("table_name"));
            }
        }
    }

    /// <inheritdoc />
    public async Task DeleteTableAsync(string tableName, CancellationToken cancellationToken = default)
    {
        NpgsqlConnection connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        await using (connection)
        {
            using NpgsqlCommand cmd = connection.CreateCommand();
            cmd.CommandText = $"DROP TABLE IF EXISTS {this.GetFullTableName(tableName)}";

            await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc />
    public async Task UpsertAsync(string tableName, string key,
        string? metadata, Vector? embedding, DateTime? timestamp, CancellationToken cancellationToken = default)
    {
        NpgsqlConnection connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        await using (connection)
        {
            using NpgsqlCommand cmd = connection.CreateCommand();
            cmd.CommandText = $@"
                INSERT INTO {this.GetFullTableName(tableName)} (key, metadata, embedding, timestamp)
                VALUES(@key, @metadata, @embedding, @timestamp)
                ON CONFLICT (key)
                DO UPDATE SET metadata=@metadata, embedding=@embedding, timestamp=@timestamp";
            cmd.Parameters.AddWithValue("@key", key);
            cmd.Parameters.AddWithValue("@metadata", NpgsqlTypes.NpgsqlDbType.Jsonb, metadata ?? (object)DBNull.Value);
            cmd.Parameters.AddWithValue("@embedding", embedding ?? (object)DBNull.Value);
            cmd.Parameters.AddWithValue("@timestamp", NpgsqlTypes.NpgsqlDbType.TimestampTz, timestamp ?? (object)DBNull.Value);

            await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<(PostgresMemoryEntry, double)> GetNearestMatchesAsync(
        string tableName, Vector embedding, int limit, double minRelevanceScore = 0, bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        string queryColumns = "key, metadata, timestamp";
        if (withEmbeddings)
        {
            queryColumns = "*";
        }

        NpgsqlConnection connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        await using (connection)
        {
            using NpgsqlCommand cmd = connection.CreateCommand();
            cmd.CommandText = @$"
                SELECT * FROM (SELECT {queryColumns}, 1 - (embedding <=> @embedding) AS cosine_similarity FROM {this.GetFullTableName(tableName)}
                ) AS sk_memory_cosine_similarity_table
                WHERE cosine_similarity >= @min_relevance_score
                ORDER BY cosine_similarity DESC
                Limit @limit";
            cmd.Parameters.AddWithValue("@embedding", embedding);
            cmd.Parameters.AddWithValue("@collection", tableName);
            cmd.Parameters.AddWithValue("@min_relevance_score", minRelevanceScore);
            cmd.Parameters.AddWithValue("@limit", limit);

            using NpgsqlDataReader dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);

            while (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                double cosineSimilarity = dataReader.GetDouble(dataReader.GetOrdinal("cosine_similarity"));
                yield return (await this.ReadEntryAsync(dataReader, withEmbeddings, cancellationToken).ConfigureAwait(false), cosineSimilarity);
            }
        }
    }

    /// <inheritdoc />
    public async Task<PostgresMemoryEntry?> ReadAsync(string tableName, string key,
        bool withEmbeddings = false, CancellationToken cancellationToken = default)
    {
        string queryColumns = "key, metadata, timestamp";
        if (withEmbeddings)
        {
            queryColumns = "*";
        }

        NpgsqlConnection connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        await using (connection)
        {
            using NpgsqlCommand cmd = connection.CreateCommand();
            cmd.CommandText = $"SELECT {queryColumns} FROM {this.GetFullTableName(tableName)} WHERE key=@key";
            cmd.Parameters.AddWithValue("@key", key);

            using NpgsqlDataReader dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
            if (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                return await this.ReadEntryAsync(dataReader, withEmbeddings, cancellationToken).ConfigureAwait(false);
            }

            return null;
        }
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<PostgresMemoryEntry> ReadBatchAsync(string tableName, IEnumerable<string> keys, bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        string[] keysArray = keys.ToArray();
        if (keysArray.Length == 0)
        {
            yield break;
        }

        string queryColumns = "key, metadata, timestamp";
        if (withEmbeddings)
        {
            queryColumns = "*";
        }

        NpgsqlConnection connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        await using (connection)
        {
            using NpgsqlCommand cmd = connection.CreateCommand();
            cmd.CommandText = $"SELECT {queryColumns} FROM {this.GetFullTableName(tableName)} WHERE key=ANY(@keys)";
            cmd.Parameters.AddWithValue("@keys", NpgsqlDbType.Array | NpgsqlDbType.Text, keysArray);

            using NpgsqlDataReader dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
            while (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                yield return await this.ReadEntryAsync(dataReader, withEmbeddings, cancellationToken).ConfigureAwait(false);
            }
        }
    }

    /// <inheritdoc />
    public async Task DeleteAsync(string tableName, string key, CancellationToken cancellationToken = default)
    {
        NpgsqlConnection connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        await using (connection)
        {
            using NpgsqlCommand cmd = connection.CreateCommand();
            cmd.CommandText = $"DELETE FROM {this.GetFullTableName(tableName)} WHERE key=@key";
            cmd.Parameters.AddWithValue("@key", key);

            await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc />
    public async Task DeleteBatchAsync(string tableName, IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        string[] keysArray = keys.ToArray();
        if (keysArray.Length == 0)
        {
            return;
        }

        NpgsqlConnection connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        await using (connection)
        {
            using NpgsqlCommand cmd = connection.CreateCommand();
            cmd.CommandText = $"DELETE FROM {this.GetFullTableName(tableName)} WHERE key=ANY(@keys)";
            cmd.Parameters.AddWithValue("@keys", NpgsqlDbType.Array | NpgsqlDbType.Text, keysArray);

            await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    #region private ================================================================================

    private readonly NpgsqlDataSource _dataSource;
    private readonly int _vectorSize;
    private readonly string _schema;

    /// <summary>
    /// Read a entry.
    /// </summary>
    /// <param name="dataReader">The <see cref="NpgsqlDataReader"/> to read.</param>
    /// <param name="withEmbeddings">If true, the embeddings will be returned in the entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    private async Task<PostgresMemoryEntry> ReadEntryAsync(NpgsqlDataReader dataReader, bool withEmbeddings = false, CancellationToken cancellationToken = default)
    {
        string key = dataReader.GetString(dataReader.GetOrdinal("key"));
        string metadata = dataReader.GetString(dataReader.GetOrdinal("metadata"));
        Vector? embedding = withEmbeddings ? await dataReader.GetFieldValueAsync<Vector>(dataReader.GetOrdinal("embedding"), cancellationToken).ConfigureAwait(false) : null;
        DateTime? timestamp = await dataReader.GetFieldValueAsync<DateTime?>(dataReader.GetOrdinal("timestamp"), cancellationToken).ConfigureAwait(false);
        return new PostgresMemoryEntry() { Key = key, MetadataString = metadata, Embedding = embedding, Timestamp = timestamp };
    }

    /// <summary>
    /// Get full table name with schema from table name.
    /// </summary>
    /// <param name="tableName"></param>
    /// <returns></returns>
    private string GetFullTableName(string tableName)
    {
        return $"{this._schema}.\"{tableName}\"";
    }
    #endregion
}
