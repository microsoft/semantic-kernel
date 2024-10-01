// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;
using Microsoft.Data.Sqlite;
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel.Connectors.Sqlite;

/// <summary>
/// Contains helper methods to create queries for SQLite database.
/// </summary>
internal static class SqliteVectorStoreCollectionCommandBuilder
{
    public static SqliteCommand BuildTableCountCommand(
        SqliteConnection connection,
        string tableName)
    {
        const string SystemTable = "sqlite_master";
        const string ParameterName = "@tableName";

        var query = $"SELECT count(*) FROM {SystemTable} WHERE type='table' AND name={ParameterName};";

        using var command = new SqliteCommand(query, connection);

        command.Parameters.AddWithValue(ParameterName, tableName);

        return command;
    }

    [System.Diagnostics.CodeAnalysis.SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities", Justification = "Query does not contain user input.")]
    public static SqliteCommand BuildCreateTableCommand(
        SqliteConnection connection,
        string tableName,
        VectorStoreRecordKeyProperty keyProperty,
        List<VectorStoreRecordDataProperty> dataProperties,
        Dictionary<string, string> storagePropertyNames,
        bool ifNotExists)
    {
        var builder = new StringBuilder();
        var columns = new List<string>();

        builder.AppendLine($"CREATE TABLE {(ifNotExists ? "IF NOT EXISTS " : string.Empty)}{tableName} (");

        AddColumn(columns, keyProperty, storagePropertyNames, isPrimaryKey: true);

        foreach (var property in dataProperties)
        {
            AddColumn(columns, property, storagePropertyNames);
        }

        builder.AppendLine(string.Join(",\n", columns));
        builder.Append(");");

        var query = builder.ToString();

        return new SqliteCommand(query, connection);
    }

    [System.Diagnostics.CodeAnalysis.SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities", Justification = "Query does not contain user input.")]
    public static SqliteCommand BuildDropTableCommand(
        SqliteConnection connection,
        string tableName)
    {
        string query = $"DROP TABLE IF EXISTS [{tableName}];";

        return new SqliteCommand(query, connection);
    }

    #region private

    private static void AddColumn(
        List<string> columns,
        VectorStoreRecordProperty property,
        Dictionary<string, string> storagePropertyNames,
        bool isPrimaryKey = false)
    {
        const string PrimaryKeyIdentifier = "PRIMARY KEY";

        var primaryKeyPlaceholder = isPrimaryKey ? $" {PrimaryKeyIdentifier}" : string.Empty;

        columns.Add($"{storagePropertyNames[property.DataModelPropertyName]} {GetStoragePropertyType(property)}{primaryKeyPlaceholder}");
    }

    private static string GetStoragePropertyType(VectorStoreRecordProperty property)
    {
        return property.PropertyType switch
        {
            // Integer types
            Type t when t == typeof(int) || t == typeof(int?) => "INTEGER",
            Type t when t == typeof(long) || t == typeof(long?) => "INTEGER",
            Type t when t == typeof(ulong) || t == typeof(ulong?) => "INTEGER",
            Type t when t == typeof(short) || t == typeof(short?) => "INTEGER",
            Type t when t == typeof(ushort) || t == typeof(ushort?) => "INTEGER",

            // Floating-point types
            Type t when t == typeof(float) || t == typeof(float?) => "REAL",
            Type t when t == typeof(double) || t == typeof(double?) => "REAL",
            Type t when t == typeof(decimal) || t == typeof(decimal?) => "REAL",

            // String type
            Type t when t == typeof(string) => "TEXT",

            // Boolean types - SQLite doesn't have a boolean type, represent it as 0/1
            Type t when t == typeof(bool) || t == typeof(bool?) => "INTEGER",

            // Byte array (BLOB)
            Type t when t == typeof(byte[]) => "BLOB",

            // DateTime types - use ISO 8601 string for datetimes
            Type t when t == typeof(DateTime) || t == typeof(DateTime?) => "TEXT",

            // Default fallback for unknown types
            _ => throw new NotSupportedException($"Property {property.DataModelPropertyName} has type {property.PropertyType.FullName}, which is not supported by SQLite connector.")
        };
    }

    #endregion
}
