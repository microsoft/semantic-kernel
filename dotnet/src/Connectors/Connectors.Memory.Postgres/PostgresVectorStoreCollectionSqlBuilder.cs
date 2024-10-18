// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Microsoft.Extensions.VectorData;
using Npgsql;
using NpgsqlTypes;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

/// <summary>
/// Provides methods to build SQL commands for managing vector store collections in PostgreSQL.
/// </summary>
public class PostgresVectorStoreCollectionSqlBuilder : IPostgresVectorStoreCollectionSqlBuilder
{
    /// <inheritdoc />
    public PostgresSqlCommandInfo BuildDoesTableExistCommand(string schema, string tableName)
    {
        return new PostgresSqlCommandInfo(
            commandText: $@"
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = $1
                    AND table_type = 'BASE TABLE'
                    AND table_name = '{tableName}'",
            parameters: [new NpgsqlParameter() { Value = schema }]
        );
    }

    /// <inheritdoc />
    public PostgresSqlCommandInfo BuildGetTablesCommand(string schema)
    {
        return new PostgresSqlCommandInfo(
            commandText: @"
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = $1
                    AND table_type = 'BASE TABLE'",
            parameters: [new NpgsqlParameter() { Value = schema }]
        );
    }

    /// <inheritdoc />
    public PostgresSqlCommandInfo BuildCreateTableCommand(string schema, string tableName, VectorStoreRecordDefinition recordDefinition, bool ifNotExists = true)
    {
        if (string.IsNullOrWhiteSpace(tableName))
        {
            throw new ArgumentException("Table name cannot be null or whitespace", nameof(tableName));
        }

        VectorStoreRecordKeyProperty? keyProperty = default;
        List<VectorStoreRecordDataProperty> dataProperties = new();
        List<VectorStoreRecordVectorProperty> vectorProperties = new();

        foreach (var property in recordDefinition.Properties)
        {
            if (property is VectorStoreRecordKeyProperty keyProp)
            {
                if (keyProperty != null)
                {
                    throw new ArgumentException("Record definition cannot have more than one key property.");
                }
                keyProperty = keyProp;
            }
            else if (property is VectorStoreRecordDataProperty dataProp)
            {
                dataProperties.Add(dataProp);
            }
            else if (property is VectorStoreRecordVectorProperty vectorProp)
            {
                vectorProperties.Add(vectorProp);
            }
            else
            {
                throw new NotSupportedException($"Property type {property.GetType().Name} is not supported by this store.");
            }
        }

        if (keyProperty == null)
        {
            throw new ArgumentException("Record definition must have a key property.");
        }

        var keyName = keyProperty.StoragePropertyName ?? keyProperty.DataModelPropertyName;

        StringBuilder createTableCommand = new();
        createTableCommand.AppendLine($"CREATE TABLE {(ifNotExists ? "IF NOT EXISTS " : "")}{schema}.\"{tableName}\" (");

        // Add the key column
        var keyPgTypeInfo = PostgresVectorStoreRecordPropertyMapping.GetPostgresTypeName(keyProperty.PropertyType);
        createTableCommand.AppendLine($"    \"{keyName}\" {keyPgTypeInfo.PgType} {(keyPgTypeInfo.IsNullable ? "" : "NOT NULL")},");

        // Add the data columns
        foreach (var dataProperty in dataProperties)
        {
            string columnName = dataProperty.StoragePropertyName ?? dataProperty.DataModelPropertyName;
            var dataPgTypeInfo = PostgresVectorStoreRecordPropertyMapping.GetPostgresTypeName(dataProperty.PropertyType);
            createTableCommand.AppendLine($"    \"{columnName}\" {dataPgTypeInfo.PgType} {(dataPgTypeInfo.IsNullable ? "" : "NOT NULL")},");
        }

        // Add the vector columns
        foreach (var vectorProperty in vectorProperties)
        {
            string columnName = vectorProperty.StoragePropertyName ?? vectorProperty.DataModelPropertyName;
            var vectorPgTypeInfo = PostgresVectorStoreRecordPropertyMapping.GetPgVectorTypeName(vectorProperty);
            createTableCommand.AppendLine($"    \"{columnName}\" {vectorPgTypeInfo.PgType} {(vectorPgTypeInfo.IsNullable ? "" : "NOT NULL")},");
        }

        createTableCommand.AppendLine($"    PRIMARY KEY (\"{keyName}\")");

        createTableCommand.AppendLine(");");

        return new PostgresSqlCommandInfo(commandText: createTableCommand.ToString());
    }

    /// <inheritdoc />
    public PostgresSqlCommandInfo BuildDropTableCommand(string schema, string tableName)
    {
        return new PostgresSqlCommandInfo(
            commandText: $@"DROP TABLE IF EXISTS {schema}.""{tableName}"""
        );
    }

    /// <inheritdoc/>
    public PostgresSqlCommandInfo BuildUpsertCommand(string schema, string tableName, string keyColumn, Dictionary<string, object?> row)
    {
        var columns = row.Keys.ToList();
        var columnNames = string.Join(", ", columns.Select(k => $"\"{k}\""));
        var valuesParams = string.Join(", ", columns.Select((k, i) => $"${i + 1}"));
        var columnsWithIndex = columns.Select((k, i) => (col: k, idx: i));
        var updateColumnsWithParams = string.Join(", ", columnsWithIndex.Where(c => c.col != keyColumn).Select(c => $"\"{c.col}\"=${c.idx + 1}"));
        var commandText = $@"
                INSERT INTO {schema}.""{tableName}"" ({columnNames})
                VALUES({valuesParams})
                ON CONFLICT (""{keyColumn}"")
                DO UPDATE SET {updateColumnsWithParams};";

        var parameters = row.ToDictionary(kvp => $"@{kvp.Key}", kvp => kvp.Value);

        return new PostgresSqlCommandInfo(commandText)
        {
            Parameters = columns.Select(c => new NpgsqlParameter() { Value = row[c] ?? DBNull.Value }).ToList()
        };
    }

    /// <inheritdoc />
    public PostgresSqlCommandInfo BuildUpsertBatchCommand(string schema, string tableName, string keyColumn, List<Dictionary<string, object?>> rows)
    {
        if (rows == null || rows.Count == 0)
        {
            throw new ArgumentException("Rows cannot be null or empty", nameof(rows));
        }

        var firstRow = rows[0];
        var columns = firstRow.Keys.ToList();

        // Generate column names and parameter placeholders
        var columnNames = string.Join(", ", columns.Select(c => $"\"{c}\""));
        var valuePlaceholders = string.Join(", ", columns.Select((c, i) => $"${i + 1}"));
        var valuesRows = string.Join(", ", rows.Select((row, rowIndex) => $"({string.Join(", ", columns.Select((c, colIndex) => $"${rowIndex * columns.Count + colIndex + 1}"))})"));

        // Generate the update set clause
        var updateSetClause = string.Join(", ", columns.Where(c => c != keyColumn).Select(c => $"\"{c}\" = EXCLUDED.\"{c}\""));

        // Generate the SQL command
        var commandText = $@"
            INSERT INTO {schema}.""{tableName}"" ({columnNames})
            VALUES {valuesRows}
        ON CONFLICT(""{keyColumn}"")
            DO UPDATE SET {updateSetClause}; ";

        // Generate the parameters
        var parameters = new List<NpgsqlParameter>();
        for (int rowIndex = 0; rowIndex < rows.Count; rowIndex++)
        {
            var row = rows[rowIndex];
            foreach (var column in columns)
            {
                parameters.Add(new NpgsqlParameter()
                {
                    Value = row[column] ?? DBNull.Value
                });
            }
        }

        return new PostgresSqlCommandInfo(commandText, parameters);
    }

    /// <inheritdoc />
    public PostgresSqlCommandInfo BuildGetCommand<TKey>(string schema, string tableName, VectorStoreRecordDefinition recordDefinition, TKey key, bool includeVectors = false)
        where TKey : notnull
    {
        List<string> queryColumns = new();
        string? keyColumn = null;

        foreach (var property in recordDefinition.Properties)
        {
            if (property is VectorStoreRecordKeyProperty keyProperty)
            {
                if (keyColumn != null)
                {
                    throw new ArgumentException("Record definition cannot have more than one key property.");
                }
                keyColumn = keyProperty.StoragePropertyName ?? keyProperty.DataModelPropertyName;
                queryColumns.Add($"\"{keyColumn}\"");
            }
            else if (property is VectorStoreRecordDataProperty dataProperty)
            {
                string columnName = dataProperty.StoragePropertyName ?? dataProperty.DataModelPropertyName;
                queryColumns.Add($"\"{columnName}\"");
            }
            else if (property is VectorStoreRecordVectorProperty vectorProperty && includeVectors)
            {
                string columnName = vectorProperty.StoragePropertyName ?? vectorProperty.DataModelPropertyName;
                queryColumns.Add($"\"{columnName}\"");
            }
        }

        Verify.NotNull(keyColumn, "Record definition must have a key property.");

        var queryColumnList = string.Join(", ", queryColumns);

        return new PostgresSqlCommandInfo(
            commandText: $@"
                SELECT {queryColumnList}
                FROM {schema}.""{tableName}""
                WHERE ""{keyColumn}"" = ${1};",
            parameters: [new NpgsqlParameter() { Value = key }]
        );
    }

    /// <inheritdoc />
    public PostgresSqlCommandInfo BuildGetBatchCommand<TKey>(string schema, string tableName, VectorStoreRecordDefinition recordDefinition, List<TKey> keys, bool includeVectors = false)
        where TKey : notnull
    {
        NpgsqlDbType? keyType = PostgresVectorStoreRecordPropertyMapping.GetNpgsqlDbType(typeof(TKey)) ?? throw new ArgumentException($"Unsupported key type {typeof(TKey).Name}");

        if (keys == null || keys.Count == 0)
        {
            throw new ArgumentException("Keys cannot be null or empty", nameof(keys));
        }

        var keyProperty = recordDefinition.Properties.OfType<VectorStoreRecordKeyProperty>().FirstOrDefault() ?? throw new ArgumentException("Record definition must contain a key property", nameof(recordDefinition));
        var keyColumn = keyProperty.StoragePropertyName ?? keyProperty.DataModelPropertyName;

        // Generate the column names
        var columns = recordDefinition.Properties
            .Where(p => includeVectors || p is not VectorStoreRecordVectorProperty)
            .Select(p => p.StoragePropertyName ?? p.DataModelPropertyName)
            .ToList();

        var columnNames = string.Join(", ", columns.Select(c => $"\"{c}\""));
        var keyParams = string.Join(", ", keys.Select((k, i) => $"${i + 1}"));

        // Generate the SQL command
        var commandText = $@"
            SELECT {columnNames}
            FROM {schema}.""{tableName}""
            WHERE ""{keyColumn}"" = ANY($1);";

        return new PostgresSqlCommandInfo(commandText)
        {
            Parameters = [new NpgsqlParameter() { Value = keys.ToArray(), NpgsqlDbType = NpgsqlDbType.Array | keyType.Value }]
        };
    }

    /// <inheritdoc />
    public PostgresSqlCommandInfo BuildDeleteCommand<TKey>(string schema, string tableName, string keyColumn, TKey key)
    {
        return new PostgresSqlCommandInfo(
            commandText: $@"
                DELETE FROM {schema}.""{tableName}""
                WHERE ""{keyColumn}"" = ${1};",
            parameters: [new NpgsqlParameter() { Value = key }]
        );
    }

    /// <inheritdoc />
    public PostgresSqlCommandInfo BuildDeleteBatchCommand<TKey>(string schema, string tableName, string keyColumn, List<TKey> keys)
    {
        NpgsqlDbType? keyType = PostgresVectorStoreRecordPropertyMapping.GetNpgsqlDbType(typeof(TKey)) ?? throw new ArgumentException($"Unsupported key type {typeof(TKey).Name}");
        if (keys == null || keys.Count == 0)
        {
            throw new ArgumentException("Keys cannot be null or empty", nameof(keys));
        }

        for (int i = 0; i < keys.Count; i++)
        {
            if (keys[i] == null)
            {
                throw new ArgumentException("Keys cannot contain null values", nameof(keys));
            }
        }

        var commandText = $@"
            DELETE FROM {schema}.""{tableName}""
            WHERE ""{keyColumn}"" = ANY($1);";

        return new PostgresSqlCommandInfo(commandText)
        {
            Parameters = [new NpgsqlParameter() { Value = keys, NpgsqlDbType = NpgsqlDbType.Array | keyType.Value }]
        };
    }
}