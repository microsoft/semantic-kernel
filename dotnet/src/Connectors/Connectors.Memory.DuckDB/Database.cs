// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using DuckDB.NET.Data;

namespace Microsoft.SemanticKernel.Connectors.Memory.DuckDB;

internal struct DatabaseEntry
{
    public string Key { get; set; }

    public string MetadataString { get; set; }

    public string EmbeddingString { get; set; }

    public string? Timestamp { get; set; }
}

internal sealed class Database
{
    private const string TableName = "SKMemoryTable";

    public Database() { }

    public Task CreateTableAsync(DuckDBConnection conn, CancellationToken cancellationToken = default)
    {
        using var cmd = conn.CreateCommand();
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

    public async Task CreateCollectionAsync(DuckDBConnection conn, string collectionName, CancellationToken cancellationToken = default)
    {
        if (await this.DoesCollectionExistsAsync(conn, collectionName, cancellationToken).ConfigureAwait(false))
        {
            // Collection already exists
            return;
        }

        using var cmd = conn.CreateCommand();
        cmd.CommandText = $@"
                INSERT INTO {TableName} VALUES (?1,?2,?3,?4,?5 ); ";
        cmd.Parameters.Add(new DuckDBParameter(collectionName));
        cmd.Parameters.Add(new DuckDBParameter(string.Empty));
        cmd.Parameters.Add(new DuckDBParameter(string.Empty));
        cmd.Parameters.Add(new DuckDBParameter(string.Empty));
        cmd.Parameters.Add(new DuckDBParameter(string.Empty));

        await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }

    public async Task UpdateOrInsertAsync(DuckDBConnection conn,
        string collection, string key, string? metadata, string? embedding, string? timestamp, CancellationToken cancellationToken = default)
    {
        using var cmd = conn.CreateCommand();
        cmd.CommandText = $@"
             INSERT INTO {TableName} VALUES(?1, ?2, ?3, ?4, ?5)
             ON CONFLICT (collection, key) DO UPDATE SET metadata=?3, embedding=?4, timestamp=?5; ";
        cmd.Parameters.Add(new DuckDBParameter(collection));
        cmd.Parameters.Add(new DuckDBParameter(key));
        cmd.Parameters.Add(new DuckDBParameter(metadata ?? string.Empty));
        cmd.Parameters.Add(new DuckDBParameter(embedding ?? string.Empty));
        cmd.Parameters.Add(new DuckDBParameter(timestamp ?? string.Empty));
        await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }

    public async Task<bool> DoesCollectionExistsAsync(DuckDBConnection conn,
        string collectionName,
        CancellationToken cancellationToken = default)
    {
        var collections = await this.GetCollectionsAsync(conn, cancellationToken).ToListAsync(cancellationToken).ConfigureAwait(false);
        return collections.Contains(collectionName);
    }

    public async IAsyncEnumerable<string> GetCollectionsAsync(DuckDBConnection conn,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using var cmd = conn.CreateCommand();
        cmd.CommandText = $@"
            SELECT DISTINCT collection 
            FROM {TableName};";

        using var dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
        while (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            yield return dataReader.GetString("collection");
        }
    }

    public async IAsyncEnumerable<DatabaseEntry> ReadAllAsync(DuckDBConnection conn,
        string collectionName,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using var cmd = conn.CreateCommand();
        cmd.CommandText = $@"
            SELECT * FROM {TableName}
            WHERE collection=?1;";
        cmd.Parameters.Add(new DuckDBParameter(collectionName));

        using var dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
        while (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            string key = dataReader.GetString("key");
            if (string.IsNullOrWhiteSpace(key))
            {
                continue;
            }
            string metadata = dataReader.GetString("metadata");
            string embedding = dataReader.GetString("embedding");
            string timestamp = dataReader.GetString("timestamp");
            yield return new DatabaseEntry() { Key = key, MetadataString = metadata, EmbeddingString = embedding, Timestamp = timestamp };
        }
    }

    public async Task<DatabaseEntry?> ReadAsync(DuckDBConnection conn,
        string collectionName,
        string key,
        CancellationToken cancellationToken = default)
    {
        using var cmd = conn.CreateCommand();
        cmd.CommandText = $@"
             SELECT * FROM {TableName}
             WHERE collection=?1
                AND key=?2; ";
        cmd.Parameters.Add(new DuckDBParameter(collectionName));
        cmd.Parameters.Add(new DuckDBParameter(key));

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

    public Task DeleteCollectionAsync(DuckDBConnection conn, string collectionName, CancellationToken cancellationToken = default)
    {
        using var cmd = conn.CreateCommand();
        cmd.CommandText = $@"
             DELETE FROM {TableName}
             WHERE collection=?;";
        cmd.Parameters.Add(new DuckDBParameter(collectionName));
        return cmd.ExecuteNonQueryAsync(cancellationToken);
    }

    public Task DeleteAsync(DuckDBConnection conn, string collectionName, string key, CancellationToken cancellationToken = default)
    {
        using var cmd = conn.CreateCommand();
        cmd.CommandText = $@"
             DELETE FROM {TableName}
             WHERE collection=?1
                AND key=?2; ";
        cmd.Parameters.Add(new DuckDBParameter(collectionName));
        cmd.Parameters.Add(new DuckDBParameter(key));
        return cmd.ExecuteNonQueryAsync(cancellationToken);
    }

    public Task DeleteEmptyAsync(DuckDBConnection conn, string collectionName, CancellationToken cancellationToken = default)
    {
        using var cmd = conn.CreateCommand();
        cmd.CommandText = $@"
             DELETE FROM {TableName}
             WHERE collection=?1
                AND key IS NULL";
        cmd.Parameters.Add(new DuckDBParameter(collectionName));
        return cmd.ExecuteNonQueryAsync(cancellationToken);
    }
}
