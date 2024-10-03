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
[SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities", Justification = "User input is passed using command parameters.")]
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

    public SqliteCommand BuildCreateTableCommand(string tableName, IReadOnlyList<SqliteColumn> columns, bool ifNotExists)
    {
        var builder = new StringBuilder();

        builder.AppendLine($"CREATE TABLE {(ifNotExists ? "IF NOT EXISTS " : string.Empty)}{tableName} (");

        builder.AppendLine(string.Join(",\n", columns.Select(GetColumnDefinition)));
        builder.Append(");");

        var query = builder.ToString();

        return new SqliteCommand(query, this._connection);
    }

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

    public SqliteCommand BuildDropTableCommand(string tableName)
    {
        string query = $"DROP TABLE [{tableName}];";

        return new SqliteCommand(query, this._connection);
    }

    public SqliteCommand BuildInsertCommand(
        string tableName,
        string keyStoragePropertyName,
        IReadOnlyList<string> propertyNames,
        IReadOnlyList<Dictionary<string, object?>> records,
        bool replaceIfExists = false)
    {
        var builder = new StringBuilder();
        var command = new SqliteCommand();

        var replacePlaceholder = replaceIfExists ? " OR REPLACE" : string.Empty;

        for (var recordIndex = 0; recordIndex < records.Count; recordIndex++)
        {
            var keyParameterName = GetParameterName(keyStoragePropertyName, recordIndex);

            var (columns, parameters, values) = GetQueryParts(
                propertyNames,
                records[recordIndex],
                recordIndex);

            builder.AppendLine($"INSERT{replacePlaceholder} INTO {tableName} ({string.Join(", ", columns)})");
            builder.AppendLine($"VALUES ({string.Join(", ", parameters)})");
            builder.AppendLine($"RETURNING {keyStoragePropertyName};");

            for (var i = 0; i < parameters.Count; i++)
            {
                command.Parameters.AddWithValue(parameters[i], values[i]);
            }
        }

        var query = builder.ToString();

        command.CommandText = query;
        command.Connection = this._connection;

        return command;
    }

    public SqliteCommand BuildSelectCommand<TKey>(
        string tableName,
        string keyStoragePropertyName,
        IReadOnlyList<string> propertyNames,
        IReadOnlyList<TKey> keys)
    {
        var (command, parameterNames) = GetCommandWithParameterNames(keyStoragePropertyName, keys);

        var equalityClause = GetEqualityClause(keyStoragePropertyName, parameterNames);

        var query =
            $"SELECT {string.Join(", ", propertyNames)} " +
            $"FROM {tableName} " +
            $"WHERE {equalityClause}";

        command.CommandText = query;
        command.Connection = this._connection;

        return command;
    }

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

        List<string> propertyNames =
        [
            .. leftTablePropertyNames.Select(property => $"{LeftTableIdentifier}.{property}"),
            .. rightTablePropertyNames.Select(property => $"{RightTableIdentifier}.{property}"),
        ];

        var (command, parameterNames) = GetCommandWithParameterNames(keyStoragePropertyName, keys);

        var equalityClause = GetEqualityClause(
            $"{LeftTableIdentifier}.{keyStoragePropertyName}",
            parameterNames);

        var query =
            $"SELECT {string.Join(", ", propertyNames)} " +
            $"FROM {leftTable} {LeftTableIdentifier} " +
            $"LEFT JOIN {rightTable} {RightTableIdentifier} ON {LeftTableIdentifier}.{keyStoragePropertyName} = {RightTableIdentifier}.{keyStoragePropertyName} " +
            $"WHERE {equalityClause}";

        command.CommandText = query;
        command.Connection = this._connection;

        return command;
    }

    public SqliteCommand BuildDeleteCommand<TKey>(
        string tableName,
        string keyStoragePropertyName,
        IReadOnlyList<TKey> keys)
    {
        var (command, parameterNames) = GetCommandWithParameterNames(keyStoragePropertyName, keys);

        var equalityClause = GetEqualityClause(keyStoragePropertyName, parameterNames);

        var query =
            $"DELETE FROM {tableName} " +
            $"WHERE {equalityClause}";

        command.CommandText = query;
        command.Connection = this._connection;

        return command;
    }

    #region private

    private static string GetColumnDefinition(SqliteColumn column)
    {
        const string PrimaryKeyIdentifier = "PRIMARY KEY";

        List<string> columnDefinitionParts = [column.Name, column.Type];

        if (column.IsPrimary)
        {
            columnDefinitionParts.Add(PrimaryKeyIdentifier);
        }

        if (column.Configuration is { Count: > 0 })
        {
            columnDefinitionParts.AddRange(column.Configuration
                .Select(configuration => $"{configuration.Key}={configuration.Value}"));
        }

        return string.Join(" ", columnDefinitionParts);
    }

    private static string GetEqualityClause(string propertyName, List<string> parameterNames)
    {
        return parameterNames.Count == 1 ?
            $"{propertyName} = {parameterNames[0]}" :
            $"{propertyName} IN ({string.Join(", ", parameterNames)})";
    }

    private static (SqliteCommand Command, List<string> ParameterNames) GetCommandWithParameterNames<TParameter>(
        string propertyName,
        IReadOnlyList<TParameter> parameters)
    {
        var command = new SqliteCommand();
        var parameterNames = new List<string>();

        for (var parameterIndex = 0; parameterIndex < parameters.Count; parameterIndex++)
        {
            var parameterName = GetParameterName(propertyName, parameterIndex);
            parameterNames.Add(parameterName);

            command.Parameters.AddWithValue(parameterName, parameters[parameterIndex]);
        }

        return (command, parameterNames);
    }

    private static (List<string> Columns, List<string> Parameters, List<object?> Values) GetQueryParts(
        IReadOnlyList<string> propertyNames,
        Dictionary<string, object?> record,
        int index)
    {
        var columns = new List<string>();
        var parameters = new List<string>();
        var values = new List<object?>();

        foreach (var propertyName in propertyNames)
        {
            if (record.TryGetValue(propertyName, out var value))
            {
                columns.Add(propertyName);
                parameters.Add(GetParameterName(propertyName, index));
                values.Add(value ?? DBNull.Value);
            }
        }

        return (columns, parameters, values);
    }

    private static string GetParameterName(string propertyName, int index)
    {
        return $"@{propertyName}{index}";
    }

    #endregion
}
