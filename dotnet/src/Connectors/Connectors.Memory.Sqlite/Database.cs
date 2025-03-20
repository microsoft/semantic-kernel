// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Data.Sqlite;

namespace Microsoft.SemanticKernel.Connectors.Sqlite;

[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and SqliteVectorStore")]
internal struct DatabaseEntry
{
    public string Key { get; set; }

    public string MetadataString { get; set; }

    public string EmbeddingString { get; set; }

    public string? Timestamp { get; set; }
}

[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and SqliteVectorStore")]
internal sealed class Database
{
    private const string TableName = "SKMemoryTable";

    public Database() { }

    public Task CreateTableAsync(SqliteConnection conn, CancellationToken cancellationToken = default)
    {
        using SqliteCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
            CREATE TABLE IF NOT EXISTS {TableName}(
                collection TEXT,
                key TEXT,
                metadata TEXT,
                embedding TEXT,
                timestamp TEXT,
                PRIMARY KEY(collection, key))";
        return cmd.ExecuteNonQueryAsync(cancellationToken);
    }

    public async Task CreateCollectionAsync(SqliteConnection conn, string collectionName, CancellationToken cancellationToken = default)
    {
        if (await this.DoesCollectionExistsAsync(conn, collectionName, cancellationToken).ConfigureAwait(false))
        {
            // Collection already exists
            return;
        }

        using SqliteCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
             INSERT INTO {TableName}(collection)
             VALUES(@collection); ";
        cmd.Parameters.AddWithValue("@collection", collectionName);
        await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }

    public async Task UpsertAsync(SqliteConnection conn,
        string collection, string key, string? metadata, string? embedding, string? timestamp, CancellationToken cancellationToken = default)
    {
        using SqliteCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
        INSERT OR REPLACE INTO {TableName}(collection, key, metadata, embedding, timestamp)
        VALUES(@collection, @key, @metadata, @embedding, @timestamp);";
        cmd.Parameters.AddWithValue("@collection", collection);
        cmd.Parameters.AddWithValue("@key", key);
        cmd.Parameters.AddWithValue("@metadata", metadata ?? string.Empty);
        cmd.Parameters.AddWithValue("@embedding", embedding ?? string.Empty);
        cmd.Parameters.AddWithValue("@timestamp", timestamp ?? string.Empty);
        await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }

    public async Task<bool> DoesCollectionExistsAsync(SqliteConnection conn,
        string collectionName,
        CancellationToken cancellationToken = default)
    {
        var collections = await this.GetCollectionsAsync(conn, cancellationToken).ToListAsync(cancellationToken).ConfigureAwait(false);
        return collections.Contains(collectionName);
    }

    public async IAsyncEnumerable<string> GetCollectionsAsync(SqliteConnection conn,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using SqliteCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
            SELECT DISTINCT(collection)
            FROM {TableName}";

        using var dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
        while (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            yield return dataReader.GetString("collection");
        }
    }

    public async IAsyncEnumerable<DatabaseEntry> ReadAllAsync(SqliteConnection conn,
        string collectionName,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using SqliteCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
            SELECT * FROM {TableName}
            WHERE collection=@collection";
        cmd.Parameters.AddWithValue("@collection", collectionName);

        using var dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
        while (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            string key = dataReader.GetString("key");
            string metadata = dataReader.GetString("metadata");
            string embedding = dataReader.GetString("embedding");
            string timestamp = dataReader.GetString("timestamp");
            yield return new DatabaseEntry() { Key = key, MetadataString = metadata, EmbeddingString = embedding, Timestamp = timestamp };
        }
    }

    public async Task<DatabaseEntry?> ReadAsync(SqliteConnection conn,
        string collectionName,
        string key,
        CancellationToken cancellationToken = default)
    {
        using SqliteCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
             SELECT * FROM {TableName}
             WHERE collection=@collection
                AND key=@key ";
        cmd.Parameters.AddWithValue("@collection", collectionName);
        cmd.Parameters.AddWithValue("@key", key);

        using var dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
        if (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            string metadata = dataReader.GetString(dataReader.GetOrdinal("metadata"));
            string embedding = dataReader.GetString(dataReader.GetOrdinal("embedding"));
            string timestamp = dataReader.GetString(dataReader.GetOrdinal("timestamp"));
            return new DatabaseEntry()
            {
                Key = key,
                MetadataString = metadata,
                EmbeddingString = embedding,
                Timestamp = timestamp
            };
        }

        return null;
    }

    public async IAsyncEnumerable<DatabaseEntry> ReadBatchAsync(SqliteConnection conn,
    string collectionName,
    string[] keys,
    bool withEmbeddings = false,
    [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using SqliteCommand cmd = conn.CreateCommand();
        var keyParameters = keys.Select((key, index) => $"@key{index}");
        var parameters = string.Join(", ", keyParameters);

        var selectFieldQuery = withEmbeddings ? "*" : "key, metadata, timestamp";
#pragma warning disable CA2100 // Review SQL queries for security vulnerabilities
        cmd.CommandText = $@"
             SELECT {selectFieldQuery} FROM {TableName}
             WHERE collection=@collection
                AND key IN ({parameters})";
#pragma warning restore CA2100 // Review SQL queries for security vulnerabilities

        cmd.Parameters.Add(new SqliteParameter("@collection", collectionName));
        for (int i = 0; i < keys.Length; i++)
        {
            cmd.Parameters.Add(new SqliteParameter($"@key{i}", keys[i]));
        }

        using var dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
        while (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            string key = dataReader.GetString("key");
            string metadata = dataReader.GetString("metadata");
            string embedding = withEmbeddings ? dataReader.GetString("embedding") : string.Empty;
            string timestamp = dataReader.GetString("timestamp");
            yield return new DatabaseEntry() { Key = key, MetadataString = metadata, EmbeddingString = embedding, Timestamp = timestamp };
        }
    }

    public Task DeleteCollectionAsync(SqliteConnection conn, string collectionName, CancellationToken cancellationToken = default)
    {
        using SqliteCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
             DELETE FROM {TableName}
             WHERE collection=@collection";
        cmd.Parameters.AddWithValue("@collection", collectionName);
        return cmd.ExecuteNonQueryAsync(cancellationToken);
    }

    public Task DeleteAsync(SqliteConnection conn, string collectionName, string key, CancellationToken cancellationToken = default)
    {
        using SqliteCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
             DELETE FROM {TableName}
             WHERE collection=@collection
                AND key=@key ";
        cmd.Parameters.AddWithValue("@collection", collectionName);
        cmd.Parameters.AddWithValue("@key", key);
        return cmd.ExecuteNonQueryAsync(cancellationToken);
    }

    public Task DeleteBatchAsync(SqliteConnection conn, string collectionName, string[] keys, CancellationToken cancellationToken = default)
    {
        using SqliteCommand cmd = conn.CreateCommand();
        var keyParameters = keys.Select((key, index) => $"@key{index}");
        var parameters = string.Join(", ", keyParameters);

#pragma warning disable CA2100 // Review SQL queries for security vulnerabilities
        cmd.CommandText = $@"
         DELETE FROM {TableName}
         WHERE collection=@collection
            AND key IN ({parameters})";
#pragma warning restore CA2100 // Review SQL queries for security vulnerabilities

        cmd.Parameters.Add(new SqliteParameter("@collection", collectionName));
        for (int i = 0; i < keys.Length; i++)
        {
            cmd.Parameters.Add(new SqliteParameter($"@key{i}", keys[i]));
        }
        return cmd.ExecuteNonQueryAsync(cancellationToken);
    }

    public Task DeleteEmptyAsync(SqliteConnection conn, string collectionName, CancellationToken cancellationToken = default)
    {
        using SqliteCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
             DELETE FROM {TableName}
             WHERE collection=@collection
                AND key IS NULL";
        cmd.Parameters.AddWithValue("@collection", collectionName);
        return cmd.ExecuteNonQueryAsync(cancellationToken);
    }
}
