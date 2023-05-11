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

internal struct DatabaseEntry
{
    public string Key { get; set; }

    public string MetadataString { get; set; }

    public Vector? Embedding { get; set; }

    public long? Timestamp { get; set; }
}

internal sealed class Database
{
    private const string TableName = "sk_memory_table";

    public Database() { }

    public async Task CreatePgVectorExtensionAsync(NpgsqlConnection conn, CancellationToken cancellationToken = default)
    {
        using NpgsqlCommand cmd = conn.CreateCommand();
        cmd.CommandText = "CREATE EXTENSION IF NOT EXISTS vector";
        await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        await conn.ReloadTypesAsync().ConfigureAwait(false);
    }

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

    public async Task CreateIndexAsync(NpgsqlConnection conn, CancellationToken cancellationToken = default)
    {
        using NpgsqlCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
            CREATE INDEX IF NOT EXISTS {TableName}_ivfflat_embedding_vector_cosine_ops_idx
            ON {TableName} USING ivfflat (embedding vector_cosine_ops) WITH (lists = 1000)";
        await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }

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

    public async Task InsertOrUpdateAsync(NpgsqlConnection conn,
        string collection, string key, string? metadata, Vector? embedding, long? timestamp, CancellationToken cancellationToken = default)
    {
        using NpgsqlCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
            INSERT INTO {TableName} (collection, key, metadata, embedding, timestamp)
            VALUES(@collection, @key, @metadata, @embedding, @timestamp)
            ON CONFLICT (collection, key)
            DO UPDATE SET metadata=@metadata, embedding=@embedding, timestamp=@timestamp";
        cmd.Parameters.AddWithValue("@collection", collection);
        cmd.Parameters.AddWithValue("@key", key);
        cmd.Parameters.AddWithValue("@metadata", metadata ?? string.Empty);
        cmd.Parameters.AddWithValue("@embedding", embedding ?? (object)DBNull.Value);
        cmd.Parameters.AddWithValue("@timestamp", timestamp ?? (object)DBNull.Value);
        await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }

    public async Task<bool> DoesCollectionExistsAsync(NpgsqlConnection conn,
        string collectionName,
        CancellationToken cancellationToken = default)
    {
        var collections = await this.GetCollectionsAsync(conn, cancellationToken).ToListAsync(cancellationToken).ConfigureAwait(false);
        return collections.Contains(collectionName);
    }

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

    public Task DeleteCollectionAsync(NpgsqlConnection conn, string collectionName, CancellationToken cancellationToken = default)
    {
        using NpgsqlCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
            DELETE FROM {TableName}
            WHERE collection=@collection";
        cmd.Parameters.AddWithValue("@collection", collectionName);
        return cmd.ExecuteNonQueryAsync(cancellationToken);
    }

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

    private async Task<DatabaseEntry> ReadEntryAsync(NpgsqlDataReader dataReader, bool withEmbeddings = false, CancellationToken cancellationToken = default)
    {
        string key = dataReader.GetString(dataReader.GetOrdinal("key"));
        string metadata = dataReader.GetString(dataReader.GetOrdinal("metadata"));
        Vector? embedding = withEmbeddings ? await dataReader.GetFieldValueAsync<Vector>(dataReader.GetOrdinal("embedding"), cancellationToken).ConfigureAwait(false) : null;
        long? timestamp = await dataReader.GetFieldValueAsync<long?>(dataReader.GetOrdinal("timestamp"), cancellationToken).ConfigureAwait(false);
        return new DatabaseEntry() { Key = key, MetadataString = metadata, Embedding = embedding, Timestamp = timestamp };
    }
}
