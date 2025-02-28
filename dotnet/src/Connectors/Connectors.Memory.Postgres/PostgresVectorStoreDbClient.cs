// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Npgsql;
using Pgvector;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

/// <summary>
/// An implementation of a client for Postgres. This class is used to managing postgres database operations.
/// </summary>
/// <remarks>
/// Initializes a new instance of the <see cref="PostgresDbClient"/> class.
/// </remarks>
/// <param name="dataSource">Postgres data source.</param>
/// <param name="schema">Schema of collection tables.</param>
[System.Diagnostics.CodeAnalysis.SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities", Justification = "We need to build the full table name using schema and collection, it does not support parameterized passing.")]
internal class PostgresVectorStoreDbClient(NpgsqlDataSource dataSource, string schema = PostgresConstants.DefaultSchema) : IPostgresVectorStoreDbClient
{
    private readonly string _schema = schema;

    private IPostgresVectorStoreCollectionSqlBuilder _sqlBuilder = new PostgresVectorStoreCollectionSqlBuilder();

    public NpgsqlDataSource DataSource { get; } = dataSource;

    /// <inheritdoc />
    public async Task<bool> DoesTableExistsAsync(string tableName, CancellationToken cancellationToken = default)
    {
        NpgsqlConnection connection = await this.DataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        await using (connection)
        {
            var commandInfo = this._sqlBuilder.BuildDoesTableExistCommand(this._schema, tableName);
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
            var commandInfo = this._sqlBuilder.BuildGetTablesCommand(this._schema);
            using NpgsqlCommand cmd = commandInfo.ToNpgsqlCommand(connection);
            using NpgsqlDataReader dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
            while (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                yield return dataReader.GetString(dataReader.GetOrdinal("table_name"));
            }
        }
    }

    /// <inheritdoc />
    public async Task CreateTableAsync(string tableName, IReadOnlyList<VectorStoreRecordProperty> properties, bool ifNotExists = true, CancellationToken cancellationToken = default)
    {
        // Prepare the SQL commands.
        var commandInfo = this._sqlBuilder.BuildCreateTableCommand(this._schema, tableName, properties, ifNotExists);
        var createIndexCommands =
            PostgresVectorStoreRecordPropertyMapping.GetVectorIndexInfo(properties)
                .Select(index =>
                    this._sqlBuilder.BuildCreateVectorIndexCommand(this._schema, tableName, index.column, index.kind, index.function, ifNotExists)
                );

        // Execute the commands in a transaction.
        NpgsqlConnection connection = await this.DataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        await using (connection)
        {
#if !NETSTANDARD2_0
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

#if !NETSTANDARD2_0
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
        var commandInfo = this._sqlBuilder.BuildDropTableCommand(this._schema, tableName);
        await this.ExecuteNonQueryAsync(commandInfo, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task UpsertAsync(string tableName, Dictionary<string, object?> row, string keyColumn, CancellationToken cancellationToken = default)
    {
        var commandInfo = this._sqlBuilder.BuildUpsertCommand(this._schema, tableName, keyColumn, row);
        await this.ExecuteNonQueryAsync(commandInfo, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task UpsertBatchAsync(string tableName, IEnumerable<Dictionary<string, object?>> rows, string keyColumn, CancellationToken cancellationToken = default)
    {
        var commandInfo = this._sqlBuilder.BuildUpsertBatchCommand(this._schema, tableName, keyColumn, rows.ToList());
        await this.ExecuteNonQueryAsync(commandInfo, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task<Dictionary<string, object?>?> GetAsync<TKey>(string tableName, TKey key, IReadOnlyList<VectorStoreRecordProperty> properties, bool includeVectors = false, CancellationToken cancellationToken = default) where TKey : notnull
    {
        NpgsqlConnection connection = await this.DataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        await using (connection)
        {
            var commandInfo = this._sqlBuilder.BuildGetCommand(this._schema, tableName, properties, key, includeVectors);
            using NpgsqlCommand cmd = commandInfo.ToNpgsqlCommand(connection);
            using NpgsqlDataReader dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
            if (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                return this.GetRecord(dataReader, properties, includeVectors);
            }

            return null;
        }
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<Dictionary<string, object?>> GetBatchAsync<TKey>(string tableName, IEnumerable<TKey> keys, IReadOnlyList<VectorStoreRecordProperty> properties, bool includeVectors = false, [EnumeratorCancellation] CancellationToken cancellationToken = default)
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
            var commandInfo = this._sqlBuilder.BuildGetBatchCommand(this._schema, tableName, properties, listOfKeys, includeVectors);
            using NpgsqlCommand cmd = commandInfo.ToNpgsqlCommand(connection);
            using NpgsqlDataReader dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
            while (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                yield return this.GetRecord(dataReader, properties, includeVectors);
            }
        }
    }

    /// <inheritdoc />
    public async Task DeleteAsync<TKey>(string tableName, string keyColumn, TKey key, CancellationToken cancellationToken = default)
    {
        var commandInfo = this._sqlBuilder.BuildDeleteCommand(this._schema, tableName, keyColumn, key);
        await this.ExecuteNonQueryAsync(commandInfo, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
#pragma warning disable CS0618 // VectorSearchFilter is obsolete
    public async IAsyncEnumerable<(Dictionary<string, object?> Row, double Distance)> GetNearestMatchesAsync<TRecord>(
        string tableName, VectorStoreRecordPropertyReader propertyReader, VectorStoreRecordVectorProperty vectorProperty, Vector vectorValue, int limit,
        VectorSearchFilter? legacyFilter = default, Expression<Func<TRecord, bool>>? newFilter = default, int? skip = default, bool includeVectors = false, [EnumeratorCancellation] CancellationToken cancellationToken = default)
#pragma warning restore CS0618 // VectorSearchFilter is obsolete
    {
        NpgsqlConnection connection = await this.DataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        await using (connection)
        {
            var commandInfo = this._sqlBuilder.BuildGetNearestMatchCommand(this._schema, tableName, propertyReader, vectorProperty, vectorValue, legacyFilter, newFilter, skip, includeVectors, limit);
            using NpgsqlCommand cmd = commandInfo.ToNpgsqlCommand(connection);
            using NpgsqlDataReader dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
            while (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                var distance = dataReader.GetDouble(dataReader.GetOrdinal(PostgresConstants.DistanceColumnName));
                yield return (Row: this.GetRecord(dataReader, propertyReader.RecordDefinition.Properties, includeVectors), Distance: distance);
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

        var commandInfo = this._sqlBuilder.BuildDeleteBatchCommand(this._schema, tableName, keyColumn, listOfKeys);
        await this.ExecuteNonQueryAsync(commandInfo, cancellationToken).ConfigureAwait(false);
    }

    #region internal ===============================================================================

    /// <summary>
    /// Sets the SQL builder for the client.
    /// </summary>
    /// <param name="sqlBuilder"></param>
    /// <remarks>
    /// This method is used for other Semnatic Kernel connectors that may need to override the default SQL
    /// used by this client.
    /// </remarks>
    internal void SetSqlBuilder(IPostgresVectorStoreCollectionSqlBuilder sqlBuilder)
    {
        this._sqlBuilder = sqlBuilder;
    }

    #endregion

    #region private ================================================================================

    private Dictionary<string, object?> GetRecord(
        NpgsqlDataReader reader,
        IEnumerable<VectorStoreRecordProperty> properties,
        bool includeVectors = false
    )
    {
        var storageModel = new Dictionary<string, object?>();

        foreach (var property in properties)
        {
            var isEmbedding = property is VectorStoreRecordVectorProperty;
            var propertyName = property.StoragePropertyName ?? property.DataModelPropertyName;
            var propertyType = property.PropertyType;
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
