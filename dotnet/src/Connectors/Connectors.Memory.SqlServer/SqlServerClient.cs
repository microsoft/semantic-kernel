// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Data;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Data.SqlClient;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

/// <summary>
/// Implementation of database client managing SQL Server or Azure SQL database operations.
/// </summary>
[SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities", Justification = "We need to build the full table name using schema and collection, it does not support parameterized passing.")]
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and SqlServerVectorStore")]
internal sealed class SqlServerClient : ISqlServerClient
{
    private readonly SqlConnection _connection;
    private readonly string _schema;
    private readonly int _embeddingsDimensionsCount;

    /// <summary>
    /// Initializes a new instance of the <see cref="SqlServerClient"/> class.
    /// </summary>
    /// <param name="connection">Connection to use when working with database.</param>
    /// <param name="schema">Schema of collection tables.</param>
    /// <param name="embeddingsDimensionsCount">Number of dimensions that stored embeedings will use</param>
    public SqlServerClient(SqlConnection connection, string schema, int embeddingsDimensionsCount)
    {
        this._connection = connection;
        this._schema = schema;
        this._embeddingsDimensionsCount = embeddingsDimensionsCount;
    }

    private async Task CheckForRequiredNativeTypesAsync(CancellationToken cancellationToken = default)
    {
        using (await this.OpenConnectionAsync(cancellationToken).ConfigureAwait(false))
        {
            using var cmd = this._connection.CreateCommand();
            cmd.CommandText = "select count(*) from sys.types where (system_type_id = 244 and user_type_id = 244) or (system_type_id = 165 and schema_id = 4 and [name] = 'vector')";
            var typesCount = await cmd.ExecuteScalarAsync(cancellationToken).ConfigureAwait(false);
            if (typesCount == null || typesCount.Equals(DBNull.Value) || Convert.ToInt32(typesCount) != 2)
            {
                throw new InvalidOperationException("The database does not have the required native types.");
            }
        }
    }

    /// <inheritdoc/>
    public async Task CreateTableAsync(string tableName, CancellationToken cancellationToken = default)
    {
        await this.CheckForRequiredNativeTypesAsync(cancellationToken).ConfigureAwait(false);

        var fullTableName = this.GetSanitizedFullTableName(tableName);

        using (await this.OpenConnectionAsync(cancellationToken).ConfigureAwait(false))
        {
            using var cmd = this._connection.CreateCommand();
            cmd.CommandText = $"""
                IF OBJECT_ID(N'{fullTableName}', N'U') IS NULL
                CREATE TABLE {fullTableName} (
                    [key] NVARCHAR(255) COLLATE Latin1_General_100_BIN2 NOT NULL,
                    [metadata] JSON NOT NULL,
                    [embedding] VECTOR({this._embeddingsDimensionsCount}),
                    [timestamp] DATETIMEOFFSET,
                    PRIMARY KEY NONCLUSTERED ([key]),
                    INDEX IXC CLUSTERED ([timestamp] DESC)
                )
                """;
            await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> GetTablesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using (await this.OpenConnectionAsync(cancellationToken).ConfigureAwait(false))
        {
            using var cmd = SqlServerCommandBuilder.SelectTableNames(this._connection, this._schema);
            using var reader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
            while (await reader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                yield return reader.GetString(reader.GetOrdinal("table_name"));
            }
        }
    }

    /// <inheritdoc/>
    public async Task<bool> DoesTableExistsAsync(string tableName, CancellationToken cancellationToken = default)
    {
        using (await this.OpenConnectionAsync(cancellationToken).ConfigureAwait(false))
        {
            using var cmd = SqlServerCommandBuilder.SelectTableName(this._connection, this._schema, tableName);
            using var reader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
            return await reader.ReadAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public async Task DeleteTableAsync(string tableName, CancellationToken cancellationToken = default)
    {
        using (await this.OpenConnectionAsync(cancellationToken).ConfigureAwait(false))
        {
            using var cmd = SqlServerCommandBuilder.DropTableIfExists(this._connection, this._schema, tableName);
            await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public async Task UpsertAsync(string tableName, string key, string metadata, ReadOnlyMemory<float> embedding, DateTimeOffset? timestamp, CancellationToken cancellationToken = default)
    {
        using (await this.OpenConnectionAsync(cancellationToken).ConfigureAwait(false))
        {
            using var cmd = this._connection.CreateCommand();
            var fullTableName = this.GetSanitizedFullTableName(tableName);
            cmd.CommandText = $"""
                MERGE INTO {fullTableName} AS t
                USING (VALUES (@key, @metadata, @embedding, @timestamp)) AS s ([key], [metadata], [embedding], [timestamp])
                ON (t.[key] = s.[key])
                WHEN MATCHED THEN
                    UPDATE SET t.[metadata] = s.[metadata], t.[embedding] = s.[embedding], t.[timestamp] = s.[timestamp]
                WHEN NOT MATCHED THEN
                    INSERT ([key], [metadata], [embedding], [timestamp])
                    VALUES (s.[key], s.[metadata], s.[embedding], s.[timestamp]);
                """;
            cmd.Parameters.AddWithValue("@key", key);
            cmd.Parameters.AddWithValue("@metadata", metadata);
            cmd.Parameters.AddWithValue("@embedding", this.SerializeEmbedding((ReadOnlyMemory<float>)embedding));
            cmd.Parameters.AddWithValue("@timestamp", timestamp ?? (object)DBNull.Value);
            await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<SqlServerMemoryEntry> ReadBatchAsync(string tableName, IEnumerable<string> keys, bool withEmbeddings = false, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var queryColumns = "[key], [metadata], [timestamp]" + (withEmbeddings ? ", [embedding]" : string.Empty);

        var fullTableName = this.GetSanitizedFullTableName(tableName);
        var keysList = keys.ToList();
        var keysParams = string.Join(", ", keysList.Select((_, i) => $"@k{i}"));
        using (await this.OpenConnectionAsync(cancellationToken).ConfigureAwait(false))
        {
            using var cmd = this._connection.CreateCommand();
            cmd.CommandText = $"""
                SELECT {queryColumns}
                FROM {fullTableName}
                WHERE [key] IN ({keysParams})
                """;
            for (var i = 0; i < keysList.Count; i++)
            {
                cmd.Parameters.AddWithValue($"k{i}", keysList[i]);
            }
            using var reader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
            while (await reader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                yield return this.ReadEntry(reader, withEmbeddings);
            }
        }
    }

    /// <inheritdoc/>
    public async Task DeleteBatchAsync(string tableName, IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        var fullTableName = this.GetSanitizedFullTableName(tableName);
        var keysList = keys.ToList();
        var keysParams = string.Join(", ", keysList.Select((_, i) => $"@k{i}"));
        using (await this.OpenConnectionAsync(cancellationToken).ConfigureAwait(false))
        {
            using var cmd = this._connection.CreateCommand();
            cmd.CommandText = $"""
                DELETE
                FROM {fullTableName}
                WHERE [key] IN ({keysParams})
                """;
            for (var i = 0; i < keysList.Count; i++)
            {
                cmd.Parameters.AddWithValue($"k{i}", keysList[i]);
            }
            await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<(SqlServerMemoryEntry, double)> GetNearestMatchesAsync(string tableName, ReadOnlyMemory<float> embedding, int limit, double minRelevanceScore = 0, bool withEmbeddings = false, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var queryColumns = $"[key], [metadata], [timestamp], 1 - VECTOR_DISTANCE('cosine', [embedding], CAST(@e AS VECTOR({embedding.Length}))) AS [cosine_similarity]" + (withEmbeddings ? ", [embedding]" : string.Empty);
        var fullTableName = this.GetSanitizedFullTableName(tableName);
        using (await this.OpenConnectionAsync(cancellationToken).ConfigureAwait(false))
        {
            using var cmd = this._connection.CreateCommand();
            cmd.CommandText = $"""
                WITH data as (
                    SELECT {queryColumns}
                    FROM {fullTableName}
                )
                SELECT TOP (@limit) *
                FROM data
                WHERE [cosine_similarity] >= @score
                ORDER BY [cosine_similarity] DESC
                """;
            cmd.Parameters.AddWithValue("@e", this.SerializeEmbedding(embedding));
            cmd.Parameters.AddWithValue("@limit", limit);
            cmd.Parameters.AddWithValue("@score", minRelevanceScore);
            using var reader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
            while (await reader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                var cosineSimilarity = reader.GetDouble(reader.GetOrdinal("cosine_similarity"));
                yield return (this.ReadEntry(reader, withEmbeddings), cosineSimilarity);
            }
        }
    }

    private string GetSanitizedFullTableName(string tableName) => $"{DelimitIdentifier(this._schema)}.{DelimitIdentifier(tableName)}";

    private string SerializeEmbedding(ReadOnlyMemory<float> embedding) => JsonSerializer.Serialize(embedding);

    private ReadOnlyMemory<float> DeserializeEmbedding(string embedding) => JsonSerializer.Deserialize<ReadOnlyMemory<float>>(embedding);

    private SqlServerMemoryEntry ReadEntry(SqlDataReader reader, bool hasEmbedding)
    {
        var key = reader.GetString(reader.GetOrdinal("key"));
        var metadata = reader.GetString(reader.GetOrdinal("metadata"));
        var timestamp = !reader.IsDBNull(reader.GetOrdinal("timestamp"))
            ? reader.GetDateTimeOffset(reader.GetOrdinal("timestamp"))
            : (DateTimeOffset?)null;
        var embedding = hasEmbedding && !reader.IsDBNull(reader.GetOrdinal("embedding"))
            ? this.DeserializeEmbedding(reader.GetString(reader.GetOrdinal("embedding")))
            : null;
        return new SqlServerMemoryEntry() { Key = key, MetadataString = metadata, Embedding = embedding, Timestamp = timestamp };
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

    private static string DelimitIdentifier(string identifier) => $"[{EscapeIdentifier(identifier)}]";

    private static string EscapeIdentifier(string identifier) => identifier.Replace("]", "]]");

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
}
