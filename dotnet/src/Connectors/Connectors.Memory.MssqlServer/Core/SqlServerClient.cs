// Copyright (c) Kevin BEAUGRAND. All rights reserved.

using Microsoft.Data.SqlClient;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Connectors.MssqlServer.Core;

/// <summary>
/// Represents a client for interacting with a SQL Server database for storing semantic memories and embeddings.
/// </summary>
[System.Diagnostics.CodeAnalysis.SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities",
                                                   Justification = "We need to build the full table name using schema and collection, it does not support parameterized passing.")]
internal sealed class SqlServerClient
{
    private readonly string _connectionString;
    private readonly SqlServerConfig _configuration;
    private SqlConnection _connection;

    /// <summary>
    /// Initializes a new instance of the <see cref="SqlServerClient"/> class with the specified connection string and schema.
    /// </summary>
    /// <param name="connectionString">The connection string to use for connecting to the SQL Server database.</param>
    /// <param name="configuration">The configuration to use for the SQL Server database.</param>
    public SqlServerClient(string connectionString, SqlServerConfig configuration)
    {
        this._connectionString = connectionString;
        this._configuration = configuration;

        this._connection = new SqlConnection(this._connectionString);
        this._connection.Open();
    }

    /// <inheritdoc />
    public async Task CreateTablesAsync(CancellationToken cancellationToken)
    {
        var sql = $@"IF NOT EXISTS (SELECT  *
                                    FROM    sys.schemas
                                    WHERE   name = N'{this._configuration.Schema}' )
                    EXEC('CREATE SCHEMA [{this._configuration.Schema}]');
                    IF OBJECT_ID(N'{this.GetFullTableName(this._configuration.MemoryCollectionTableName)}', N'U') IS NULL
                    CREATE TABLE {this.GetFullTableName(this._configuration.MemoryCollectionTableName)}
                    (   [id] NVARCHAR(256) NOT NULL,
                        PRIMARY KEY ([id])
                    );

                    IF OBJECT_ID(N'{this.GetFullTableName(this._configuration.MemoryTableName)}', N'U') IS NULL
                    CREATE TABLE {this.GetFullTableName(this._configuration.MemoryTableName)}
                    (   [id] UNIQUEIDENTIFIER NOT NULL,
                        [key] NVARCHAR(256)  NOT NULL,
                        [collection] NVARCHAR(256) NOT NULL,
                        [metadata] TEXT,
                        [embedding] TEXT,
                        [timestamp] DATETIMEOFFSET,
                        PRIMARY KEY ([id]),
                        FOREIGN KEY ([collection]) REFERENCES {this.GetFullTableName(this._configuration.MemoryCollectionTableName)}([id]) ON DELETE CASCADE,
                        CONSTRAINT UK_{this._configuration.MemoryTableName} UNIQUE([collection], [key])
                    );";

        using (SqlCommand command = this._connection.CreateCommand())
        {
            command.CommandText = sql;
            await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc />
    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        collectionName = NormalizeIndexName(collectionName);

        if (await this.DoesCollectionExistsAsync(collectionName, cancellationToken).ConfigureAwait(false))
        {
            // Collection already exists
            return;
        }

        using (SqlCommand command = this._connection.CreateCommand())
        {
            command.CommandText = $@"
                    INSERT INTO {this.GetFullTableName(this._configuration.MemoryCollectionTableName)}([id])
                    VALUES (@collectionName);

                    IF OBJECT_ID(N'{this.GetFullTableName($"{this._configuration.EmbeddingsTableName}_{collectionName}")}', N'U') IS NULL
                    CREATE TABLE {this.GetFullTableName($"{this._configuration.EmbeddingsTableName}_{collectionName}")}
                    (
                        [memory_id] UNIQUEIDENTIFIER NOT NULL,
                        [vector_value_id] [int] NOT NULL,
                        [vector_value] [float] NOT NULL
                        FOREIGN KEY ([memory_id]) REFERENCES {this.GetFullTableName(this._configuration.MemoryTableName)}([id]) ON DELETE CASCADE
                    );

                    IF OBJECT_ID(N'{this._configuration.Schema}.IXC_{$"{this._configuration.EmbeddingsTableName}_{collectionName}"}', N'U') IS NULL
                    CREATE CLUSTERED COLUMNSTORE INDEX [IXC_{$"{this._configuration.EmbeddingsTableName}_{collectionName}]"}
                    ON {this.GetFullTableName($"{this._configuration.EmbeddingsTableName}_{collectionName}")};";

            command.Parameters.AddWithValue("@collectionName", collectionName);

            await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        };
    }

    /// <inheritdoc />
    public async Task<bool> DoesCollectionExistsAsync(string collectionName,
        CancellationToken cancellationToken = default)
    {
        collectionName = NormalizeIndexName(collectionName);

        var collections = this.GetCollectionsAsync(cancellationToken)
                            .WithCancellation(cancellationToken)
                            .ConfigureAwait(false);

        await foreach (var item in collections)
        {
            if (item.Equals(collectionName, StringComparison.OrdinalIgnoreCase))
            {
                return true;
            }
        }

        return false;
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> GetCollectionsAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using (SqlCommand command = this._connection.CreateCommand())
        {
            command.CommandText = $"SELECT [id] FROM {this.GetFullTableName(this._configuration.MemoryCollectionTableName)}";

            using var dataReader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);

            while (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                yield return dataReader.GetString(dataReader.GetOrdinal("id"));
            }
        };
    }

    /// <inheritdoc />
    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        collectionName = NormalizeIndexName(collectionName);

        if (!await this.DoesCollectionExistsAsync(collectionName, cancellationToken).ConfigureAwait(false))
        {
            // Collection does not exist
            return;
        }

        using (SqlCommand command = this._connection.CreateCommand())
        {
            command.CommandText = $@"DELETE FROM {this.GetFullTableName(this._configuration.MemoryCollectionTableName)}
                                     WHERE [id] = @collectionName;

                                     DROP TABLE {this.GetFullTableName($"{this._configuration.EmbeddingsTableName}_{collectionName}")};";

            command.Parameters.AddWithValue("@collectionName", collectionName);

            await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        };
    }

    /// <inheritdoc />
    public async Task<SqlServerMemoryEntry?> ReadAsync(string collectionName, string key, bool withEmbeddings = false, CancellationToken cancellationToken = default)
    {
        collectionName = NormalizeIndexName(collectionName);

        string queryColumns = "[id], [key], [metadata], [timestamp]";

        if (withEmbeddings)
        {
            queryColumns += ", [embedding]";
        }

        using SqlCommand entryCommand = this._connection.CreateCommand();

        entryCommand.CommandText = $@"
                                    SELECT {queryColumns}
                                    FROM {this.GetFullTableName(this._configuration.MemoryTableName)}
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
        collectionName = NormalizeIndexName(collectionName);

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

        using SqlCommand cmd = this._connection.CreateCommand();

        cmd.CommandText = $@"
            SELECT {queryColumns}
            FROM {this.GetFullTableName(this._configuration.MemoryTableName)}
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
        collectionName = NormalizeIndexName(collectionName);

        using SqlCommand cmd = this._connection.CreateCommand();

        cmd.CommandText = $"DELETE FROM {this.GetFullTableName(this._configuration.MemoryTableName)} WHERE [collection] = @collectionName AND [key]=@key";
        cmd.Parameters.AddWithValue("@collectionName", collectionName);
        cmd.Parameters.AddWithValue("@key", key);

        await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task DeleteBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        collectionName = NormalizeIndexName(collectionName);

        string[] keysArray = keys.ToArray();

        if (keysArray.Length == 0)
        {
            return;
        }

        using SqlCommand cmd = this._connection.CreateCommand();

        cmd.CommandText = $@"
            DELETE
            FROM {this.GetFullTableName(this._configuration.MemoryTableName)}
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
        collectionName = NormalizeIndexName(collectionName);

        string queryColumns = "[id], [key], [metadata], [timestamp]";

        if (withEmbeddings)
        {
            queryColumns += ", [embedding]";
        }

        using SqlCommand cmd = this._connection.CreateCommand();

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
            {this.GetFullTableName($"{this._configuration.EmbeddingsTableName}_{collectionName}")}.[memory_id],
            SUM([embedding].[vector_value] * {this.GetFullTableName($"{this._configuration.EmbeddingsTableName}_{collectionName}")}.[vector_value]) /
            (
                SQRT(SUM([embedding].[vector_value] * [embedding].[vector_value]))
                *
                SQRT(SUM({this.GetFullTableName($"{this._configuration.EmbeddingsTableName}_{collectionName}")}.[vector_value] * {this.GetFullTableName($"{this._configuration.EmbeddingsTableName}_{collectionName}")}.[vector_value]))
            ) AS cosine_similarity
            -- sum([embedding].[vector_value] * {this.GetFullTableName($"{this._configuration.EmbeddingsTableName}_{collectionName}")}.[vector_value]) as cosine_distance -- Optimized as per https://platform.openai.com/docs/guides/embeddings/which-distance-function-should-i-use
        FROM
            [embedding]
        INNER JOIN
            {this.GetFullTableName($"{this._configuration.EmbeddingsTableName}_{collectionName}")} ON [embedding].vector_value_id = {this.GetFullTableName($"{this._configuration.EmbeddingsTableName}_{collectionName}")}.vector_value_id
        GROUP BY
            {this.GetFullTableName($"{this._configuration.EmbeddingsTableName}_{collectionName}")}.[memory_id]
        ORDER BY
            cosine_similarity DESC
        )
        SELECT
            {this.GetFullTableName(this._configuration.MemoryTableName)}.[id],
            {this.GetFullTableName(this._configuration.MemoryTableName)}.[key],
            {this.GetFullTableName(this._configuration.MemoryTableName)}.[metadata],
            {this.GetFullTableName(this._configuration.MemoryTableName)}.[timestamp],
            {this.GetFullTableName(this._configuration.MemoryTableName)}.[embedding],
            (
                SELECT
                    [vector_value]
                FROM {this.GetFullTableName($"{this._configuration.EmbeddingsTableName}_{collectionName}")}
                WHERE {this.GetFullTableName(this._configuration.MemoryTableName)}.[id] = {this.GetFullTableName($"{this._configuration.EmbeddingsTableName}_{collectionName}")}.[memory_id]
                ORDER BY vector_value_id
                FOR JSON AUTO
            ) AS [embeddings],
            [similarity].[cosine_similarity]
        FROM
            [similarity]
        INNER JOIN
            {this.GetFullTableName(this._configuration.MemoryTableName)} ON [similarity].[memory_id] = {this.GetFullTableName(this._configuration.MemoryTableName)}.[id]
        WHERE [cosine_similarity] >= @min_relevance_score
        ORDER BY [cosine_similarity] desc";

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

    /// <inheritdoc />
    public async Task UpsertAsync(string collectionName,
        string key,
        string? metadata,
        string embedding,
        DateTimeOffset? timestamp,
        CancellationToken cancellationToken = default)
    {
        collectionName = NormalizeIndexName(collectionName);

        using SqlCommand cmd = this._connection.CreateCommand();

        cmd.CommandText = $@"
                MERGE INTO {this.GetFullTableName(this._configuration.MemoryTableName)}
                USING (SELECT @key) as [src]([key])
                ON {this.GetFullTableName(this._configuration.MemoryTableName)}.[key] = [src].[key]
                WHEN MATCHED THEN
                    UPDATE SET metadata=@metadata, embedding=@embedding, timestamp=@timestamp
                WHEN NOT MATCHED THEN
                    INSERT ([id], [collection], [key], [metadata], [timestamp], [embedding])
                    VALUES (NEWID(), @collection, @key, @metadata, @timestamp, @embedding);


                MERGE {this.GetFullTableName($"{this._configuration.EmbeddingsTableName}_{collectionName}")} AS [tgt]
                USING (
                    SELECT
                        {this.GetFullTableName(this._configuration.MemoryTableName)}.[id],
                        cast([vector].[key] AS INT) AS [vector_value_id],
                        cast([vector].[value] AS FLOAT) AS [vector_value]
                    FROM {this.GetFullTableName(this._configuration.MemoryTableName)}
                    CROSS APPLY
                        openjson(@embedding) [vector]
                    WHERE {this.GetFullTableName(this._configuration.MemoryTableName)}.[key] = @key
                        AND {this.GetFullTableName(this._configuration.MemoryTableName)}.[collection] = @collection
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
        return $"[{this._configuration.Schema}].[{tableName}]";
    }

    /// <inheritdoc />
    private async Task<SqlServerMemoryEntry> ReadEntryAsync(SqlDataReader dataReader, bool withEmbedding, CancellationToken cancellationToken = default)
    {
        var entry = new SqlServerMemoryEntry();

        entry.Id = dataReader.GetGuid(dataReader.GetOrdinal("id"));
        entry.Key = dataReader.GetString(dataReader.GetOrdinal("key"));

        if (!await dataReader.IsDBNullAsync(dataReader.GetOrdinal("metadata"), cancellationToken).ConfigureAwait(false))
        {
            entry.MetadataString = dataReader.GetString(dataReader.GetOrdinal("metadata"));
        }

        if (!await dataReader.IsDBNullAsync(dataReader.GetOrdinal("timestamp"), cancellationToken).ConfigureAwait(false))
        {
            entry.Timestamp = await dataReader.GetFieldValueAsync<DateTimeOffset?>(dataReader.GetOrdinal("timestamp"), cancellationToken).ConfigureAwait(false);
        }

        if (withEmbedding)
        {
            entry.Embedding = new ReadOnlyMemory<float>(JsonSerializer.Deserialize<IEnumerable<float>>(dataReader.GetString(dataReader.GetOrdinal("embedding")))!.ToArray());
        }

        return entry;
    }

    // Note: "_" is allowed in Postgres, but we normalize it to "-" for consistency with other DBs
    private static readonly Regex s_replaceIndexNameCharsRegex = new(@"[\s|\\|/|.|_|:]");
    private const string ValidSeparator = "-";

    private static string NormalizeIndexName(string index)
    {
        index = s_replaceIndexNameCharsRegex.Replace(index.Trim().ToLowerInvariant(), ValidSeparator);

        return index;
    }

    public void Dispose()
    {
        if (this._connection != null)
        {
            this._connection.Dispose();
            this._connection = null!;
        }
    }
}
