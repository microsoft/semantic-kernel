// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Npgsql;
using Pgvector;

namespace Microsoft.SemanticKernel.Connectors.Memory.Postgres;

/// <summary>
/// An implementation of a client for Postgres. This class is used to managing postgres database operations.
/// </summary>
[System.Diagnostics.CodeAnalysis.SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities", Justification = "We need to build the full table name using schema and collection, it does not support parameterized passing.")]
public class PostgresDbClient : IPostgresDbClient
{
    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresDbClient"/> class.
    /// </summary>
    /// <param name="dataSource">Postgres data source.</param>
    /// <param name="schema">Schema of collection tables.</param>
    /// <param name="vectorSize">Embedding vector size.</param>
    /// <param name="numberOfLists">Specifies the number of lists for indexing. Higher values can improve recall but may impact performance. The default value is 1000. More info <see href="https://github.com/pgvector/pgvector#indexing"/></param>
    public PostgresDbClient(NpgsqlDataSource dataSource, string schema, int vectorSize, int numberOfLists)
    {
        this._dataSource = dataSource;
        this._schema = schema;
        this._vectorSize = vectorSize;
        this._numberOfLists = numberOfLists;
    }

    /// <summary>
    /// Check if a collection exists.
    /// </summary>
    /// <param name="collectionName">The name assigned to a collection of entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public async Task<bool> DoesCollectionExistsAsync(
        string collectionName,
        CancellationToken cancellationToken = default)
    {
        using NpgsqlConnection connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        using NpgsqlCommand cmd = connection.CreateCommand();
        cmd.CommandText = $@"
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = @schema
                AND table_type = 'BASE TABLE'
                AND table_name = '{collectionName}'";
        cmd.Parameters.AddWithValue("@schema", this._schema);

        using var dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
        if (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            return dataReader.GetString(dataReader.GetOrdinal("table_name")) == collectionName;
        }

        return false;
    }

    /// <summary>
    /// Create a collection.
    /// </summary>
    /// <param name="collectionName">The name assigned to a collection of entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        using NpgsqlConnection connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        await this.CreateTableAsync(connection, collectionName, cancellationToken).ConfigureAwait(false);

        await this.CreateIndexAsync(connection, collectionName, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Get all collections.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public async IAsyncEnumerable<string> GetCollectionsAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using NpgsqlConnection connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        using NpgsqlCommand cmd = connection.CreateCommand();
        cmd.CommandText = @"
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = @schema
                AND table_type = 'BASE TABLE'";
        cmd.Parameters.AddWithValue("@schema", this._schema);

        using var dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
        while (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            yield return dataReader.GetString(dataReader.GetOrdinal("table_name"));
        }
    }

    /// <summary>
    /// Delete a collection.
    /// </summary>
    /// <param name="collectionName">The name assigned to a collection of entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        using NpgsqlConnection connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        using NpgsqlCommand cmd = connection.CreateCommand();
        cmd.CommandText = $"DROP TABLE IF EXISTS {this.GetTableName(collectionName)}";

        await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Upsert entry into a collection.
    /// </summary>
    /// <param name="collectionName">The name assigned to a collection of entries.</param>
    /// <param name="key">The key of the entry to upsert.</param>
    /// <param name="metadata">The metadata of the entry.</param>
    /// <param name="embedding">The embedding of the entry.</param>
    /// <param name="timestamp">The timestamp of the entry</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public async Task UpsertAsync(string collectionName, string key,
        string? metadata, Vector? embedding, long? timestamp, CancellationToken cancellationToken = default)
    {
        using NpgsqlConnection connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        using NpgsqlCommand cmd = connection.CreateCommand();
        cmd.CommandText = $@"
            INSERT INTO {this.GetTableName(collectionName)} (key, metadata, embedding, timestamp)
            VALUES(@key, @metadata, @embedding, @timestamp)
            ON CONFLICT (key)
            DO UPDATE SET metadata=@metadata, embedding=@embedding, timestamp=@timestamp";
        cmd.Parameters.AddWithValue("@key", key);
        cmd.Parameters.AddWithValue("@metadata", NpgsqlTypes.NpgsqlDbType.Jsonb, metadata ?? (object)DBNull.Value);
        cmd.Parameters.AddWithValue("@embedding", embedding ?? (object)DBNull.Value);
        cmd.Parameters.AddWithValue("@timestamp", timestamp ?? (object)DBNull.Value);

        await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Gets the nearest matches to the <see cref="Vector"/>.
    /// </summary>
    /// <param name="collectionName">The name assigned to a collection of entries.</param>
    /// <param name="embeddingFilter">The <see cref="Vector"/> to compare the collection's embeddings with.</param>
    /// <param name="limit">The maximum number of similarity results to return.</param>
    /// <param name="minRelevanceScore">The minimum relevance threshold for returned results.</param>
    /// <param name="withEmbeddings">If true, the embeddings will be returned in the entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public async IAsyncEnumerable<(PostgresMemoryEntry, double)> GetNearestMatchesAsync(
        string collectionName, Vector embeddingFilter, int limit, double minRelevanceScore = 0, bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var queryColumns = "key, metadata, timestamp";
        if (withEmbeddings)
        {
            queryColumns = "*";
        }

        using NpgsqlConnection connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        using NpgsqlCommand cmd = connection.CreateCommand();
        cmd.CommandText = @$"
            SELECT * FROM (SELECT {queryColumns}, 1 - (embedding <=> @embedding) AS cosine_similarity FROM {this.GetTableName(collectionName)}
            ) AS sk_memory_cosine_similarity_table
            WHERE cosine_similarity >= @min_relevance_score
            ORDER BY cosine_similarity DESC
            Limit @limit";
        cmd.Parameters.AddWithValue("@embedding", embeddingFilter);
        cmd.Parameters.AddWithValue("@collection", collectionName);
        cmd.Parameters.AddWithValue("@min_relevance_score", minRelevanceScore);
        cmd.Parameters.AddWithValue("@limit", limit);

        using var dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);

        while (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            double cosineSimilarity = dataReader.GetDouble(dataReader.GetOrdinal("cosine_similarity"));
            yield return (await this.ReadEntryAsync(dataReader, withEmbeddings, cancellationToken).ConfigureAwait(false), cosineSimilarity);
        }
    }

    /// <summary>
    /// Read a entry by its key.
    /// </summary>
    /// <param name="collectionName">The name assigned to a collection of entries.</param>
    /// <param name="key">The key of the entry to read.</param>
    /// <param name="withEmbeddings">If true, the embeddings will be returned in the entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public async Task<PostgresMemoryEntry?> ReadAsync(string collectionName, string key,
        bool withEmbeddings = false, CancellationToken cancellationToken = default)
    {
        var queryColumns = "key, metadata, timestamp";
        if (withEmbeddings)
        {
            queryColumns = "*";
        }

        using NpgsqlConnection connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        using NpgsqlCommand cmd = connection.CreateCommand();
        cmd.CommandText = $"SELECT {queryColumns} FROM {this.GetTableName(collectionName)} WHERE key=@key";
        cmd.Parameters.AddWithValue("@key", key);

        using var dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
        if (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            return await this.ReadEntryAsync(dataReader, withEmbeddings, cancellationToken).ConfigureAwait(false);
        }

        return null;
    }

    /// <summary>
    /// Delete a entry by its key.
    /// </summary>
    /// <param name="collectionName">The name assigned to a collection of entries.</param>
    /// <param name="key">The key of the entry to delete.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public async Task DeleteAsync(string collectionName, string key, CancellationToken cancellationToken = default)
    {
        using NpgsqlConnection connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        using NpgsqlCommand cmd = connection.CreateCommand();
        cmd.CommandText = $"DELETE FROM {this.GetTableName(collectionName)} WHERE key=@key";
        cmd.Parameters.AddWithValue("@key", key);

        await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }

    #region private ================================================================================

    private readonly NpgsqlDataSource _dataSource;
    private readonly int _vectorSize;
    private readonly string _schema;
    private readonly int _numberOfLists;

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
        long? timestamp = await dataReader.GetFieldValueAsync<long?>(dataReader.GetOrdinal("timestamp"), cancellationToken).ConfigureAwait(false);
        return new PostgresMemoryEntry() { Key = key, MetadataString = metadata, Embedding = embedding, Timestamp = timestamp };
    }

    /// <summary>
    /// Create a collection as table.
    /// </summary>
    /// <param name="connection">An opened <see cref="NpgsqlConnection"/> instance.</param>
    /// <param name="collectionName">The name assigned to a collection of entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    private async Task CreateTableAsync(NpgsqlConnection connection, string collectionName, CancellationToken cancellationToken = default)
    {
        using NpgsqlCommand cmd = connection.CreateCommand();
        cmd.CommandText = $@"
            CREATE TABLE IF NOT EXISTS {this.GetTableName(collectionName)} (
                key TEXT NOT NULL,
                metadata JSONB,
                embedding vector({this._vectorSize}),
                timestamp BIGINT,
                PRIMARY KEY (key))";
        await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Create index for collection table.
    /// </summary>
    /// <param name="connection">An opened <see cref="NpgsqlConnection"/> instance.</param>
    /// <param name="collectionName">The name assigned to a collection of entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    private async Task CreateIndexAsync(NpgsqlConnection connection, string collectionName, CancellationToken cancellationToken = default)
    {
        using NpgsqlCommand cmd = connection.CreateCommand();
        cmd.CommandText = $@"
            CREATE INDEX IF NOT EXISTS {collectionName}_ix
            ON {this.GetTableName(collectionName)} USING ivfflat (embedding vector_cosine_ops) WITH (lists = {this._numberOfLists})";
        await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Get table name from collection name.
    /// </summary>
    /// <param name="collectionName"></param>
    /// <returns></returns>
    private string GetTableName(string collectionName)
    {
        return $"{this._schema}.\"{collectionName}\"";
    }
    #endregion
}
