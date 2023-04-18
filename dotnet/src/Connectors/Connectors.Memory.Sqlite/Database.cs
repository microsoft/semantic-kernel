// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Data.Sqlite;

namespace Microsoft.SemanticKernel.Connectors.Memory.Sqlite;

internal struct DatabaseEntry
{
    public string Key { get; set; }

    public string MetadataString { get; set; }

    public string EmbeddingString { get; set; }

    public string? Timestamp { get; set; }
}

internal class Database
{
    private const string TableName = "SKMemoryTable";

    public Database() { }

    public Task CreateTableAsync(SqliteConnection conn, CancellationToken cancel = default)
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
        return cmd.ExecuteNonQueryAsync(cancel);
    }

    public async Task CreateCollectionAsync(SqliteConnection conn, string collectionName, CancellationToken cancel = default)
    {
        if (await this.DoesCollectionExistsAsync(conn, collectionName, cancel))
        {
            // Collection already exists
            return;
        }

        using SqliteCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
             INSERT INTO {TableName}(collection)
             VALUES(@collection); ";
        cmd.Parameters.AddWithValue("@collection", collectionName);
        await cmd.ExecuteNonQueryAsync(cancel);
    }

    public async Task UpdateAsync(SqliteConnection conn,
        string collection, string key, string? metadata, string? embedding, string? timestamp, CancellationToken cancel = default)
    {
        using SqliteCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
             UPDATE {TableName}
             SET metadata=@metadata, embedding=@embedding, timestamp=@timestamp
             WHERE collection=@collection
                AND key=@key ";
        cmd.Parameters.AddWithValue("@collection", collection);
        cmd.Parameters.AddWithValue("@key", key);
        cmd.Parameters.AddWithValue("@metadata", metadata ?? string.Empty);
        cmd.Parameters.AddWithValue("@embedding", embedding ?? string.Empty);
        cmd.Parameters.AddWithValue("@timestamp", timestamp ?? string.Empty);
        await cmd.ExecuteNonQueryAsync(cancel);
    }

    public async Task InsertOrIgnoreAsync(SqliteConnection conn,
        string collection, string key, string? metadata, string? embedding, string? timestamp, CancellationToken cancel = default)
    {
        using SqliteCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
             INSERT OR IGNORE INTO {TableName}(collection, key, metadata, embedding, timestamp)
             VALUES(@collection, @key, @metadata, @embedding, @timestamp); ";
        cmd.Parameters.AddWithValue("@collection", collection);
        cmd.Parameters.AddWithValue("@key", key);
        cmd.Parameters.AddWithValue("@metadata", metadata ?? string.Empty);
        cmd.Parameters.AddWithValue("@embedding", embedding ?? string.Empty);
        cmd.Parameters.AddWithValue("@timestamp", timestamp ?? string.Empty);
        await cmd.ExecuteNonQueryAsync(cancel);
    }

    public async Task<bool> DoesCollectionExistsAsync(SqliteConnection conn,
        string collectionName,
        CancellationToken cancel = default)
    {
        var collections = await this.GetCollectionsAsync(conn, cancel).ToListAsync(cancel);
        return collections.Contains(collectionName);
    }

    public async IAsyncEnumerable<string> GetCollectionsAsync(SqliteConnection conn,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        using SqliteCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
            SELECT DISTINCT(collection)
            FROM {TableName}";

        using var dataReader = await cmd.ExecuteReaderAsync(cancel);
        while (await dataReader.ReadAsync(cancel))
        {
            yield return dataReader.GetString("collection");
        }
    }

    public async IAsyncEnumerable<DatabaseEntry> ReadAllAsync(SqliteConnection conn,
        string collectionName,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        using SqliteCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
            SELECT * FROM {TableName}
            WHERE collection=@collection";
        cmd.Parameters.AddWithValue("@collection", collectionName);

        using var dataReader = await cmd.ExecuteReaderAsync(cancel);
        while (await dataReader.ReadAsync(cancel))
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
        CancellationToken cancel = default)
    {
        using SqliteCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
             SELECT * FROM {TableName}
             WHERE collection=@collection
                AND key=@key ";
        cmd.Parameters.AddWithValue("@collection", collectionName);
        cmd.Parameters.AddWithValue("@key", key);

        using var dataReader = await cmd.ExecuteReaderAsync(cancel);
        if (await dataReader.ReadAsync(cancel))
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

    public Task DeleteCollectionAsync(SqliteConnection conn, string collectionName, CancellationToken cancel = default)
    {
        using SqliteCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
             DELETE FROM {TableName}
             WHERE collection=@collection";
        cmd.Parameters.AddWithValue("@collection", collectionName);
        return cmd.ExecuteNonQueryAsync(cancel);
    }

    public Task DeleteAsync(SqliteConnection conn, string collectionName, string key, CancellationToken cancel = default)
    {
        using SqliteCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
             DELETE FROM {TableName}
             WHERE collection=@collection
                AND key=@key ";
        cmd.Parameters.AddWithValue("@collection", collectionName);
        cmd.Parameters.AddWithValue("@key", key);
        return cmd.ExecuteNonQueryAsync(cancel);
    }

    public Task DeleteEmptyAsync(SqliteConnection conn, string collectionName, CancellationToken cancel = default)
    {
        using SqliteCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
             DELETE FROM {TableName}
             WHERE collection=@collection
                AND key IS NULL";
        cmd.Parameters.AddWithValue("@collection", collectionName);
        return cmd.ExecuteNonQueryAsync(cancel);
    }
}
