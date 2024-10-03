// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text;
using Microsoft.Data.Sqlite;

namespace Microsoft.SemanticKernel.Connectors.Sqlite;

/// <summary>
/// Command builder for queries in SQLite database.
/// </summary>
internal class SqliteVectorStoreCollectionCommandBuilder
{
    /// <summary><see cref="SqliteConnection"/> that will be used to manage the data in SQLite.</summary>
    private readonly SqliteConnection _connection;

    /// <summary>
    /// Initializes a new instance of the <see cref="SqliteVectorStoreCollectionCommandBuilder"/> class.
    /// </summary>
    /// <param name="connection"><see cref="SqliteConnection"/> that will be used to manage the data in SQLite.</param>
    public SqliteVectorStoreCollectionCommandBuilder(SqliteConnection connection)
    {
        Verify.NotNull(connection);

        this._connection = connection;
    }

    public SqliteCommand BuildTableCountCommand(string tableName)
    {
        const string SystemTable = "sqlite_master";
        const string ParameterName = "@tableName";

        var query = $"SELECT count(*) FROM {SystemTable} WHERE type='table' AND name={ParameterName};";

        var command = new SqliteCommand(query, this._connection);

        command.Parameters.AddWithValue(ParameterName, tableName);

        return command;
    }

    [SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities", Justification = "Query does not contain user input.")]
    public SqliteCommand BuildCreateTableCommand(string tableName, IReadOnlyList<SqliteColumn> columns, bool ifNotExists)
    {
        var builder = new StringBuilder();

        builder.AppendLine($"CREATE TABLE {(ifNotExists ? "IF NOT EXISTS " : string.Empty)}{tableName} (");

        builder.AppendLine(string.Join(",\n", columns.Select(GetColumnDefinition)));
        builder.Append(");");

        var query = builder.ToString();

        return new SqliteCommand(query, this._connection);
    }

    [SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities", Justification = "Query does not contain user input.")]
    public SqliteCommand BuildCreateVirtualTableCommand(
        string tableName,
        IReadOnlyList<SqliteColumn> columns,
        bool ifNotExists,
        string extensionName)
    {
        var builder = new StringBuilder();

        builder.AppendLine($"CREATE VIRTUAL TABLE {(ifNotExists ? "IF NOT EXISTS " : string.Empty)}{tableName} USING {extensionName}(");

        builder.AppendLine(string.Join(",\n", columns.Select(GetColumnDefinition)));
        builder.Append(");");

        var query = builder.ToString();

        return new SqliteCommand(query, this._connection);
    }

    [SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities", Justification = "Query does not contain user input.")]
    public SqliteCommand BuildDropTableCommand(string tableName)
    {
        string query = $"DROP TABLE [{tableName}];";

        return new SqliteCommand(query, this._connection);
    }

    [SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities", Justification = "User input is passed using command parameters.")]
    public SqliteCommand BuildInsertOrReplaceCommand(
        string tableName,
        IReadOnlyList<string> propertyNames,
        IReadOnlyList<Dictionary<string, object?>> records,
        bool shouldReturnKey = false)
    {
        var builder = new StringBuilder();
        var command = new SqliteCommand();

        for (var recordIndex = 0; recordIndex < records.Count; recordIndex++)
        {
            var columns = new List<string>();
            var valueParameters = new List<string>();
            var values = new List<object?>();

            var record = records[recordIndex];

            foreach (var propertyName in propertyNames)
            {
                if (record.TryGetValue(propertyName, out var value))
                {
                    columns.Add(propertyName);
                    valueParameters.Add($"@{propertyName}{recordIndex}");
                    values.Add(value ?? DBNull.Value);
                }
            }

            builder.AppendLine($"INSERT OR REPLACE INTO {tableName} ({string.Join(", ", columns)})");
            builder.AppendLine($"VALUES ({string.Join(", ", valueParameters)});");

            if (shouldReturnKey)
            {
                builder.AppendLine("SELECT last_insert_rowid();");
            }

            for (var i = 0; i < valueParameters.Count; i++)
            {
                command.Parameters.AddWithValue(valueParameters[i], values[i]);
            }
        }

        var query = builder.ToString();

        command.CommandText = query;
        command.Connection = this._connection;

        return command;
    }

    [SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities", Justification = "User input is passed using command parameters.")]
    public SqliteCommand BuildSelectCommand<TKey>(
        string tableName,
        string keyStoragePropertyName,
        IReadOnlyList<string> propertyNames,
        IReadOnlyList<TKey> keys)
    {
        var command = new SqliteCommand();
        var keyPropertyParameterNames = new List<string>();

        for (var keyIndex = 0; keyIndex < keys.Count; keyIndex++)
        {
            var keyPropertyParameterName = $"@{keyStoragePropertyName}{keyIndex}";
            keyPropertyParameterNames.Add(keyPropertyParameterName);

            command.Parameters.AddWithValue($"{keyPropertyParameterName}", keys[keyIndex]);
        }

        var whereClause = keyPropertyParameterNames.Count == 1 ?
            $"{keyStoragePropertyName} = {keyPropertyParameterNames[0]}" :
            $"{keyStoragePropertyName} IN ({string.Join(", ", keyPropertyParameterNames)})";

        var query =
            $"SELECT {string.Join(", ", propertyNames)} " +
            $"FROM {tableName} " +
            $"WHERE {whereClause}";

        command.CommandText = query;
        command.Connection = this._connection;

        return command;
    }

    [SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities", Justification = "User input is passed using command parameters.")]
    public SqliteCommand BuildSelectLeftJoinCommand<TKey>(
        string leftTable,
        string rightTable,
        string keyStoragePropertyName,
        IReadOnlyList<string> leftTablePropertyNames,
        IReadOnlyList<string> rightTablePropertyNames,
        IReadOnlyList<TKey> keys)
    {
        const string LeftTableIdentifier = "l";
        const string RightTableIdentifier = "r";

        var command = new SqliteCommand();
        var keyPropertyParameterNames = new List<string>();

        for (var keyIndex = 0; keyIndex < keys.Count; keyIndex++)
        {
            var keyPropertyParameterName = $"@{keyStoragePropertyName}{keyIndex}";
            keyPropertyParameterNames.Add(keyPropertyParameterName);

            command.Parameters.AddWithValue($"{keyPropertyParameterName}", keys[keyIndex]);
        }

        List<string> propertyNames =
        [
            .. leftTablePropertyNames.Select(property => $"{LeftTableIdentifier}.{property}"),
            .. rightTablePropertyNames.Select(property => $"{RightTableIdentifier}.{property}"),
        ];

        var whereClause = keyPropertyParameterNames.Count == 1 ?
            $"{LeftTableIdentifier}.{keyStoragePropertyName} = {keyPropertyParameterNames[0]}" :
            $"{LeftTableIdentifier}.{keyStoragePropertyName} IN ({string.Join(", ", keyPropertyParameterNames)})";

        var query =
            $"SELECT {string.Join(", ", propertyNames)} " +
            $"FROM {leftTable} {LeftTableIdentifier} " +
            $"LEFT JOIN {rightTable} {RightTableIdentifier} ON {LeftTableIdentifier}.{keyStoragePropertyName} = {RightTableIdentifier}.{keyStoragePropertyName} " +
            $"WHERE {whereClause}";

        command.CommandText = query;
        command.Connection = this._connection;

        return command;
    }

    #region private

    private static string GetColumnDefinition(SqliteColumn column)
    {
        const string PrimaryKeyIdentifier = "PRIMARY KEY";

        var primaryKeyPlaceholder = column.IsPrimary ? $" {PrimaryKeyIdentifier}" : string.Empty;
        return $"{column.Name} {column.Type}{primaryKeyPlaceholder}";
    }

    #endregion
}
