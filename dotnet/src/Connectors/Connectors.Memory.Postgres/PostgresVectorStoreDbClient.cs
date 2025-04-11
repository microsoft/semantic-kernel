// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Npgsql;
using Pgvector;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

/// <summary>
/// An implementation of a client for Postgres. This class is used to managing postgres database operations.
/// </summary>
/// <remarks>
/// Initializes a new instance of the <see cref="PostgresVectorStoreDbClient"/> class.
/// </remarks>
/// <param name="dataSource">Postgres data source.</param>
/// <param name="schema">Schema of collection tables.</param>
[System.Diagnostics.CodeAnalysis.SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities", Justification = "We need to build the full table name using schema and collection, it does not support parameterized passing.")]
internal class PostgresVectorStoreDbClient(NpgsqlDataSource dataSource, string schema = PostgresConstants.DefaultSchema) : IPostgresVectorStoreDbClient
{
    private readonly string _schema = schema;

    private readonly NpgsqlConnectionStringBuilder _connectionStringBuilder = new(dataSource.ConnectionString);

    public NpgsqlDataSource DataSource { get; } = dataSource;

    public string? DatabaseName => this._connectionStringBuilder.Database;

    /// <inheritdoc />
    public async Task<bool> DoesTableExistsAsync(string tableName, CancellationToken cancellationToken = default)
    {
        NpgsqlConnection connection = await this.DataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        await using (connection)
        {
            var commandInfo = PostgresSqlBuilder.BuildDoesTableExistCommand(this._schema, tableName);
            using NpgsqlCommand cmd = commandInfo.ToNpgsqlCommand(connection);
            using NpgsqlDataReader dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
            if (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                return dataReader.GetString(dataReader.GetOrdinal("table_name")) == tableName;
            }

            return false;
        }
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> GetTablesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        NpgsqlConnection connection = await this.DataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        await using (connection)
        {
            var commandInfo = PostgresSqlBuilder.BuildGetTablesCommand(this._schema);
            using NpgsqlCommand cmd = commandInfo.ToNpgsqlCommand(connection);
            using NpgsqlDataReader dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
            while (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                yield return dataReader.GetString(dataReader.GetOrdinal("table_name"));
            }
        }
    }

    /// <inheritdoc />
    public async Task CreateTableAsync(string tableName, VectorStoreRecordModel model, bool ifNotExists = true, CancellationToken cancellationToken = default)
    {
        // Prepare the SQL commands.
        var commandInfo = PostgresSqlBuilder.BuildCreateTableCommand(this._schema, tableName, model, ifNotExists);
        var createIndexCommands =
            PostgresVectorStoreRecordPropertyMapping.GetIndexInfo(model.Properties)
                .Select(index =>
                    PostgresSqlBuilder.BuildCreateIndexCommand(this._schema, tableName, index.column, index.kind, index.function, index.isVector, ifNotExists));

        // Execute the commands in a transaction.
        NpgsqlConnection connection = await this.DataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        await using (connection)
        {
#if NET8_0_OR_GREATER
            var transaction = await connection.BeginTransactionAsync(cancellationToken).ConfigureAwait(false);
            await using (transaction)
#else
            var transaction = connection.BeginTransaction();
            using (transaction)
#endif
            {
                using NpgsqlCommand cmd = commandInfo.ToNpgsqlCommand(connection, transaction);
                await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);

                foreach (var createIndexCommand in createIndexCommands)
                {
                    using NpgsqlCommand indexCmd = createIndexCommand.ToNpgsqlCommand(connection, transaction);
                    await indexCmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
                }

#if NET8_0_OR_GREATER
                await transaction.CommitAsync(cancellationToken).ConfigureAwait(false);
#else
                transaction.Commit();
#endif
            }
        }
    }

    /// <inheritdoc />
    public async Task DeleteTableAsync(string tableName, CancellationToken cancellationToken = default)
    {
        var commandInfo = PostgresSqlBuilder.BuildDropTableCommand(this._schema, tableName);
        await this.ExecuteNonQueryAsync(commandInfo, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task UpsertAsync(string tableName, Dictionary<string, object?> row, string keyColumn, CancellationToken cancellationToken = default)
    {
        var commandInfo = PostgresSqlBuilder.BuildUpsertCommand(this._schema, tableName, keyColumn, row);
        await this.ExecuteNonQueryAsync(commandInfo, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task UpsertBatchAsync(string tableName, IEnumerable<Dictionary<string, object?>> rows, string keyColumn, CancellationToken cancellationToken = default)
    {
        var commandInfo = PostgresSqlBuilder.BuildUpsertBatchCommand(this._schema, tableName, keyColumn, rows.ToList());
        await this.ExecuteNonQueryAsync(commandInfo, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task<Dictionary<string, object?>?> GetAsync<TKey>(string tableName, TKey key, VectorStoreRecordModel model, bool includeVectors = false, CancellationToken cancellationToken = default) where TKey : notnull
    {
        NpgsqlConnection connection = await this.DataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        await using (connection)
        {
            var commandInfo = PostgresSqlBuilder.BuildGetCommand(this._schema, tableName, model, key, includeVectors);
            using NpgsqlCommand cmd = commandInfo.ToNpgsqlCommand(connection);
            using NpgsqlDataReader dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
            if (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                return this.GetRecord(dataReader, model, includeVectors);
            }

            return null;
        }
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<Dictionary<string, object?>> GetBatchAsync<TKey>(string tableName, IEnumerable<TKey> keys, VectorStoreRecordModel model, bool includeVectors = false, [EnumeratorCancellation] CancellationToken cancellationToken = default)
        where TKey : notnull
    {
        Verify.NotNull(keys);

        List<TKey> listOfKeys = keys.ToList();
        if (listOfKeys.Count == 0)
        {
            yield break;
        }

        NpgsqlConnection connection = await this.DataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        await using (connection)
        {
            var commandInfo = PostgresSqlBuilder.BuildGetBatchCommand(this._schema, tableName, model, listOfKeys, includeVectors);
            using NpgsqlCommand cmd = commandInfo.ToNpgsqlCommand(connection);
            using NpgsqlDataReader dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
            while (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                yield return this.GetRecord(dataReader, model, includeVectors);
            }
        }
    }

    /// <inheritdoc />
    public async Task DeleteAsync<TKey>(string tableName, string keyColumn, TKey key, CancellationToken cancellationToken = default)
    {
        var commandInfo = PostgresSqlBuilder.BuildDeleteCommand(this._schema, tableName, keyColumn, key);
        await this.ExecuteNonQueryAsync(commandInfo, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<(Dictionary<string, object?> Row, double Distance)> GetNearestMatchesAsync<TRecord>(
        string tableName, VectorStoreRecordModel model, VectorStoreRecordVectorPropertyModel vectorProperty, Vector vectorValue, int limit,
        VectorSearchOptions<TRecord> options, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        NpgsqlConnection connection = await this.DataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        await using (connection)
        {
            var commandInfo = PostgresSqlBuilder.BuildGetNearestMatchCommand(this._schema, tableName, model, vectorProperty, vectorValue,
#pragma warning disable CS0618 // VectorSearchFilter is obsolete
                options.OldFilter,
#pragma warning restore CS0618 // VectorSearchFilter is obsolete
                options.Filter, options.Skip, options.IncludeVectors, limit);
            using NpgsqlCommand cmd = commandInfo.ToNpgsqlCommand(connection);
            using NpgsqlDataReader dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
            while (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                var distance = dataReader.GetDouble(dataReader.GetOrdinal(PostgresConstants.DistanceColumnName));
                yield return (Row: this.GetRecord(dataReader, model, options.IncludeVectors), Distance: distance);
            }
        }
    }

    public async IAsyncEnumerable<Dictionary<string, object?>> GetMatchingRecordsAsync<TRecord>(string tableName, VectorStoreRecordModel model,
        Expression<Func<TRecord, bool>> filter, int top, GetFilteredRecordOptions<TRecord> options, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        NpgsqlConnection connection = await this.DataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        await using (connection)
        {
            var commandInfo = PostgresSqlBuilder.BuildSelectWhereCommand(this._schema, tableName, model, filter, top, options);
            using NpgsqlCommand cmd = commandInfo.ToNpgsqlCommand(connection);
            using NpgsqlDataReader dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);

            while (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                yield return this.GetRecord(dataReader, model, options.IncludeVectors);
            }
        }
    }

    /// <inheritdoc />
    public async Task DeleteBatchAsync<TKey>(string tableName, string keyColumn, IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
    {
        var listOfKeys = keys.ToList();
        if (listOfKeys.Count == 0)
        {
            return;
        }

        var commandInfo = PostgresSqlBuilder.BuildDeleteBatchCommand(this._schema, tableName, keyColumn, listOfKeys);
        await this.ExecuteNonQueryAsync(commandInfo, cancellationToken).ConfigureAwait(false);
    }

    #region private ================================================================================

    private Dictionary<string, object?> GetRecord(
        NpgsqlDataReader reader,
        VectorStoreRecordModel model,
        bool includeVectors = false
    )
    {
        var storageModel = new Dictionary<string, object?>();

        foreach (var property in model.Properties)
        {
            var isEmbedding = property is VectorStoreRecordVectorPropertyModel;
            var propertyName = property.StorageName;
            var propertyType = property.Type;
            var propertyValue = !isEmbedding || includeVectors ? PostgresVectorStoreRecordPropertyMapping.GetPropertyValue(reader, propertyName, propertyType) : null;

            storageModel.Add(propertyName, propertyValue);
        }

        return storageModel;
    }

    private async Task ExecuteNonQueryAsync(PostgresSqlCommandInfo commandInfo, CancellationToken cancellationToken)
    {
        NpgsqlConnection connection = await this.DataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        await using (connection)
        {
            using NpgsqlCommand cmd = commandInfo.ToNpgsqlCommand(connection);
            await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    #endregion
}
