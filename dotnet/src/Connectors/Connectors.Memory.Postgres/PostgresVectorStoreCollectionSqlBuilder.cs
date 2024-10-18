// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Microsoft.Extensions.VectorData;
using Npgsql;

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
        var keyPgTypeInfo = GetPostgresTypeName(keyProperty.PropertyType);
        createTableCommand.AppendLine($"    \"{keyName}\" {keyPgTypeInfo.PgType} {(keyPgTypeInfo.IsNullable ? "" : "NOT NULL")},");

        // Add the data columns
        foreach (var dataProperty in dataProperties)
        {
            string columnName = dataProperty.StoragePropertyName ?? dataProperty.DataModelPropertyName;
            var dataPgTypeInfo = GetPostgresTypeName(dataProperty.PropertyType);
            createTableCommand.AppendLine($"    \"{columnName}\" {dataPgTypeInfo.PgType} {(dataPgTypeInfo.IsNullable ? "" : "NOT NULL")},");
        }

        // Add the vector columns
        foreach (var vectorProperty in vectorProperties)
        {
            string columnName = vectorProperty.StoragePropertyName ?? vectorProperty.DataModelPropertyName;
            var vectorPgTypeInfo = GetPgVectorTypeName(vectorProperty);
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
    public PostgresSqlCommandInfo BuildUpsertCommand(string schema, string tableName, Dictionary<string, object?> row, string keyColumn)
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

    /// <summary>
    /// Maps a .NET type to a PostgreSQL type name.
    /// </summary>
    /// <param name="propertyType">The .NET type.</param>
    /// <returns>Tuple of the the PostgreSQL type name and whether it can be NULL</returns>
    private static (string PgType, bool IsNullable) GetPostgresTypeName(Type propertyType)
    {
        var (pgType, isNullable) = propertyType switch
        {
            Type t when t == typeof(int) => ("INTEGER", false),
            Type t when t == typeof(string) => ("TEXT", true),
            Type t when t == typeof(bool) => ("BOOLEAN", false),
            Type t when t == typeof(DateTime) => ("TIMESTAMP", false),
            Type t when t == typeof(double) => ("DOUBLE PRECISION", false),
            Type t when t == typeof(decimal) => ("NUMERIC", false),
            Type t when t == typeof(float) => ("REAL", false),
            Type t when t == typeof(byte[]) => ("BYTEA", true),
            Type t when t == typeof(Guid) => ("UUID", false),
            Type t when t == typeof(short) => ("SMALLINT", false),
            Type t when t == typeof(long) => ("BIGINT", false),
            _ => (null, false)
        };

        if (pgType != null)
        {
            return (pgType, isNullable);
        }

        // Handle lists and arrays (PostgreSQL supports array types for most types)
        if (propertyType.IsArray)
        {
            Type elementType = propertyType.GetElementType() ?? throw new ArgumentException("Array type must have an element type.");
            var underlyingPgType = GetPostgresTypeName(elementType);
            return (underlyingPgType.PgType + "[]", true);
        }
        else if (propertyType.IsGenericType && propertyType.GetGenericTypeDefinition() == typeof(List<>))
        {
            Type elementType = propertyType.GetGenericArguments()[0];
            var underlyingPgType = GetPostgresTypeName(elementType);
            return (underlyingPgType.PgType + "[]", true);
        }

        // Handle nullable types (e.g. Nullable<int>)
        if (Nullable.GetUnderlyingType(propertyType) != null)
        {
            Type underlyingType = Nullable.GetUnderlyingType(propertyType) ?? throw new ArgumentException("Nullable type must have an underlying type.");
            var underlyingPgType = GetPostgresTypeName(underlyingType);
            return (underlyingPgType.PgType, true);
        }

        throw new NotSupportedException($"Type {propertyType.Name} is not supported by this store.");
    }

    /// <summary>
    /// Gets the PostgreSQL vector type name based on the dimensions of the vector property.
    /// </summary>
    /// <param name="vectorProperty">The vector property.</param>
    /// <returns>The PostgreSQL vector type name.</returns>
    private static (string PgType, bool IsNullable) GetPgVectorTypeName(VectorStoreRecordVectorProperty vectorProperty)
    {
        if (vectorProperty.Dimensions <= 0)
        {
            throw new ArgumentException("Vector property must have a positive number of dimensions.");
        }

        return ($"VECTOR({vectorProperty.Dimensions})", Nullable.GetUnderlyingType(vectorProperty.PropertyType) != null);
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
}