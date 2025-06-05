// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Data.Common;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text;
using Microsoft.Data.Sqlite;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.SqliteVec;

/// <summary>
/// Command builder for queries in SQLite database.
/// </summary>
[SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities", Justification = "User input is passed using command parameters.")]
internal static class SqliteCommandBuilder
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
        bool ifNotExists)
    {
        var builder = new StringBuilder();

        builder.AppendLine($"CREATE VIRTUAL TABLE {(ifNotExists ? "IF NOT EXISTS " : string.Empty)}\"{tableName}\" USING vec0(");

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
        CollectionModel model,
        IEnumerable<object> records,
        Dictionary<VectorPropertyModel, IReadOnlyList<Embedding<float>>>? generatedEmbeddings,
        bool data,
        bool replaceIfExists = false)
    {
        var sql = new StringBuilder();
        var command = connection.CreateCommand();

        var recordIndex = 0;

        var properties = model.KeyProperties.Concat(data ? model.DataProperties : (IEnumerable<PropertyModel>)model.VectorProperties);

        foreach (var record in records)
        {
            var rowIdentifierParameterName = GetParameterName(rowIdentifier, recordIndex);

            sql.Append("INSERT");

            if (replaceIfExists)
            {
                sql.Append(" OR REPLACE");
            }

            sql.Append(" INTO \"").Append(tableName).Append("\" (");  // TODO: Sanitize

#pragma warning disable CA1851 // Possible multiple enumerations of 'IEnumerable' collection
            var propertyIndex = 0;
            foreach (var property in properties)
            {
                if (propertyIndex++ > 0)
                {
                    sql.Append(", ");
                }

                sql.Append('"').Append(property.StorageName).Append('"'); // TODO: Sanitize
            }

            sql.AppendLine(")");

            sql.Append("VALUES (");

            propertyIndex = 0;
            foreach (var property in properties)
            {
                var parameterName = GetParameterName(property.StorageName, recordIndex);

                if (propertyIndex++ > 0)
                {
                    sql.Append(", ");
                }

                sql.Append(parameterName);

                var value = property.GetValueAsObject(record);

                if (property is VectorPropertyModel vectorProperty)
                {
                    if (generatedEmbeddings?[vectorProperty] is IReadOnlyList<Embedding> ge)
                    {
                        value = ((Embedding<float>)ge[recordIndex]).Vector;
                    }

                    value = value switch
                    {
                        ReadOnlyMemory<float> m => SqlitePropertyMapping.MapVectorForStorageModel(m),
                        Embedding<float> e => SqlitePropertyMapping.MapVectorForStorageModel(e.Vector),
                        float[] a => SqlitePropertyMapping.MapVectorForStorageModel(a),
                        null => null,

                        _ => throw new InvalidOperationException($"Retrieved value for vector property '{property.StorageName}' which is not a ReadOnlyMemory<float> ('{value?.GetType().Name}').")
                    };
                }

                command.Parameters.Add(new SqliteParameter(parameterName, value ?? DBNull.Value));
            }
#pragma warning restore CA1851

            sql.AppendLine(")");

            sql
                .Append("RETURNING ")
                .AppendLine(rowIdentifier)
                .AppendLine(";");

            recordIndex++;
        }

        command.CommandText = sql.ToString();

        return command;
    }

    public static DbCommand BuildSelectDataCommand<TRecord>(
        SqliteConnection connection,
        string tableName,
        CollectionModel model,
        List<SqliteWhereCondition> conditions,
        FilteredRecordRetrievalOptions<TRecord>? filterOptions = null,
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

    public static DbCommand BuildSelectInnerJoinCommand<TRecord>(
        SqliteConnection connection,
        string vectorTableName,
        string dataTableName,
        string keyColumnName,
        CollectionModel model,
        IReadOnlyList<SqliteWhereCondition> conditions,
        bool includeDistance,
        FilteredRecordRetrievalOptions<TRecord>? filterOptions = null,
        string? extraWhereFilter = null,
        Dictionary<string, object>? extraParameters = null,
        int top = 0,
        int skip = 0)
    {
        const string SubqueryName = "subquery";

        var builder = new StringBuilder();

        var subqueryCommand = BuildSelectDataCommand(
                connection,
                dataTableName,
                model,
                [],
                filterOptions,
                extraWhereFilter,
                extraParameters,
                top,
                skip);

        var queryExtraFilter = $"\"{vectorTableName}\".\"{keyColumnName}\" IN (SELECT \"{keyColumnName}\" FROM {SubqueryName})";
        var (command, whereClause) = GetCommandWithWhereClause(connection, conditions, queryExtraFilter, []);

        foreach (var parameter in subqueryCommand.Parameters)
        {
            command.Parameters.Add(parameter);
        }

        builder.AppendLine($"WITH {SubqueryName} AS ({subqueryCommand.CommandText}) ");

        builder.Append("SELECT ");
        builder.AppendColumnNames(includeVectors: true, model.Properties, vectorTableName, dataTableName);
        if (includeDistance)
        {
            builder.AppendLine($", \"{vectorTableName}\".\"{DistancePropertyName}\"");
        }
        builder.AppendLine($"FROM \"{vectorTableName}\"");
        builder.AppendLine($"INNER JOIN \"{dataTableName}\" ON \"{vectorTableName}\".\"{keyColumnName}\" = \"{dataTableName}\".\"{keyColumnName}\"");
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

    private static StringBuilder AppendColumnNames(this StringBuilder builder, bool includeVectors, IReadOnlyList<PropertyModel> properties,
        string? escapedVectorTableName = null, string? escapedDataTableName = null)
    {
        foreach (var property in properties)
        {
            string? tableName = escapedDataTableName;
            if (property is VectorPropertyModel)
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

    private static StringBuilder AppendOrderBy<TRecord>(this StringBuilder builder, CollectionModel model,
        FilteredRecordRetrievalOptions<TRecord> options, string? tableName = null)
    {
        var orderBy = options.OrderBy?.Invoke(new()).Values;
        if (orderBy is { Count: > 0 })
        {
            builder.Append("ORDER BY ");

            foreach (var sortInfo in orderBy)
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

    private static string GetParameterName(string propertyName, int index)
        => $"@{propertyName}{index}";

    #endregion
}
