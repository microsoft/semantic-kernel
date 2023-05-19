// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Npgsql;
using Pgvector;

namespace Microsoft.SemanticKernel.Connectors.Memory.Postgres;

/// <summary>
/// A postgres memory entry.
/// </summary>
internal struct DatabaseEntry
{
    /// <summary>
    /// Unique identifier of the memory entry.
    /// </summary>
    public string Key { get; set; }

    /// <summary>
    /// Metadata as a string.
    /// </summary>
    public string MetadataString { get; set; }

    /// <summary>
    /// The embedding data as a <see cref="Vector"/>.
    /// </summary>
    public Vector? Embedding { get; set; }

    /// <summary>
    /// Optional timestamp.
    /// </summary>
    public long? Timestamp { get; set; }
}

/// <summary>
/// The class for managing postgres database operations.
/// </summary>
internal sealed class Database
{
    private const string TableName = "sk_memory_table";

    /// <summary>
    /// Create pgvector extensions.
    /// </summary>
    /// <param name="conn">An opened <see cref="NpgsqlConnection"/> instance.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public async Task CreatePgVectorExtensionAsync(NpgsqlConnection conn, CancellationToken cancellationToken = default)
    {
        using NpgsqlCommand cmd = conn.CreateCommand();
        cmd.CommandText = "CREATE EXTENSION IF NOT EXISTS vector";
        await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        await conn.ReloadTypesAsync().ConfigureAwait(false);
    }

    /// <summary>
    /// Create memory table.
    /// </summary>
    /// <param name="conn">An opened <see cref="NpgsqlConnection"/> instance.</param>
    /// <param name="vectorSize">Vector size of embedding column</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public async Task CreateTableAsync(NpgsqlConnection conn, int vectorSize, CancellationToken cancellationToken = default)
    {
        await this.CreatePgVectorExtensionAsync(conn, cancellationToken).ConfigureAwait(false);

        using NpgsqlCommand cmd = conn.CreateCommand();
#pragma warning disable CA2100 // Review SQL queries for security vulnerabilities
        cmd.CommandText = $@"
            CREATE TABLE IF NOT EXISTS {TableName} (
                collection TEXT,
                key TEXT,
                metadata TEXT,
                embedding vector({vectorSize}),
                timestamp BIGINT,
                PRIMARY KEY(collection, key))";
#pragma warning restore CA2100 // Review SQL queries for security vulnerabilities
        await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Create index for memory table.
    /// </summary>
    /// <param name="conn">An opened <see cref="NpgsqlConnection"/> instance.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public async Task CreateIndexAsync(NpgsqlConnection conn, CancellationToken cancellationToken = default)
    {
        using NpgsqlCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
            CREATE INDEX IF NOT EXISTS {TableName}_ivfflat_embedding_vector_cosine_ops_idx
            ON {TableName} USING ivfflat (embedding vector_cosine_ops) WITH (lists = 1000)";
        await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Create a collection.
    /// </summary>
    /// <param name="conn">An opened <see cref="NpgsqlConnection"/> instance.</param>
    /// <param name="collectionName">The name assigned to a collection of entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public async Task CreateCollectionAsync(NpgsqlConnection conn, string collectionName, CancellationToken cancellationToken = default)
    {
        if (await this.DoesCollectionExistsAsync(conn, collectionName, cancellationToken).ConfigureAwait(false))
        {
            // Collection already exists
            return;
        }

        using NpgsqlCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
            INSERT INTO {TableName} (collection, key)
            VALUES(@collection, '')";
        cmd.Parameters.AddWithValue("@collection", collectionName);
        await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Upsert entry into a collection.
    /// </summary>
    /// <param name="conn">An opened <see cref="NpgsqlConnection"/> instance.</param>
    /// <param name="collectionName">The name assigned to a collection of entries.</param>
    /// <param name="key">The key of the entry to upsert.</param>
    /// <param name="metadata">The metadata of the entry.</param>
    /// <param name="embedding">The embedding of the entry.</param>
    /// <param name="timestamp">The timestamp of the entry</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public async Task UpsertAsync(NpgsqlConnection conn,
        string collectionName, string key, string? metadata, Vector? embedding, long? timestamp, CancellationToken cancellationToken = default)
    {
        using NpgsqlCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
            INSERT INTO {TableName} (collection, key, metadata, embedding, timestamp)
            VALUES(@collection, @key, @metadata, @embedding, @timestamp)
            ON CONFLICT (collection, key)
            DO UPDATE SET metadata=@metadata, embedding=@embedding, timestamp=@timestamp";
        cmd.Parameters.AddWithValue("@collection", collectionName);
        cmd.Parameters.AddWithValue("@key", key);
        cmd.Parameters.AddWithValue("@metadata", metadata ?? string.Empty);
        cmd.Parameters.AddWithValue("@embedding", embedding ?? (object)DBNull.Value);
        cmd.Parameters.AddWithValue("@timestamp", timestamp ?? (object)DBNull.Value);
        await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Check if a collection exists.
    /// </summary>
    /// <param name="conn">An opened <see cref="NpgsqlConnection"/> instance.</param>
    /// <param name="collectionName">The name assigned to a collection of entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public async Task<bool> DoesCollectionExistsAsync(NpgsqlConnection conn,
        string collectionName,
        CancellationToken cancellationToken = default)
    {
        var collections = await this.GetCollectionsAsync(conn, cancellationToken).ToListAsync(cancellationToken).ConfigureAwait(false);
        return collections.Contains(collectionName);
    }

    /// <summary>
    /// Get all collections.
    /// </summary>
    /// <param name="conn">An opened <see cref="NpgsqlConnection"/> instance.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public async IAsyncEnumerable<string> GetCollectionsAsync(NpgsqlConnection conn,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using NpgsqlCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
            SELECT DISTINCT(collection)
            FROM {TableName}";

        using var dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
        while (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            yield return dataReader.GetString(dataReader.GetOrdinal("collection"));
        }
    }

    /// <summary>
    /// Gets the nearest matches to the <see cref="Vector"/>.
    /// </summary>
    /// <param name="conn">An opened <see cref="NpgsqlConnection"/> instance.</param>
    /// <param name="collectionName">The name assigned to a collection of entries.</param>
    /// <param name="embeddingFilter">The <see cref="Vector"/> to compare the collection's embeddings with.</param>
    /// <param name="limit">The maximum number of similarity results to return.</param>
    /// <param name="minRelevanceScore">The minimum relevance threshold for returned results.</param>
    /// <param name="withEmbeddings">If true, the embeddings will be returned in the entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public async IAsyncEnumerable<(DatabaseEntry, double)> GetNearestMatchesAsync(NpgsqlConnection conn,
        string collectionName, Vector embeddingFilter, int limit, double minRelevanceScore = 0, bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var queryColumns = "collection, key, metadata, timestamp";
        if (withEmbeddings)
        {
            queryColumns = "*";
        }

        using NpgsqlCommand cmd = conn.CreateCommand();
        cmd.CommandText = @$"
            SELECT * FROM (SELECT {queryColumns}, 1 - (embedding <=> @embedding) AS cosine_similarity FROM {TableName}
                WHERE collection = @collection
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
    /// Read all entries from a collection
    /// </summary>
    /// <param name="conn">An opened <see cref="NpgsqlConnection"/> instance.</param>
    /// <param name="collectionName">The name assigned to a collection of entries.</param>
    /// <param name="withEmbeddings">If true, the embeddings will be returned in the entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public async IAsyncEnumerable<DatabaseEntry> ReadAllAsync(NpgsqlConnection conn,
        string collectionName, bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var queryColumns = "collection, key, metadata, timestamp";
        if (withEmbeddings)
        {
            queryColumns = "*";
        }

        using NpgsqlCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
            SELECT {queryColumns} FROM {TableName}
            WHERE collection=@collection";
        cmd.Parameters.AddWithValue("@collection", collectionName);

        using var dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
        while (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            yield return await this.ReadEntryAsync(dataReader, withEmbeddings, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <summary>
    /// Read a entry by its key.
    /// </summary>
    /// <param name="conn">An opened <see cref="NpgsqlConnection"/> instance.</param>
    /// <param name="collectionName">The name assigned to a collection of entries.</param>
    /// <param name="key">The key of the entry to read.</param>
    /// <param name="withEmbeddings">If true, the embeddings will be returned in the entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public async Task<DatabaseEntry?> ReadAsync(NpgsqlConnection conn,
        string collectionName, string key, bool withEmbeddings = false,
        CancellationToken cancellationToken = default)
    {
        var queryColumns = "collection, key, metadata, timestamp";
        if (withEmbeddings)
        {
            queryColumns = "*";
        }

        using NpgsqlCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
            SELECT {queryColumns} FROM {TableName}
            WHERE collection=@collection AND key=@key";
        cmd.Parameters.AddWithValue("@collection", collectionName);
        cmd.Parameters.AddWithValue("@key", key);

        using var dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
        if (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            return await this.ReadEntryAsync(dataReader, withEmbeddings, cancellationToken).ConfigureAwait(false);
        }

        return null;
    }

    /// <summary>
    /// Delete a collection.
    /// </summary>
    /// <param name="conn">An opened <see cref="NpgsqlConnection"/> instance.</param>
    /// <param name="collectionName">The name assigned to a collection of entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public Task DeleteCollectionAsync(NpgsqlConnection conn, string collectionName, CancellationToken cancellationToken = default)
    {
        using NpgsqlCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
            DELETE FROM {TableName}
            WHERE collection=@collection";
        cmd.Parameters.AddWithValue("@collection", collectionName);
        return cmd.ExecuteNonQueryAsync(cancellationToken);
    }

    /// <summary>
    /// Delete a entry by its key.
    /// </summary>
    /// <param name="conn">An opened <see cref="NpgsqlConnection"/> instance.</param>
    /// <param name="collectionName">The name assigned to a collection of entries.</param>
    /// <param name="key">The key of the entry to delete.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public Task DeleteAsync(NpgsqlConnection conn, string collectionName, string key, CancellationToken cancellationToken = default)
    {
        using NpgsqlCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
            DELETE FROM {TableName}
            WHERE collection=@collection AND key=@key ";
        cmd.Parameters.AddWithValue("@collection", collectionName);
        cmd.Parameters.AddWithValue("@key", key);
        return cmd.ExecuteNonQueryAsync(cancellationToken);
    }

    /// <summary>
    /// Read a entry.
    /// </summary>
    /// <param name="dataReader">The <see cref="NpgsqlDataReader"/> to read.</param>
    /// <param name="withEmbeddings">If true, the embeddings will be returned in the entries.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    private async Task<DatabaseEntry> ReadEntryAsync(NpgsqlDataReader dataReader, bool withEmbeddings = false, CancellationToken cancellationToken = default)
    {
        string key = dataReader.GetString(dataReader.GetOrdinal("key"));
        string metadata = dataReader.GetString(dataReader.GetOrdinal("metadata"));
        Vector? embedding = withEmbeddings ? await dataReader.GetFieldValueAsync<Vector>(dataReader.GetOrdinal("embedding"), cancellationToken).ConfigureAwait(false) : null;
        long? timestamp = await dataReader.GetFieldValueAsync<long?>(dataReader.GetOrdinal("timestamp"), cancellationToken).ConfigureAwait(false);
        return new DatabaseEntry() { Key = key, MetadataString = metadata, Embedding = embedding, Timestamp = timestamp };
    }
}
