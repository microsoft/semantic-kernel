// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Data.Common;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text;
using Microsoft.Data.Sqlite;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.Sqlite;

/// <summary>
/// Command builder for queries in SQLite database.
/// </summary>
[SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities", Justification = "User input is passed using command parameters.")]
internal static class SqliteVectorStoreCollectionCommandBuilder
{
    internal const string DistancePropertyName = "distance";

    internal static string EscapeIdentifier(this string value) => value.Replace("'", "''").Replace("\"", "\"\"");

    public static DbCommand BuildTableCountCommand(SqliteConnection connection, string tableName)
    {
        Verify.NotNullOrWhiteSpace(tableName);

        const string SystemTable = "sqlite_master";
        const string ParameterName = "@tableName";

        var query = $"SELECT count(*) FROM {SystemTable} WHERE type='table' AND name={ParameterName};";

        var command = connection.CreateCommand();

        command.CommandText = query;

        command.Parameters.Add(new SqliteParameter(ParameterName, tableName));

        return command;
    }

    public static DbCommand BuildCreateTableCommand(SqliteConnection connection, string tableName, IReadOnlyList<SqliteColumn> columns, bool ifNotExists)
    {
        var builder = new StringBuilder();

        builder.AppendLine($"CREATE TABLE {(ifNotExists ? "IF NOT EXISTS " : string.Empty)}\"{tableName}\" (");

        builder.AppendLine(string.Join(",\n", columns.Select(column => GetColumnDefinition(column, quote: true))));
        builder.AppendLine(");");

        foreach (var column in columns)
        {
            if (column.HasIndex)
            {
                builder.AppendLine($"CREATE INDEX {(ifNotExists ? "IF NOT EXISTS " : string.Empty)}\"{tableName}_{column.Name}_index\" ON \"{tableName}\"(\"{column.Name}\");");
            }
        }

        var command = connection.CreateCommand();

        command.CommandText = builder.ToString();

        return command;
    }

    public static DbCommand BuildCreateVirtualTableCommand(
        SqliteConnection connection,
        string tableName,
        IReadOnlyList<SqliteColumn> columns,
        bool ifNotExists,
        string extensionName)
    {
        var builder = new StringBuilder();

        builder.AppendLine($"CREATE VIRTUAL TABLE {(ifNotExists ? "IF NOT EXISTS " : string.Empty)}\"{tableName}\" USING {extensionName}(");

        // The vector extension is currently uncapable of handling quoted identifiers.
        builder.AppendLine(string.Join(",\n", columns.Select(column => GetColumnDefinition(column, quote: false))));
        builder.Append(");");

        var command = connection.CreateCommand();

        command.CommandText = builder.ToString();

        return command;
    }

    public static DbCommand BuildDropTableCommand(SqliteConnection connection, string tableName)
    {
        string query = $"DROP TABLE IF EXISTS \"{tableName}\";";

        var command = connection.CreateCommand();

        command.CommandText = query;

        return command;
    }

    public static DbCommand BuildInsertCommand(
        SqliteConnection connection,
        string tableName,
        string rowIdentifier,
        IReadOnlyList<VectorStoreRecordPropertyModel> properties,
        IReadOnlyList<Dictionary<string, object?>> records,
        bool data,
        bool replaceIfExists = false)
    {
        var builder = new StringBuilder();
        var command = connection.CreateCommand();

        var replacePlaceholder = replaceIfExists ? " OR REPLACE" : string.Empty;

        for (var recordIndex = 0; recordIndex < records.Count; recordIndex++)
        {
            var rowIdentifierParameterName = GetParameterName(rowIdentifier, recordIndex);

            var (columns, parameters, values) = GetQueryParts(
                properties,
                records[recordIndex],
                recordIndex,
                data);

            builder.AppendLine($"INSERT{replacePlaceholder} INTO \"{tableName}\" ({string.Join(", ", columns)})");
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

    public static DbCommand BuildSelectDataCommand<TRecord>(
        SqliteConnection connection,
        string tableName,
        VectorStoreRecordModel model,
        List<SqliteWhereCondition> conditions,
        GetFilteredRecordOptions<TRecord>? filterOptions = null,
        string? extraWhereFilter = null,
        Dictionary<string, object>? extraParameters = null,
        int top = 0,
        int skip = 0)
    {
        var builder = new StringBuilder();

        var (command, whereClause) = GetCommandWithWhereClause(connection, conditions, extraWhereFilter, extraParameters);

        builder.Append("SELECT ");
        builder.AppendColumnNames(includeVectors: false, model.Properties);
        builder.AppendLine($"FROM \"{tableName}\"");
        builder.AppendWhereClause(whereClause);

        if (filterOptions is not null)
        {
            builder.AppendOrderBy(model, filterOptions);
        }

        builder.AppendLimits(top, skip);

        command.CommandText = builder.ToString();

        return command;
    }

    public static DbCommand BuildSelectLeftJoinCommand<TRecord>(
        SqliteConnection connection,
        string vectorTableName,
        string dataTableName,
        string joinColumnName,
        VectorStoreRecordModel model,
        IReadOnlyList<SqliteWhereCondition> conditions,
        bool includeDistance,
        GetFilteredRecordOptions<TRecord>? filterOptions = null,
        string? extraWhereFilter = null,
        Dictionary<string, object>? extraParameters = null,
        int top = 0,
        int skip = 0)
    {
        var builder = new StringBuilder();

        var (command, whereClause) = GetCommandWithWhereClause(connection, conditions, extraWhereFilter, extraParameters);

        builder.Append("SELECT ");
        builder.AppendColumnNames(includeVectors: true, model.Properties, vectorTableName, dataTableName);
        if (includeDistance)
        {
            builder.AppendLine($", \"{vectorTableName}\".\"{DistancePropertyName}\"");
        }
        builder.AppendLine($"FROM \"{vectorTableName}\"");
        builder.AppendLine($"LEFT JOIN \"{dataTableName}\" ON \"{vectorTableName}\".\"{joinColumnName}\" = \"{dataTableName}\".\"{joinColumnName}\"");
        builder.AppendWhereClause(whereClause);

        if (filterOptions is not null)
        {
            builder.AppendOrderBy(model, filterOptions, dataTableName);
        }
        else if (includeDistance)
        {
            builder.AppendLine($"ORDER BY \"{vectorTableName}\".\"{DistancePropertyName}\"");
        }

        builder.AppendLimits(top, skip);

        command.CommandText = builder.ToString();

        return command;
    }

    public static DbCommand BuildDeleteCommand(
        SqliteConnection connection,
        string tableName,
        IReadOnlyList<SqliteWhereCondition> conditions)
    {
        var builder = new StringBuilder();

        var (command, whereClause) = GetCommandWithWhereClause(connection, conditions);

        builder.AppendLine($"DELETE FROM \"{tableName}\"");
        builder.AppendWhereClause(whereClause);

        command.CommandText = builder.ToString();

        return command;
    }

    #region private

    private static StringBuilder AppendColumnNames(this StringBuilder builder, bool includeVectors, IReadOnlyList<VectorStoreRecordPropertyModel> properties,
        string? escapedVectorTableName = null, string? escapedDataTableName = null)
    {
        foreach (var property in properties)
        {
            string? tableName = escapedDataTableName;
            if (property is VectorStoreRecordVectorPropertyModel)
            {
                if (!includeVectors)
                {
                    continue;
                }
                tableName = escapedVectorTableName;
            }

            if (tableName is not null)
            {
                builder.AppendFormat("\"{0}\".\"{1}\",", tableName, property.StorageName);
            }
            else
            {
                builder.AppendFormat("\"{0}\",", property.StorageName);
            }
        }

        builder.Length--; // Remove the trailing comma
        builder.AppendLine();
        return builder;
    }

    private static StringBuilder AppendOrderBy<TRecord>(this StringBuilder builder, VectorStoreRecordModel model,
        GetFilteredRecordOptions<TRecord> options, string? tableName = null)
    {
        if (options.OrderBy.Values.Count > 0)
        {
            builder.Append("ORDER BY ");

            foreach (var sortInfo in options.OrderBy.Values)
            {
                var storageName = model.GetDataOrKeyProperty(sortInfo.PropertySelector).StorageName;

                if (tableName is not null)
                {
                    builder.AppendFormat("\"{0}\".", tableName);
                }

                builder.AppendFormat("\"{0}\" {1},", storageName, sortInfo.Ascending ? "ASC" : "DESC");
            }

            builder.Length--; // remove the last comma
            builder.AppendLine();
        }

        return builder;
    }

    private static StringBuilder AppendLimits(this StringBuilder builder, int top, int skip)
    {
        if (top > 0)
        {
            builder.AppendFormat("LIMIT {0}", top).AppendLine();
        }

        if (skip > 0)
        {
            builder.AppendFormat("OFFSET {0}", skip).AppendLine();
        }

        return builder;
    }

    private static StringBuilder AppendWhereClause(this StringBuilder builder, string? whereClause)
    {
        if (!string.IsNullOrWhiteSpace(whereClause))
        {
            builder.AppendLine($"WHERE {whereClause}");
        }

        return builder;
    }

    private static string GetColumnDefinition(SqliteColumn column, bool quote)
    {
        const string PrimaryKeyIdentifier = "PRIMARY KEY";

        List<string> columnDefinitionParts = [quote ? $"\"{column.Name}\"" : column.Name, column.Type];

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

    private static (DbCommand Command, string WhereClause) GetCommandWithWhereClause(
        SqliteConnection connection,
        IReadOnlyList<SqliteWhereCondition> conditions,
        string? extraWhereFilter = null,
        Dictionary<string, object>? extraParameters = null)
    {
        const string WhereClauseOperator = " AND ";

        var command = connection.CreateCommand();
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
            foreach (var p in extraParameters!)
            {
                command.Parameters.Add(new SqliteParameter(p.Key, p.Value));
            }
        }

        return (command, whereClause);
    }

    private static (List<string> Columns, List<string> ParameterNames, List<object?> ParameterValues) GetQueryParts(
        IReadOnlyList<VectorStoreRecordPropertyModel> properties,
        Dictionary<string, object?> record,
        int index,
        bool data)
    {
        var columns = new List<string>();
        var parameterNames = new List<string>();
        var parameterValues = new List<object?>();

        foreach (var property in properties)
        {
            bool include = property is VectorStoreRecordKeyPropertyModel // The Key column is included in both Vector and Data tables.
                || (data == property is VectorStoreRecordDataPropertyModel); // The Data column is included only in the Data table.

            string propertyName = property.StorageName;
            if (include && record.TryGetValue(propertyName, out var value))
            {
                columns.Add($"\"{propertyName}\"");
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
