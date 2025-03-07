// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Data.Common;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text;
using Microsoft.Data.Sqlite;

namespace Microsoft.SemanticKernel.Connectors.Sqlite;

/// <summary>
/// Command builder for queries in SQLite database.
/// </summary>
[SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities", Justification = "User input is passed using command parameters.")]
internal sealed class SqliteVectorStoreCollectionCommandBuilder
{
    /// <summary><see cref="DbConnection"/> that will be used to manage the data in SQLite.</summary>
    private readonly DbConnection _connection;

    /// <summary>
    /// Initializes a new instance of the <see cref="SqliteVectorStoreCollectionCommandBuilder"/> class.
    /// </summary>
    /// <param name="connection"><see cref="DbConnection"/> that will be used to manage the data in SQLite.</param>
    public SqliteVectorStoreCollectionCommandBuilder(DbConnection connection)
    {
        Verify.NotNull(connection);

        this._connection = connection;
    }

    public DbCommand BuildTableCountCommand(string tableName)
    {
        Verify.NotNullOrWhiteSpace(tableName);

        const string SystemTable = "sqlite_master";
        const string ParameterName = "@tableName";

        var query = $"SELECT count(*) FROM {SystemTable} WHERE type='table' AND name={ParameterName};";

        var command = this._connection.CreateCommand();

        command.CommandText = query;

        command.Parameters.Add(new SqliteParameter(ParameterName, tableName));

        return command;
    }

    public DbCommand BuildCreateTableCommand(string tableName, IReadOnlyList<SqliteColumn> columns, bool ifNotExists)
    {
        var builder = new StringBuilder();

        builder.AppendLine($"CREATE TABLE {(ifNotExists ? "IF NOT EXISTS " : string.Empty)}{tableName} (");

        builder.AppendLine(string.Join(",\n", columns.Select(GetColumnDefinition)));
        builder.Append(");");

        var command = this._connection.CreateCommand();

        command.CommandText = builder.ToString();

        return command;
    }

    public DbCommand BuildCreateVirtualTableCommand(
        string tableName,
        IReadOnlyList<SqliteColumn> columns,
        bool ifNotExists,
        string extensionName)
    {
        var builder = new StringBuilder();

        builder.AppendLine($"CREATE VIRTUAL TABLE {(ifNotExists ? "IF NOT EXISTS " : string.Empty)}{tableName} USING {extensionName}(");

        builder.AppendLine(string.Join(",\n", columns.Select(GetColumnDefinition)));
        builder.Append(");");

        var command = this._connection.CreateCommand();

        command.CommandText = builder.ToString();

        return command;
    }

    public DbCommand BuildDropTableCommand(string tableName)
    {
        string query = $"DROP TABLE [{tableName}];";

        var command = this._connection.CreateCommand();

        command.CommandText = query;

        return command;
    }

    public DbCommand BuildInsertCommand(
        string tableName,
        string rowIdentifier,
        IReadOnlyList<string> columnNames,
        IReadOnlyList<Dictionary<string, object?>> records,
        bool replaceIfExists = false)
    {
        var builder = new StringBuilder();
        var command = this._connection.CreateCommand();

        var replacePlaceholder = replaceIfExists ? " OR REPLACE" : string.Empty;

        for (var recordIndex = 0; recordIndex < records.Count; recordIndex++)
        {
            var rowIdentifierParameterName = GetParameterName(rowIdentifier, recordIndex);

            var (columns, parameters, values) = GetQueryParts(
                columnNames,
                records[recordIndex],
                recordIndex);

            builder.AppendLine($"INSERT{replacePlaceholder} INTO {tableName} ({string.Join(", ", columns)})");
            builder.AppendLine($"VALUES ({string.Join(", ", parameters)})");
            builder.AppendLine($"RETURNING {rowIdentifier};");

            for (var i = 0; i < parameters.Count; i++)
            {
                command.Parameters.Add(new SqliteParameter(parameters[i], values[i]));
            }
        }

        command.CommandText = builder.ToString();

        return command;
    }

    public DbCommand BuildSelectCommand(
        string tableName,
        IReadOnlyList<string> columnNames,
        List<SqliteWhereCondition> conditions,
        string? orderByPropertyName = null)
    {
        var builder = new StringBuilder();

        var (command, whereClause) = this.GetCommandWithWhereClause(conditions);

        builder.AppendLine($"SELECT {string.Join(", ", columnNames)}");
        builder.AppendLine($"FROM {tableName}");

        AppendWhereClauseIfExists(builder, whereClause);
        AppendOrderByIfExists(builder, orderByPropertyName);

        command.CommandText = builder.ToString();

        return command;
    }

    public DbCommand BuildSelectLeftJoinCommand(
        string leftTable,
        string rightTable,
        string joinColumnName,
        IReadOnlyList<string> leftTablePropertyNames,
        IReadOnlyList<string> rightTablePropertyNames,
        List<SqliteWhereCondition> conditions,
        string? extraWhereFilter = null,
        Dictionary<string, object>? extraParameters = null,
        string? orderByPropertyName = null)
    {
        var builder = new StringBuilder();

        List<string> propertyNames =
        [
            .. leftTablePropertyNames.Select(property => $"{leftTable}.{property}"),
            .. rightTablePropertyNames.Select(property => $"{rightTable}.{property}"),
        ];

        var (command, whereClause) = this.GetCommandWithWhereClause(conditions, extraWhereFilter, extraParameters);

        builder.AppendLine($"SELECT {string.Join(", ", propertyNames)}");
        builder.AppendLine($"FROM {leftTable} ");
        builder.AppendLine($"LEFT JOIN {rightTable} ON {leftTable}.{joinColumnName} = {rightTable}.{joinColumnName}");

        AppendWhereClauseIfExists(builder, whereClause);
        AppendOrderByIfExists(builder, orderByPropertyName);

        command.CommandText = builder.ToString();

        return command;
    }

    public DbCommand BuildDeleteCommand(
        string tableName,
        List<SqliteWhereCondition> conditions)
    {
        var builder = new StringBuilder();

        var (command, whereClause) = this.GetCommandWithWhereClause(conditions);

        builder.AppendLine($"DELETE FROM [{tableName}]");

        AppendWhereClauseIfExists(builder, whereClause);

        command.CommandText = builder.ToString();

        return command;
    }

    #region private

    private static void AppendWhereClauseIfExists(StringBuilder builder, string? whereClause)
    {
        if (!string.IsNullOrWhiteSpace(whereClause))
        {
            builder.AppendLine($"WHERE {whereClause}");
        }
    }

    private static void AppendOrderByIfExists(StringBuilder builder, string? propertyName)
    {
        if (!string.IsNullOrWhiteSpace(propertyName))
        {
            builder.AppendLine($"ORDER BY {propertyName}");
        }
    }

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

    private (DbCommand Command, string WhereClause) GetCommandWithWhereClause(
        List<SqliteWhereCondition> conditions,
        string? extraWhereFilter = null,
        Dictionary<string, object>? extraParameters = null)
    {
        const string WhereClauseOperator = " AND ";

        var command = this._connection.CreateCommand();
        var whereClauseParts = new List<string>();

        foreach (var condition in conditions)
        {
            var parameterNames = new List<string>();

            for (var parameterIndex = 0; parameterIndex < condition.Values.Count; parameterIndex++)
            {
                var parameterName = GetParameterName(condition.Operand, parameterIndex);

                parameterNames.Add(parameterName);

                command.Parameters.Add(new SqliteParameter(parameterName, condition.Values[parameterIndex]));
            }

            whereClauseParts.Add(condition.BuildQuery(parameterNames));
        }

        var whereClause = string.Join(WhereClauseOperator, whereClauseParts);

        if (extraWhereFilter is not null)
        {
            if (conditions.Count > 0)
            {
                whereClause += " AND ";
            }

            whereClause += extraWhereFilter;

            Debug.Assert(extraParameters is not null, "extraParameters must be provided when extraWhereFilter is provided.");
            foreach (var p in extraParameters)
            {
                command.Parameters.Add(new SqliteParameter(p.Key, p.Value));
            }
        }

        return (command, whereClause);
    }

    private static (List<string> Columns, List<string> ParameterNames, List<object?> ParameterValues) GetQueryParts(
        IReadOnlyList<string> propertyNames,
        Dictionary<string, object?> record,
        int index)
    {
        var columns = new List<string>();
        var parameterNames = new List<string>();
        var parameterValues = new List<object?>();

        foreach (var propertyName in propertyNames)
        {
            if (record.TryGetValue(propertyName, out var value))
            {
                columns.Add(propertyName);
                parameterNames.Add(GetParameterName(propertyName, index));
                parameterValues.Add(value ?? DBNull.Value);
            }
        }

        return (columns, parameterNames, parameterValues);
    }

    private static string GetParameterName(string propertyName, int index)
    {
        return $"@{propertyName}{index}";
    }

    #endregion
}
