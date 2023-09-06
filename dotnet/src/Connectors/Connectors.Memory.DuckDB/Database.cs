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

    public string EmbeddingString { get; set; }

    public string? Timestamp { get; set; }

    public float Score { get; set; }
}

internal sealed class Database
{
    private const string TableName = "SKMemoryTable";

    public Task CreateFunctionsAsync(DuckDBConnection conn, CancellationToken cancellationToken)
    {
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"
                          CREATE OR REPLACE MACRO cosine_similarity(a,b) AS (select sum (xy) from (select x * y  as xy from (select  UNNEST(a) as x,  UNNEST(b) as y))) / sqrt(list_aggregate(list_transform(a, x -> x * x), 'sum') * list_aggregate(list_transform(b,  x -> x * x), 'sum'));
                          CREATE OR REPLACE MACRO split_string_of_numbers(t) AS regexp_extract_all(regexp_replace(t,'(\[|\])', '', 'g'), '([+-]?([0-9]*[.])?[0-9]+)(\s*;\s*)?',1);
                          CREATE OR REPLACE MACRO number_vector_decoder(t) AS list_transform(split_string_of_numbers(t), x -> cast(x AS double));
                          CREATE OR REPLACE MACRO encode_number_vector(t) AS concat('[',list_aggregate(list_transform(t, x -> cast(x AS string)), 'string_agg', '; '),']');
                          ";
        return cmd.ExecuteNonQueryAsync(cancellationToken);
    }

    public Task CreateTableAsync(DuckDBConnection conn, CancellationToken cancellationToken = default)
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
        float[]? embedding,
        int limit,
        double minRelevanceScore = 0,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var embeddingArrayString = EncodeFloatArrayToString(embedding ?? Array.Empty<float>());

        using var cmd = conn.CreateCommand();
        cmd.CommandText = $@"
            SELECT key, metadata, timestamp, cast(embedding as string) as embeddingAsString, cast(cosine_similarity(embedding,{embeddingArrayString}) as FLOAT) as score FROM {TableName}
            WHERE collection=?1 AND score >= {minRelevanceScore.ToString("F12", CultureInfo.InvariantCulture)}
            ORDER BY score DESC
            LIMIT {limit};";
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
            string embeddingAsString = dataReader.GetString("embeddingAsString");
            string timestamp = dataReader.GetString("timestamp");
            float score = dataReader.GetFloat("score");
            yield return new DatabaseEntry
            {
                Key = key,
                MetadataString = metadata,
                EmbeddingString = embeddingAsString,
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
             SELECT metadata, timestamp, cast(embedding as string) as embeddingAsString FROM {TableName}
             WHERE collection=?1
                AND key=?2; ";
        cmd.Parameters.Add(new DuckDBParameter(collectionName));
        cmd.Parameters.Add(new DuckDBParameter(key));

        using var dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
        if (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            string metadata = dataReader.GetString(dataReader.GetOrdinal("metadata"));
            string embeddingAsString = dataReader.GetString(dataReader.GetOrdinal("embeddingAsString"));
            string timestamp = dataReader.GetString(dataReader.GetOrdinal("timestamp"));
            return new DatabaseEntry
            {
                Key = key,
                MetadataString = metadata,
                EmbeddingString = embeddingAsString,
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
}
