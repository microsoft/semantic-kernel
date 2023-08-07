// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Data.SqlClient;
using Microsoft.SemanticKernel.AI.Embeddings;

namespace Microsoft.SemanticKernel.Connectors.Memory.SqlServer;

[System.Diagnostics.CodeAnalysis.SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities",
                                                   Justification = "We need to build the full table name using schema and collection, it does not support parameterized passing.")]
public sealed class SqlServerClient : ISqlServerClient
{
    internal const string MemoryCollectionTableName = "SKMemoryCollections";
    internal const string MemoryTableName = "SKMemories";
    internal const string EmbeddingsTableName = "SKEmbeddings";

    private readonly string _connectionString;
    private readonly string _schema;

    public SqlServerClient(string connectionString, string schema)
    {
        this._connectionString = connectionString;
        this._schema = schema;
    }

    public async Task CreateTables(CancellationToken cancellationToken)
    {
        var sql = $@"IF OBJECT_ID(N'{this.GetFullTableName(MemoryCollectionTableName)}', N'U') IS NULL
                    CREATE TABLE {this.GetFullTableName(MemoryCollectionTableName)}
                    (   [id] NVARCHAR(256) NOT NULL,
                        PRIMARY KEY ([id])
                    );

                    IF OBJECT_ID(N'{this.GetFullTableName(MemoryTableName)}', N'U') IS NULL
                    CREATE TABLE {this.GetFullTableName(MemoryTableName)}
                    (   [id] UNIQUEIDENTIFIER NOT NULL,
                        [key] NVARCHAR(256)  NOT NULL,
                        [collection] NVARCHAR(256) NOT NULL,
                        [metadata] TEXT,
                        [embedding] TEXT,
                        [timestamp] DATETIMEOFFSET,
                        PRIMARY KEY ([id]),
                        FOREIGN KEY ([collection]) REFERENCES {this.GetFullTableName(MemoryCollectionTableName)}([id]) ON DELETE CASCADE,
                        CONSTRAINT UK_{MemoryTableName} UNIQUE([collection], [key])
                    );";

        using var connection = new SqlConnection(this._connectionString);

        await connection.OpenAsync(cancellationToken)
                .ConfigureAwait(false);

        using (SqlCommand command = connection.CreateCommand())
        {
            command.CommandText = sql;
            await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        if (await this.DoesCollectionExistsAsync(collectionName, cancellationToken).ConfigureAwait(false))
        {
            // Collection already exists
            return;
        }

        using var connection = new SqlConnection(this._connectionString);

        await connection.OpenAsync(cancellationToken)
                .ConfigureAwait(false);

        using (SqlCommand command = connection.CreateCommand())
        {
            command.CommandText = $@"
                    INSERT INTO {this.GetFullTableName(MemoryCollectionTableName)}([id])
                    VALUES (@collectionName);
                    
                    IF OBJECT_ID(N'{this.GetFullTableName($"{EmbeddingsTableName}_{collectionName}")}', N'U') IS NULL
                    CREATE TABLE {this.GetFullTableName($"{EmbeddingsTableName}_{collectionName}")}
                    (   
                        [memory_id] UNIQUEIDENTIFIER NOT NULL,
                        [vector_value_id] [int] NOT NULL,
                        [vector_value] [float] NOT NULL
                        FOREIGN KEY ([memory_id]) REFERENCES {this.GetFullTableName(MemoryTableName)}([id]) ON DELETE CASCADE
                    );
                    
                    IF OBJECT_ID(N'{this._schema}.IXC_{$"{EmbeddingsTableName}_{collectionName}"}', N'U') IS NULL
                    CREATE CLUSTERED COLUMNSTORE INDEX IXC_{$"{EmbeddingsTableName}_{collectionName}"}
                    ON {this.GetFullTableName($"{EmbeddingsTableName}_{collectionName}")}
                    ORDER ([memory_id]);";

            command.Parameters.AddWithValue("@collectionName", collectionName);

            await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        };
    }

    public async Task<bool> DoesCollectionExistsAsync(string collectionName,
        CancellationToken cancellationToken = default)
    {
        var collections = await this.GetCollectionsAsync(cancellationToken).ToListAsync(cancellationToken).ConfigureAwait(false);
        return collections.Contains(collectionName);
    }

    public async IAsyncEnumerable<string> GetCollectionsAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using var connection = new SqlConnection(this._connectionString);

        await connection.OpenAsync(cancellationToken)
                .ConfigureAwait(false);

        using (SqlCommand command = connection.CreateCommand())
        {
            command.CommandText = $"SELECT [id] FROM {this.GetFullTableName(MemoryCollectionTableName)}";

            using var dataReader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);

            while (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                yield return dataReader.GetString(dataReader.GetOrdinal("id"));
            }
        };
    }

    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        if (!(await this.DoesCollectionExistsAsync(collectionName, cancellationToken).ConfigureAwait(false)))
        {
            // Collection does not exist
            return;
        }

        using var connection = new SqlConnection(this._connectionString);

        await connection.OpenAsync(cancellationToken)
                .ConfigureAwait(false);

        using (SqlCommand command = connection.CreateCommand())
        {
            command.CommandText = $@"DELETE FROM {this.GetFullTableName(MemoryCollectionTableName)}
                                     WHERE [id] = @collectionName;

                                     DROP TABLE {this.GetFullTableName($"{EmbeddingsTableName}_{collectionName}")};";

            command.Parameters.AddWithValue("@collectionName", collectionName);

            await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        };
    }

    /// <inheritdoc />
    public async Task<SqlServerMemoryEntry?> ReadAsync(string collectionName, string key, bool withEmbeddings = false, CancellationToken cancellationToken = default)
    {
        string queryColumns = "[id], [key], [metadata], [timestamp]";

        if (withEmbeddings)
        {
            queryColumns += ", [embedding]";
        }

        using var connection = new SqlConnection(this._connectionString);

        await connection.OpenAsync(cancellationToken)
                .ConfigureAwait(false);

        using SqlCommand entryCommand = connection.CreateCommand();

        entryCommand.CommandText = $@"
                                    SELECT {queryColumns}
                                    FROM {this.GetFullTableName(MemoryTableName)}
                                    WHERE [collection] = @collection
                                    AND [key]=@key";

        entryCommand.Parameters.AddWithValue("@key", key);
        entryCommand.Parameters.AddWithValue("@collection", collectionName);

        using var dataReader = await entryCommand.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);

        if (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            return await this.ReadEntryAsync(dataReader, withEmbeddings, cancellationToken).ConfigureAwait(false);
        }

        return null;
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<SqlServerMemoryEntry> ReadBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        string[] keysArray = keys.ToArray();

        if (keysArray.Length == 0)
        {
            yield break;
        }

        string queryColumns = "[id], [key], [metadata], [timestamp]";

        if (withEmbeddings)
        {
            queryColumns += ", [embedding]";
        }

        using var connection = new SqlConnection(this._connectionString);

        await connection.OpenAsync(cancellationToken)
                .ConfigureAwait(false);

        using SqlCommand cmd = connection.CreateCommand();

        cmd.CommandText = $@"
            SELECT {queryColumns}
            FROM {this.GetFullTableName(MemoryTableName)}
            WHERE [key] IN ({string.Join(",", Enumerable.Range(0, keysArray.Length).Select(c => $"@key{c}"))})";

        cmd.Parameters.AddWithValue("@collectionName", collectionName);

        for (int i = 0; i < keysArray.Length; i++)
        {
            cmd.Parameters.AddWithValue($"@key{i}", keysArray[i]);
        }

        using var dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);

        while (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            yield return await this.ReadEntryAsync(dataReader, withEmbeddings, cancellationToken).ConfigureAwait(false);
        }
    }


    /// <inheritdoc />
    public async Task DeleteAsync(string collectionName, string key, CancellationToken cancellationToken = default)
    {
        using var connection = new SqlConnection(this._connectionString);

        using SqlCommand cmd = connection.CreateCommand();

        await connection.OpenAsync(cancellationToken)
                .ConfigureAwait(false);

        cmd.CommandText = $"DELETE FROM {this.GetFullTableName(MemoryTableName)} WHERE [collection] = @collectionName AND [key]=@key";
        cmd.Parameters.AddWithValue("@collectionName", collectionName);
        cmd.Parameters.AddWithValue("@key", key);

        await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task DeleteBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        string[] keysArray = keys.ToArray();

        if (keysArray.Length == 0)
        {
            return;
        }

        using var connection = new SqlConnection(this._connectionString);

        await connection.OpenAsync(cancellationToken)
                .ConfigureAwait(false);

        using SqlCommand cmd = connection.CreateCommand();

        cmd.CommandText = $@"
            DELETE
            FROM {this.GetFullTableName(MemoryTableName)}
            WHERE [collection] = @collectionName
                AND [key] IN ({string.Join(",", Enumerable.Range(0, keysArray.Length).Select(c => $"@key{c}"))})";


        cmd.Parameters.AddWithValue("@collectionName", collectionName);

        for (int i = 0; i < keysArray.Length; i++)
        {
            cmd.Parameters.AddWithValue($"@key{i}", keysArray[i]);
        }

        await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);

    }

    /// <inheritdoc />
    public async IAsyncEnumerable<(SqlServerMemoryEntry, double)> GetNearestMatchesAsync(
        string collectionName, string embedding, int limit, double minRelevanceScore = 0, bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        string queryColumns = "[id], [key], [metadata], [timestamp]";

        if (withEmbeddings)
        {
            queryColumns += ", [embedding]";
        }

        using var connection = new SqlConnection(this._connectionString);

        await connection.OpenAsync(cancellationToken)
                .ConfigureAwait(false);

        using SqlCommand cmd = connection.CreateCommand();

        cmd.CommandText = $@"WITH [embedding] as
        (
            SELECT 
                cast([key] AS INT) AS [vector_value_id],
                cast([value] AS FLOAT) AS [vector_value]
            FROM 
                openjson(@vector)
        ),
        [similarity] AS
        (
            SELECT TOP (@limit)
            {this.GetFullTableName($"{EmbeddingsTableName}_{collectionName}")}.[memory_id], 
            SUM([embedding].[vector_value] * {this.GetFullTableName($"{EmbeddingsTableName}_{collectionName}")}.[vector_value]) / 
            (
                SQRT(SUM([embedding].[vector_value] * [embedding].[vector_value])) 
                * 
                SQRT(SUM({this.GetFullTableName($"{EmbeddingsTableName}_{collectionName}")}.[vector_value] * {this.GetFullTableName($"{EmbeddingsTableName}_{collectionName}")}.[vector_value]))
            ) AS cosine_similarity
            -- sum([embedding].[vector_value] * {this.GetFullTableName($"{EmbeddingsTableName}_{collectionName}")}.[vector_value]) as cosine_distance -- Optimized as per https://platform.openai.com/docs/guides/embeddings/which-distance-function-should-i-use
        FROM 
            [embedding]
        INNER JOIN 
            {this.GetFullTableName($"{EmbeddingsTableName}_{collectionName}")} ON [embedding].vector_value_id = {this.GetFullTableName($"{EmbeddingsTableName}_{collectionName}")}.vector_value_id
        GROUP BY
            {this.GetFullTableName($"{EmbeddingsTableName}_{collectionName}")}.[memory_id]
        ORDER BY
            cosine_similarity DESC
        )
        SELECT 
            {this.GetFullTableName(MemoryTableName)}.[id],
            {this.GetFullTableName(MemoryTableName)}.[key],    
            {this.GetFullTableName(MemoryTableName)}.[metadata],
            {this.GetFullTableName(MemoryTableName)}.[timestamp],
            {this.GetFullTableName(MemoryTableName)}.[embedding],
            (
                SELECT 
                    [vector_value]
                FROM {this.GetFullTableName($"{EmbeddingsTableName}_{collectionName}")}
                WHERE {this.GetFullTableName(MemoryTableName)}.[id] = {this.GetFullTableName($"{EmbeddingsTableName}_{collectionName}")}.[memory_id]
                ORDER BY vector_value_id
                FOR JSON AUTO
            ) AS [embeddings],
            [similarity].[cosine_similarity]
        FROM 
            [similarity] 
        INNER JOIN 
            {this.GetFullTableName(MemoryTableName)} ON [similarity].[memory_id] = {this.GetFullTableName(MemoryTableName)}.[id]
        WHERE cosine_similarity >= @min_relevance_score";

        cmd.Parameters.AddWithValue("@vector", embedding);
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

    public async Task UpsertAsync(string collectionName,
        string key,
        string? metadata,
        string embedding,
        DateTimeOffset? timestamp,
        CancellationToken cancellationToken = default)
    {
        using var connection = new SqlConnection(this._connectionString);

        await connection.OpenAsync(cancellationToken)
                .ConfigureAwait(false);

        using SqlCommand cmd = connection.CreateCommand();

        cmd.CommandText = $@"
                MERGE INTO {this.GetFullTableName(MemoryTableName)}
                USING (SELECT @key) as [src]([key])
                ON {this.GetFullTableName(MemoryTableName)}.[key] = [src].[key]
                WHEN MATCHED THEN
                    UPDATE SET metadata=@metadata, embedding=@embedding, timestamp=@timestamp
                WHEN NOT MATCHED THEN
                    INSERT ([id], [collection], [key], [metadata], [timestamp], [embedding])
                    VALUES (NEWID(), @collection, @key, @metadata, @timestamp, @embedding);


                MERGE {this.GetFullTableName($"{EmbeddingsTableName}_{collectionName}")} AS [tgt]  
                USING (
                    SELECT 
                        {this.GetFullTableName(MemoryTableName)}.[id],
                        cast([vector].[key] AS INT) AS [vector_value_id],
                        cast([vector].[value] AS FLOAT) AS [vector_value] 
                    FROM {this.GetFullTableName(MemoryTableName)}
                    CROSS APPLY
                        openjson(@embedding) [vector]
                    WHERE {this.GetFullTableName(MemoryTableName)}.[key] = @key
                        AND {this.GetFullTableName(MemoryTableName)}.[collection] = @collection
                ) AS [src]
                ON [tgt].[memory_id] = [src].[id] AND [tgt].[vector_value_id] = [src].[vector_value_id]
                WHEN MATCHED THEN
                    UPDATE SET [tgt].[vector_value] = [src].[vector_value]
                WHEN NOT MATCHED THEN
                    INSERT ([memory_id], [vector_value_id], [vector_value])
                    VALUES ([src].[id], 
                            [src].[vector_value_id], 
                            [src].[vector_value] )
                ;";

        cmd.Parameters.AddWithValue("@collection", collectionName);
        cmd.Parameters.AddWithValue("@key", key);
        cmd.Parameters.AddWithValue("@metadata", metadata ?? (object)DBNull.Value);
        cmd.Parameters.AddWithValue("@embedding", embedding);
        cmd.Parameters.AddWithValue("@timestamp", timestamp ?? (object)DBNull.Value);

        await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }

    private string GetFullTableName(string tableName)
    {
        return $"[{this._schema}].[{tableName}]";
    }

    private async Task<SqlServerMemoryEntry> ReadEntryAsync(SqlDataReader dataReader, bool withEmbedding, CancellationToken cancellationToken = default)
    {
        var entry = new SqlServerMemoryEntry();

        entry.Id = dataReader.GetGuid(dataReader.GetOrdinal("id"));
        entry.Key = dataReader.GetString(dataReader.GetOrdinal("key"));

        if (!(await dataReader.IsDBNullAsync(dataReader.GetOrdinal("metadata"), cancellationToken).ConfigureAwait(false)))
        {
            entry.MetadataString = dataReader.GetString(dataReader.GetOrdinal("metadata"));
        }

        if (!(await dataReader.IsDBNullAsync(dataReader.GetOrdinal("timestamp"), cancellationToken).ConfigureAwait(false)))
        {
            entry.Timestamp = await dataReader.GetFieldValueAsync<DateTimeOffset?>(dataReader.GetOrdinal("timestamp"), cancellationToken).ConfigureAwait(false);
        }

        if (withEmbedding)
        {
            entry.Embedding = new Embedding<float>(JsonSerializer.Deserialize<IEnumerable<float>>(dataReader.GetString(dataReader.GetOrdinal("embedding")))!);
        }

        return entry;
    }
}
