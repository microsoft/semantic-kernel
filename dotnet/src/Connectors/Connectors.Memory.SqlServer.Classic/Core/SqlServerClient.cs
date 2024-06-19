// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Data;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Data.SqlClient;

namespace Microsoft.SemanticKernel.Connectors.SqlServer.Classic.Core;

/// <summary>
/// Represents a client for interacting with a SQL Server database for storing semantic memories and embeddings.
/// </summary>
[System.Diagnostics.CodeAnalysis.SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities",
                                                   Justification = "We need to build the full table name using schema and collection, it does not support parameterized passing.")]
internal sealed class SqlServerClient
{
    private readonly SqlServerClassicConfig _configuration;
    private readonly SqlConnection _connection;

    /// <summary>
    /// Initializes a new instance of the <see cref="SqlServerClient"/> class with the specified connection string and schema.
    /// </summary>
    /// <param name="connection">The connection to the SQL Server database.</param>
    /// <param name="configuration">The configuration to use for the SQL Server database.</param>
    public SqlServerClient(SqlConnection connection, SqlServerClassicConfig configuration)
    {
        this._configuration = configuration;

        this._connection = connection;
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

        using (await this.OpenConnectionAsync(cancellationToken).ConfigureAwait(false))
        {
            using var command = this._connection.CreateCommand();

            command.CommandText = $@"
                    IF OBJECT_ID(N'{this.GetFullTableName($"{this._configuration.CollectionTableNamePrefix}_{collectionName}")}', N'U') IS NULL
                    CREATE TABLE {this.GetFullTableName($"{this._configuration.CollectionTableNamePrefix}_{collectionName}")}
                    (   [id] UNIQUEIDENTIFIER NOT NULL,
                        [key] NVARCHAR(256)  NOT NULL,
                        [metadata] TEXT,
                        [embedding] TEXT,
                        [timestamp] DATETIMEOFFSET,
                        PRIMARY KEY ([id])
                    );

                    IF OBJECT_ID(N'{this.GetFullTableName($"{this._configuration.EmbeddingsTableNamePrefix}_{collectionName}")}', N'U') IS NULL
                    CREATE TABLE {this.GetFullTableName($"{this._configuration.EmbeddingsTableNamePrefix}_{collectionName}")}
                    (
                        [memory_id] UNIQUEIDENTIFIER NOT NULL,
                        [vector_value_id] [int] NOT NULL,
                        [vector_value] [float] NOT NULL
                    );

                    IF OBJECT_ID(N'{NormalizeSQLObjectName(this._configuration.Schema)}.IXC_{$"{NormalizeSQLObjectName(this._configuration.EmbeddingsTableNamePrefix)}_{collectionName}"}', N'U') IS NULL
                    CREATE CLUSTERED COLUMNSTORE INDEX [IXC_{$"{NormalizeSQLObjectName(this._configuration.EmbeddingsTableNamePrefix)}_{collectionName}]"}
                    ON {this.GetFullTableName($"{this._configuration.EmbeddingsTableNamePrefix}_{collectionName}")};";

            command.Parameters.AddWithValue("@collectionName", collectionName);

            await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc />
    public async Task<bool> DoesCollectionExistsAsync(string collectionName,
        CancellationToken cancellationToken = default)
    {
        collectionName = NormalizeIndexName(collectionName);

        using (await this.OpenConnectionAsync(cancellationToken).ConfigureAwait(false))
        {
            using var command = this._connection.CreateCommand();

            command.CommandText = """
                SELECT 1
                FROM information_schema.tables
                WHERE table_type = 'BASE TABLE'
                    AND table_schema = @schema
                    AND table_name = @tableName
                """;

            command.Parameters.AddWithValue("@schema", this._configuration.Schema);
            command.Parameters.AddWithValue("@tableName", $"{this._configuration.CollectionTableNamePrefix}_{collectionName}");

            using var dataReader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);

            while (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                return Convert.ToBoolean(dataReader.GetInt32(0));
            }
        }

        return false;
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> GetCollectionsAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using (await this.OpenConnectionAsync(cancellationToken).ConfigureAwait(false))
        {
            using var command = this._connection.CreateCommand();

            command.CommandText = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_type = 'BASE TABLE'
                    AND table_schema = @schema
                AND table_name LIKE @tableName
                """;

            command.Parameters.AddWithValue("@schema", this._configuration.Schema);
            command.Parameters.AddWithValue("@tableName", $"{this._configuration.CollectionTableNamePrefix}_%");

            using var dataReader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);

            while (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                yield return dataReader.GetString(dataReader.GetOrdinal("table_name"))
                                .Replace($"{this._configuration.CollectionTableNamePrefix}_", string.Empty);
            }
        }
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

        using (await this.OpenConnectionAsync(cancellationToken).ConfigureAwait(false))
        {
            using var command = this._connection.CreateCommand();

            command.CommandText = $@"DROP TABLE {this.GetFullTableName($"{this._configuration.CollectionTableNamePrefix}_{collectionName}")};
                                     DROP TABLE {this.GetFullTableName($"{this._configuration.EmbeddingsTableNamePrefix}_{collectionName}")};";

            await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        }
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

        using (await this.OpenConnectionAsync(cancellationToken).ConfigureAwait(false))
        {
            using var command = this._connection.CreateCommand();

            command.CommandText = $@"
                                    SELECT {queryColumns}
                                    FROM {this.GetFullTableName($"{this._configuration.CollectionTableNamePrefix}_{collectionName}")}
                                    WHERE [key] = @key";

            command.Parameters.AddWithValue("@key", key);

            using var dataReader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);

            if (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                return await this.ReadEntryAsync(dataReader, withEmbeddings, cancellationToken).ConfigureAwait(false);
            }

            return null;
        }
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

        using (await this.OpenConnectionAsync(cancellationToken).ConfigureAwait(false))
        {
            using var command = this._connection.CreateCommand();

            command.CommandText = $@"
                SELECT {queryColumns}
                FROM {this.GetFullTableName($"{this._configuration.CollectionTableNamePrefix}_{collectionName}")}
                WHERE [key] IN ({string.Join(",", Enumerable.Range(0, keysArray.Length).Select(c => $"@key{c}"))})";

            for (int i = 0; i < keysArray.Length; i++)
            {
                command.Parameters.AddWithValue($"@key{i}", keysArray[i]);
            }

            using var dataReader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);

            while (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                yield return await this.ReadEntryAsync(dataReader, withEmbeddings, cancellationToken).ConfigureAwait(false);
            }
        }
    }

    /// <inheritdoc />
    public async Task DeleteAsync(string collectionName, string key, CancellationToken cancellationToken = default)
    {
        collectionName = NormalizeIndexName(collectionName);

        using (await this.OpenConnectionAsync(cancellationToken).ConfigureAwait(false))
        {
            using var command = this._connection.CreateCommand();

            command.CommandText = $"DELETE FROM {this.GetFullTableName($"{this._configuration.CollectionTableNamePrefix}_{collectionName}")} WHERE [key] = @key";
            command.Parameters.AddWithValue("@key", key);

            await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        }
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

        using (await this.OpenConnectionAsync(cancellationToken).ConfigureAwait(false))
        {
            using var command = this._connection.CreateCommand();

            command.CommandText = $@"
                    DELETE
                    FROM {this.GetFullTableName($"{this._configuration.CollectionTableNamePrefix}_{collectionName}")}
                    WHERE [key] IN ({string.Join(",", Enumerable.Range(0, keysArray.Length).Select(c => $"@key{c}"))})";

            for (int i = 0; i < keysArray.Length; i++)
            {
                command.Parameters.AddWithValue($"@key{i}", keysArray[i]);
            }

            await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        }
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

        using (await this.OpenConnectionAsync(cancellationToken).ConfigureAwait(false))
        {
            using var command = this._connection.CreateCommand();

            command.CommandText = $@"WITH [embedding] as
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
                {this.GetFullTableName($"{this._configuration.EmbeddingsTableNamePrefix}_{collectionName}")}.[memory_id],
                SUM([embedding].[vector_value] * {this.GetFullTableName($"{this._configuration.EmbeddingsTableNamePrefix}_{collectionName}")}.[vector_value]) /
                (
                    SQRT(SUM([embedding].[vector_value] * [embedding].[vector_value]))
                    *
                    SQRT(SUM({this.GetFullTableName($"{this._configuration.EmbeddingsTableNamePrefix}_{collectionName}")}.[vector_value] * {this.GetFullTableName($"{this._configuration.EmbeddingsTableNamePrefix}_{collectionName}")}.[vector_value]))
                ) AS cosine_similarity
                -- sum([embedding].[vector_value] * {this.GetFullTableName($"{this._configuration.EmbeddingsTableNamePrefix}_{collectionName}")}.[vector_value]) as cosine_distance -- Optimized as per https://platform.openai.com/docs/guides/embeddings/which-distance-function-should-i-use
            FROM
                [embedding]
            INNER JOIN
                {this.GetFullTableName($"{this._configuration.EmbeddingsTableNamePrefix}_{collectionName}")} ON [embedding].vector_value_id = {this.GetFullTableName($"{this._configuration.EmbeddingsTableNamePrefix}_{collectionName}")}.vector_value_id
            GROUP BY
                {this.GetFullTableName($"{this._configuration.EmbeddingsTableNamePrefix}_{collectionName}")}.[memory_id]
            ORDER BY
                cosine_similarity DESC
            )
            SELECT
                {this.GetFullTableName($"{this._configuration.CollectionTableNamePrefix}_{collectionName}")}.[id],
                {this.GetFullTableName($"{this._configuration.CollectionTableNamePrefix}_{collectionName}")}.[key],
                {this.GetFullTableName($"{this._configuration.CollectionTableNamePrefix}_{collectionName}")}.[metadata],
                {this.GetFullTableName($"{this._configuration.CollectionTableNamePrefix}_{collectionName}")}.[timestamp],
                {this.GetFullTableName($"{this._configuration.CollectionTableNamePrefix}_{collectionName}")}.[embedding],
                (
                    SELECT
                        [vector_value]
                    FROM {this.GetFullTableName($"{this._configuration.EmbeddingsTableNamePrefix}_{collectionName}")}
                    WHERE {this.GetFullTableName($"{this._configuration.CollectionTableNamePrefix}_{collectionName}")}.[id] = {this.GetFullTableName($"{this._configuration.EmbeddingsTableNamePrefix}_{collectionName}")}.[memory_id]
                    ORDER BY vector_value_id
                    FOR JSON AUTO
                ) AS [embeddings],
                [similarity].[cosine_similarity]
            FROM
                [similarity]
            INNER JOIN
                {this.GetFullTableName($"{this._configuration.CollectionTableNamePrefix}_{collectionName}")} ON [similarity].[memory_id] = {this.GetFullTableName($"{this._configuration.CollectionTableNamePrefix}_{collectionName}")}.[id]
            WHERE [cosine_similarity] >= @min_relevance_score
            ORDER BY [cosine_similarity] desc";

            command.Parameters.AddWithValue("@vector", embedding);
            command.Parameters.AddWithValue("@min_relevance_score", minRelevanceScore);
            command.Parameters.AddWithValue("@limit", limit);

            using var dataReader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);

            while (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                double cosineSimilarity = dataReader.GetDouble(dataReader.GetOrdinal("cosine_similarity"));
                yield return (await this.ReadEntryAsync(dataReader, withEmbeddings, cancellationToken).ConfigureAwait(false), cosineSimilarity);
            }
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

        using (await this.OpenConnectionAsync(cancellationToken).ConfigureAwait(false))
        {
            using var command = this._connection.CreateCommand();

            command.CommandText = $@"
                MERGE INTO {this.GetFullTableName($"{this._configuration.CollectionTableNamePrefix}_{collectionName}")}
                USING (SELECT @key) as [src]([key])
                ON {this.GetFullTableName($"{this._configuration.CollectionTableNamePrefix}_{collectionName}")}.[key] = [src].[key]
                WHEN MATCHED THEN
                    UPDATE SET metadata = @metadata, embedding = @embedding, timestamp = @timestamp
                WHEN NOT MATCHED THEN
                    INSERT ([id], [key], [metadata], [timestamp], [embedding])
                    VALUES (NEWID(), @key, @metadata, @timestamp, @embedding);

                MERGE {this.GetFullTableName($"{this._configuration.EmbeddingsTableNamePrefix}_{collectionName}")} AS [tgt]
                USING (
                    SELECT
                        {this.GetFullTableName($"{this._configuration.CollectionTableNamePrefix}_{collectionName}")}.[id],
                        cast([vector].[key] AS INT) AS [vector_value_id],
                        cast([vector].[value] AS FLOAT) AS [vector_value]
                    FROM {this.GetFullTableName($"{this._configuration.CollectionTableNamePrefix}_{collectionName}")}
                    CROSS APPLY
                        openjson(@embedding) [vector]
                    WHERE {this.GetFullTableName($"{this._configuration.CollectionTableNamePrefix}_{collectionName}")}.[key] = @key
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

            command.Parameters.AddWithValue("@collection", collectionName);
            command.Parameters.AddWithValue("@key", key);
            command.Parameters.AddWithValue("@metadata", metadata ?? (object)DBNull.Value);
            command.Parameters.AddWithValue("@embedding", embedding);
            command.Parameters.AddWithValue("@timestamp", timestamp ?? (object)DBNull.Value);

            await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    private string GetFullTableName(string tableName)
    {
        return $"[{NormalizeSQLObjectName(this._configuration.Schema)}].[{NormalizeSQLObjectName(tableName)}]";
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

    private static readonly Regex s_replaceIndexNameCharsRegex = new(@"[\s|\\|/|.|:]");
    private static readonly Regex s_replaceSQLObjectNameCharsRegex = new(@"[\s|\\|/|.|:\[|\]|\`|\'|\""]");
    private const string ValidSeparator = "-";

    private static string NormalizeIndexName(string index)
    {
        index = s_replaceIndexNameCharsRegex.Replace(index.Trim().ToLowerInvariant(), ValidSeparator);

        return index;
    }
    private static string NormalizeSQLObjectName(string objectName)
    {
        objectName = s_replaceSQLObjectNameCharsRegex.Replace(objectName.Trim(), ValidSeparator);

        return objectName;
    }

    private async Task<IDisposable> OpenConnectionAsync(CancellationToken cancellationToken = default)
    {
        if (this._connection.State == ConnectionState.Open)
        {
            return new Closer(this, false);
        }
        await this._connection.OpenAsync(cancellationToken).ConfigureAwait(false);
        return new Closer(this, true);
    }

    private readonly struct Closer(SqlServerClient client, bool shouldClose) : IDisposable
    {
        public void Dispose()
        {
            if (shouldClose)
            {
                client._connection.Close();
            }
        }
    }

    public void Dispose()
    {
        this._connection?.Dispose();
    }
}
