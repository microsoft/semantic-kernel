// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Data;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Data.Sqlite;

namespace Microsoft.SemanticKernel.Connectors.Memory.Sqlite;

internal struct DatabaseEntry
{
    public string Key { get; set; }
    public string ValueString { get; set; }
    public string? Timestamp { get; set; }
}

internal static class Database
{
    private const string TableName = "SKMemoryTable";

    public static async Task<SqliteConnection> CreateConnectionAsync(string filename, CancellationToken cancel = default)
    {
        var connection = new SqliteConnection($"Data Source={filename};");
        await connection.OpenAsync(cancel);
        await CreateTableAsync(connection, cancel);
        return connection;
    }

    public static async Task CreateCollectionAsync(this SqliteConnection conn, string collectionName, CancellationToken cancel = default)
    {
        if (await DoesCollectionExistsAsync(conn, collectionName, cancel))
        {
            // Collection already exists
            return;
        }

        SqliteCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
             INSERT INTO {TableName}(collection)
             VALUES(@collection); ";
        cmd.Parameters.AddWithValue("@collection", collectionName);
        await cmd.ExecuteNonQueryAsync(cancel);
    }

    public static async Task UpdateAsync(this SqliteConnection conn,
        string collection, string key, string? value, string? timestamp, CancellationToken cancel = default)
    {
        SqliteCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
             UPDATE {TableName}
             SET value=@value, timestamp=@timestamp
             WHERE collection=@collection
                AND key=@key ";
        cmd.Parameters.AddWithValue("@collection", collection);
        cmd.Parameters.AddWithValue("@key", key);
        cmd.Parameters.AddWithValue("@value", value ?? string.Empty);
        cmd.Parameters.AddWithValue("@timestamp", timestamp ?? string.Empty);
        await cmd.ExecuteNonQueryAsync(cancel);
    }

    public static async Task InsertOrIgnoreAsync(this SqliteConnection conn,
        string collection, string key, string? value, string? timestamp, CancellationToken cancel = default)
    {
        SqliteCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
             INSERT OR IGNORE INTO {TableName}(collection, key, value, timestamp)
             VALUES(@collection, @key, @value, @timestamp); ";
        cmd.Parameters.AddWithValue("@collection", collection);
        cmd.Parameters.AddWithValue("@key", key);
        cmd.Parameters.AddWithValue("@value", value ?? string.Empty);
        cmd.Parameters.AddWithValue("@timestamp", timestamp ?? string.Empty);
        await cmd.ExecuteNonQueryAsync(cancel);
    }

    public static async Task<bool> DoesCollectionExistsAsync(this SqliteConnection conn,
        string collectionName,
        CancellationToken cancel = default)
    {
        var collections = await GetCollectionsAsync(conn, cancel).ToListAsync(cancel);
        return collections.Contains(collectionName);
    }

    public static async IAsyncEnumerable<string> GetCollectionsAsync(this SqliteConnection conn,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        SqliteCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
            SELECT DISTINCT(collection)
            FROM {TableName}";

        var dataReader = await cmd.ExecuteReaderAsync(cancel);
        while (await dataReader.ReadAsync(cancel))
        {
            yield return dataReader.GetFieldValue<string>("collection");
        }
    }

    public static async IAsyncEnumerable<DatabaseEntry> ReadAllAsync(this SqliteConnection conn,
        string collectionName,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        SqliteCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
            SELECT * FROM {TableName}
            WHERE collection=@collection";
        cmd.Parameters.AddWithValue("@collection", collectionName);

        var dataReader = await cmd.ExecuteReaderAsync(cancel);
        while (await dataReader.ReadAsync(cancel))
        {
            string key = dataReader.GetFieldValue<string>("key");
            string value = dataReader.GetFieldValue<string>("value");
            string timestamp = dataReader.GetFieldValue<string>("timestamp");
            yield return new DatabaseEntry() { Key = key, ValueString = value, Timestamp = timestamp };
        }
    }

    public static async Task<DatabaseEntry?> ReadAsync(this SqliteConnection conn,
        string collectionName,
        string key,
        CancellationToken cancel = default)
    {
        SqliteCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
             SELECT * FROM {TableName}
             WHERE collection=@collection
                AND key=@key ";
        cmd.Parameters.AddWithValue("@collection", collectionName);
        cmd.Parameters.AddWithValue("@key", key);

        var dataReader = await cmd.ExecuteReaderAsync(cancel);
        if (await dataReader.ReadAsync(cancel))
        {
            string value = dataReader.GetString(dataReader.GetOrdinal("value"));
            string timestamp = dataReader.GetString(dataReader.GetOrdinal("timestamp"));
            return new DatabaseEntry()
            {
                Key = key,
                ValueString = value,
                Timestamp = timestamp
            };
        }

        return null;
    }

    public static Task DeleteCollectionAsync(this SqliteConnection conn, string collectionName, CancellationToken cancel = default)
    {
        SqliteCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
             DELETE FROM {TableName}
             WHERE collection=@collection";
        cmd.Parameters.AddWithValue("@collection", collectionName);
        return cmd.ExecuteNonQueryAsync(cancel);
    }

    public static Task DeleteAsync(this SqliteConnection conn, string collectionName, string key, CancellationToken cancel = default)
    {
        SqliteCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
             DELETE FROM {TableName}
             WHERE collection=@collection
                AND key=@key ";
        cmd.Parameters.AddWithValue("@collection", collectionName);
        cmd.Parameters.AddWithValue("@key", key);
        return cmd.ExecuteNonQueryAsync(cancel);
    }

    public static Task DeleteEmptyAsync(this SqliteConnection conn, string collectionName, CancellationToken cancel = default)
    {
        SqliteCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
             DELETE FROM {TableName}
             WHERE collection=@collection
                AND key IS NULL";
        cmd.Parameters.AddWithValue("@collection", collectionName);
        return cmd.ExecuteNonQueryAsync(cancel);
    }

    private static Task CreateTableAsync(SqliteConnection conn, CancellationToken cancel = default)
    {
        SqliteCommand cmd = conn.CreateCommand();
        cmd.CommandText = $@"
            CREATE TABLE IF NOT EXISTS {TableName}(
                collection TEXT,
                key TEXT,
                value TEXT,
                timestamp TEXT,
                PRIMARY KEY(collection, key))";
        return cmd.ExecuteNonQueryAsync(cancel);
    }
}
