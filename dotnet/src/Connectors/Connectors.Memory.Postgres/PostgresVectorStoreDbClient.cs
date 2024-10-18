// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Npgsql;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

/// <summary>
/// An implementation of a client for Postgres. This class is used to managing postgres database operations.
/// </summary>
/// <remarks>
/// Initializes a new instance of the <see cref="PostgresDbClient"/> class.
/// </remarks>
/// <param name="dataSource">Postgres data source.</param>
/// <param name="schema">Schema of collection tables.</param>
/// <param name="sqlBuilder">Sql builder for collection tables.</param>
[System.Diagnostics.CodeAnalysis.SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities", Justification = "We need to build the full table name using schema and collection, it does not support parameterized passing.")]
public class PostgresVectorStoreDbClient(NpgsqlDataSource dataSource, string schema, IPostgresVectorStoreCollectionSqlBuilder sqlBuilder) : IPostgresVectorStoreDbClient
{
    private readonly NpgsqlDataSource _dataSource = dataSource;
    private readonly IPostgresVectorStoreCollectionSqlBuilder _sqlBuilder = sqlBuilder;
    private readonly string _schema = schema;

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresVectorStoreDbClient"/> class.
    /// </summary>
    /// <param name="dataSource">Postgres data source.</param>
    /// <param name="schema">Schema of collection tables.</param>
    public PostgresVectorStoreDbClient(NpgsqlDataSource dataSource, string schema = "public") : this(dataSource, schema, new PostgresVectorStoreCollectionSqlBuilder()) { }

    /// <inheritdoc />
    public async Task<bool> DoesTableExistsAsync(string tableName, CancellationToken cancellationToken = default)
    {
        NpgsqlConnection connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

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
        NpgsqlConnection connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

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
    public async Task CreateTableAsync(string tableName, VectorStoreRecordDefinition recordDefinition, bool ifNotExists = true, CancellationToken cancellationToken = default)
    {
        NpgsqlConnection connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        await using (connection)
        {
            var commandInfo = this._sqlBuilder.BuildCreateTableCommand(this._schema, tableName, recordDefinition, ifNotExists);
            using NpgsqlCommand cmd = commandInfo.ToNpgsqlCommand(connection);
            await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc />
    public async Task DeleteTableAsync(string tableName, CancellationToken cancellationToken = default)
    {
        NpgsqlConnection connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        await using (connection)
        {
            var commandInfo = this._sqlBuilder.BuildDropTableCommand(this._schema, tableName);
            using NpgsqlCommand cmd = commandInfo.ToNpgsqlCommand(connection);
            await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc />
    public async Task UpsertAsync(string tableName, Dictionary<string, object?> row, string keyColumn, CancellationToken cancellationToken = default)
    {
        NpgsqlConnection connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        await using (connection)
        {
            var commandInfo = this._sqlBuilder.BuildUpsertCommand(this._schema, tableName, row, keyColumn);
            using NpgsqlCommand cmd = commandInfo.ToNpgsqlCommand(connection);
            await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    /// <inheritdoc />
    public async Task<Dictionary<string, object?>?> GetAsync<TKey>(string tableName, TKey key, VectorStoreRecordDefinition recordDefinition, bool includeVectors = false, CancellationToken cancellationToken = default) where TKey : notnull
    {
        NpgsqlConnection connection = await this._dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        await using (connection)
        {
            var commandInfo = this._sqlBuilder.BuildGetCommand(this._schema, tableName, recordDefinition, key, includeVectors);
            using NpgsqlCommand cmd = commandInfo.ToNpgsqlCommand(connection);
            using NpgsqlDataReader dataReader = await cmd.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
            if (await dataReader.ReadAsync(cancellationToken).ConfigureAwait(false))
            {
                return this.GetRecord(dataReader, recordDefinition.Properties, includeVectors);
            }

            return null;
        }
    }

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
}
