// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
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

    public float[] Embedding { get; set; }

    public string? Timestamp { get; set; }

    public float Score { get; set; }
}

internal sealed class Database
{
    private const string TableName = "SKMemoryTable";

    public async Task CreateTableAsync(DuckDBConnection conn, CancellationToken cancellationToken = default)
    {
        using var cmd = conn.CreateCommand();
        cmd.CommandText = $@"
            CREATE TABLE IF NOT EXISTS {TableName}(
                collection TEXT,
                key TEXT,
                metadata TEXT,
                embedding FLOAT[],
                timestamp TEXT,
                PRIMARY KEY(collection, key))";
        await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
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
                INSERT INTO {TableName} VALUES (?1,?2,?3, [], ?4 ); ";
        cmd.Parameters.Add(new DuckDBParameter(collectionName));
        cmd.Parameters.Add(new DuckDBParameter(string.Empty));
        cmd.Parameters.Add(new DuckDBParameter(string.Empty));
        cmd.Parameters.Add(new DuckDBParameter(string.Empty));

        await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }

    private static string EncodeFloatArrayToString(float[]? data)
    {
        var dataArrayString = $"[{string.Join(", ", (data ?? Array.Empty<float>()).Select(n => n.ToString("F10", CultureInfo.InvariantCulture)))}]";
        return dataArrayString;
    }

    [System.Diagnostics.CodeAnalysis.SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities", Justification = "Internal method serializing array of float and numbers")]
    public async Task UpdateOrInsertAsync(DuckDBConnection conn,
        string collection, string key, string? metadata, float[]? embedding, string? timestamp, CancellationToken cancellationToken = default)
    {
        await this.DeleteAsync(conn, collection, key, cancellationToken).ConfigureAwait(true);
        var embeddingArrayString = EncodeFloatArrayToString(embedding ?? Array.Empty<float>());
        using var cmd = conn.CreateCommand();
        cmd.CommandText = $"INSERT INTO {TableName} VALUES(?1, ?2, ?3, {embeddingArrayString}, ?4)";
        cmd.Parameters.Add(new DuckDBParameter(collection));
        cmd.Parameters.Add(new DuckDBParameter(key));
        cmd.Parameters.Add(new DuckDBParameter(metadata ?? string.Empty));
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

    [System.Diagnostics.CodeAnalysis.SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities", Justification = "Internal method serializing array of float and numbers")]
    public async IAsyncEnumerable<DatabaseEntry> GetNearestMatchesAsync(
        DuckDBConnection conn,
        string collectionName,
        float[] embedding,
        int limit,
        double minRelevanceScore = 0,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var embeddingArrayString = EncodeFloatArrayToString(embedding);

        using var cmd = conn.CreateCommand();
        cmd.CommandText = $@"
            SELECT key, metadata, timestamp, embedding, (embedding <=> {embeddingArrayString}) as score FROM {TableName}
            WHERE collection=?1 AND len(embedding) > 0 AND score >= {minRelevanceScore.ToString("F12", CultureInfo.InvariantCulture)}
            ORDER BY score DESC
            LIMIT ?2;";

        cmd.Parameters.Add(new DuckDBParameter(collectionName));
        cmd.Parameters.Add(new DuckDBParameter(limit));

        using var dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
        while (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            string key = dataReader.GetFieldValue<string>("key");
            if (string.IsNullOrWhiteSpace(key))
            {
                continue;
            }

            string metadata = dataReader.GetFieldValue<string?>("metadata") ?? string.Empty;
            float[] embeddingFromSearch = (dataReader.GetFieldValue<List<float>?>("embedding")?.ToArray()) ?? Array.Empty<float>();
            string timestamp = dataReader.GetFieldValue<string?>("timestamp") ?? string.Empty;
            float score = dataReader.GetFieldValue<float?>("score") ?? 0f;

            yield return new DatabaseEntry
            {
                Key = key,
                MetadataString = metadata,
                Embedding = embeddingFromSearch,
                Timestamp = timestamp,
                Score = score
            };
        }
    }

    public async Task<DatabaseEntry?> ReadAsync(DuckDBConnection conn,
        string collectionName,
        string key,
        CancellationToken cancellationToken = default)
    {
        using var cmd = conn.CreateCommand();
        cmd.CommandText = $@"
             SELECT metadata, timestamp, embedding FROM {TableName}
             WHERE collection=?1
                AND key=?2; ";
        cmd.Parameters.Add(new DuckDBParameter(collectionName));
        cmd.Parameters.Add(new DuckDBParameter(key));

        using var dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
        if (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            string metadata = dataReader.GetFieldValue<string?>("metadata") ?? string.Empty;
            float[] embeddingFromSearch = (dataReader.GetFieldValue<List<float>?>("embedding")?.ToArray()) ?? Array.Empty<float>();
            string timestamp = dataReader.GetFieldValue<string?>("timestamp") ?? string.Empty;

            return new DatabaseEntry
            {
                Key = key,
                MetadataString = metadata,
                Embedding = embeddingFromSearch,
                Timestamp = timestamp
            };
        }

        return null;
    }

    public async Task DeleteCollectionAsync(DuckDBConnection conn, string collectionName, CancellationToken cancellationToken = default)
    {
        using var cmd = conn.CreateCommand();
        cmd.CommandText = $@"
             DELETE FROM {TableName}
             WHERE collection=?;";
        cmd.Parameters.Add(new DuckDBParameter(collectionName));
        await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }

    public async Task DeleteAsync(DuckDBConnection conn, string collectionName, string key, CancellationToken cancellationToken = default)
    {
        using var cmd = conn.CreateCommand();
        cmd.CommandText = $@"
             DELETE FROM {TableName}
             WHERE collection=?1
                AND key=?2; ";
        cmd.Parameters.Add(new DuckDBParameter(collectionName));
        cmd.Parameters.Add(new DuckDBParameter(key));
        await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }
}
