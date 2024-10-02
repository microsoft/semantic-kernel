// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text;
using Microsoft.Data.Sqlite;
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel.Connectors.Sqlite;

/// <summary>
/// Command builder for queries in SQLite database.
/// </summary>
internal class SqliteVectorStoreCollectionCommandBuilder
{
    /// <summary>The name of the table.</summary>
    private readonly string _tableName;

    /// <summary>The name of the virtual table.</summary>
    private readonly string _virtualTableName;

    /// <summary><see cref="SqliteConnection"/> that will be used to manage the data in SQLite.</summary>
    private readonly SqliteConnection _connection;

    /// <summary>The key property of the storage model.</summary>
    private readonly VectorStoreRecordKeyProperty _keyProperty;

    /// <summary>Collection of record data properties.</summary>
    private readonly List<VectorStoreRecordDataProperty> _dataProperties;

    /// <summary>Collection of record vector properties.</summary>
    private readonly List<VectorStoreRecordVectorProperty> _vectorProperties;

    /// <summary>A dictionary that maps from a property name to the storage name.</summary>
    private readonly Dictionary<string, string> _storagePropertyNames;

    /// <summary>
    /// Initializes a new instance of the <see cref="SqliteVectorStoreCollectionCommandBuilder"/> class.
    /// </summary>
    /// <param name="collectionName"><see cref="SqliteConnection"/> that will be used to manage the data in SQLite.</param>
    /// <param name="connection"><see cref="SqliteConnection"/> that will be used to manage the data in SQLite.</param>
    /// <param name="keyProperty">The key property of the storage model.</param>
    /// <param name="dataProperties">Collection of record data properties.</param>
    /// <param name="vectorProperties">Collection of record vector properties.</param>
    /// <param name="storagePropertyNames">A dictionary that maps from a property name to the storage name.</param>
    public SqliteVectorStoreCollectionCommandBuilder(
        string collectionName,
        SqliteConnection connection,
        VectorStoreRecordKeyProperty keyProperty,
        List<VectorStoreRecordDataProperty> dataProperties,
        List<VectorStoreRecordVectorProperty> vectorProperties,
        Dictionary<string, string> storagePropertyNames)
    {
        Verify.NotNullOrWhiteSpace(collectionName);
        Verify.NotNull(connection);
        Verify.NotNull(keyProperty);
        Verify.NotNull(dataProperties);
        Verify.NotNull(vectorProperties);
        Verify.NotNull(storagePropertyNames);

        this._tableName = collectionName;

        // Use virtual table name with prefix to avoid collisions with regular table name.
        this._virtualTableName = $"vec_{this._tableName}";

        this._connection = connection;
        this._keyProperty = keyProperty;
        this._dataProperties = dataProperties;
        this._vectorProperties = vectorProperties;
        this._storagePropertyNames = storagePropertyNames;
    }

    public SqliteCommand BuildTableCountCommand()
    {
        const string SystemTable = "sqlite_master";
        const string ParameterName = "@tableName";

        var query = $"SELECT count(*) FROM {SystemTable} WHERE type='table' AND name={ParameterName};";

        using var command = new SqliteCommand(query, this._connection);

        command.Parameters.AddWithValue(ParameterName, this._tableName);

        return command;
    }

    [SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities", Justification = "Query does not contain user input.")]
    public SqliteCommand BuildCreateTableCommand(bool ifNotExists)
    {
        var builder = new StringBuilder();
        var columns = new List<string>();

        builder.AppendLine($"CREATE TABLE {(ifNotExists ? "IF NOT EXISTS " : string.Empty)}{this._tableName} (");

        this.AddColumn(columns, this._keyProperty);

        foreach (var property in this._dataProperties)
        {
            this.AddColumn(columns, property);
        }

        builder.AppendLine(string.Join(",\n", columns));
        builder.Append(");");

        var query = builder.ToString();

        return new SqliteCommand(query, this._connection);
    }

    [SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities", Justification = "Query does not contain user input.")]
    public SqliteCommand BuildCreateVirtualTableCommand(bool ifNotExists)
    {
        var builder = new StringBuilder();
        var columns = new List<string>();

        builder.AppendLine($"CREATE VIRTUAL TABLE {(ifNotExists ? "IF NOT EXISTS " : string.Empty)}{this._virtualTableName} USING {SqliteConstants.VectorSearchExtensionName}(");

        this.AddColumn(columns, this._keyProperty);

        foreach (var property in this._vectorProperties)
        {
            this.AddColumn(columns, property);
        }

        builder.AppendLine(string.Join(",\n", columns));
        builder.Append(");");

        var query = builder.ToString();

        return new SqliteCommand(query, this._connection);
    }

    public SqliteCommand BuildDropTableCommand()
    {
        return this.BuildDropTableCommand(this._tableName);
    }

    public SqliteCommand BuildDropVirtualTableCommand()
    {
        return this.BuildDropTableCommand(this._virtualTableName);
    }

    public SqliteCommand BuildInsertOrReplaceDataCommand(Dictionary<string, object?> record)
    {
        List<VectorStoreRecordProperty> properties = [this._keyProperty, .. this._dataProperties];
        return this.BuildInsertOrReplaceCommand(this._tableName, properties, record);
    }

    public SqliteCommand BuildInsertOrReplaceVectorCommand(Dictionary<string, object?> record)
    {
        List<VectorStoreRecordProperty> properties = [.. this._vectorProperties];
        return this.BuildInsertOrReplaceCommand(this._virtualTableName, properties, record);
    }

    #region private

    [SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities", Justification = "Query does not contain user input.")]
    private SqliteCommand BuildDropTableCommand(string tableName)
    {
        string query = $"DROP TABLE [{tableName}];";

        return new SqliteCommand(query, this._connection);
    }

    [SuppressMessage("Security", "CA2100:Review SQL queries for security vulnerabilities", Justification = "User input is passed using command parameters.")]
    private SqliteCommand BuildInsertOrReplaceCommand(
        string tableName,
        List<VectorStoreRecordProperty> properties,
        Dictionary<string, object?> record)
    {
        var builder = new StringBuilder();

        var columns = new List<string>();
        var valueParameters = new List<string>();
        var values = new List<object?>();

        foreach (var property in properties)
        {
            var storagePropertyName = this._storagePropertyNames[property.DataModelPropertyName];

            if (record.TryGetValue(storagePropertyName, out var value))
            {
                columns.Add(storagePropertyName);
                valueParameters.Add($"@{storagePropertyName}");
                values.Add(value ?? DBNull.Value);
            }
        }

        builder.AppendLine($"INSERT OR REPLACE INTO ${this._tableName} ({string.Join(", ", columns)})");
        builder.AppendLine($"VALUES ({string.Join(", ", valueParameters)});");

        var query = builder.ToString();

        var command = new SqliteCommand(query, this._connection);

        for (var i = 0; i < valueParameters.Count; i++)
        {
            command.Parameters.AddWithValue(valueParameters[i], values[i]);
        }

        return command;
    }

    private void AddColumn(List<string> columns, VectorStoreRecordProperty property)
    {
        const string PrimaryKeyIdentifier = "PRIMARY KEY";

        var primaryKeyPlaceholder = property is VectorStoreRecordKeyProperty ? $" {PrimaryKeyIdentifier}" : string.Empty;
        var propertyType = property is VectorStoreRecordVectorProperty vectorProperty ?
            GetVectorStoragePropertyType(vectorProperty) :
            GetStoragePropertyType(property);

        columns.Add($"{this._storagePropertyNames[property.DataModelPropertyName]} {propertyType}{primaryKeyPlaceholder}");
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

    private static string GetVectorStoragePropertyType(VectorStoreRecordVectorProperty vectorProperty)
    {
        var propertyType = vectorProperty.PropertyType;

        if (!SqliteConstants.SupportedVectorTypes.Contains(propertyType))
        {
            throw new NotSupportedException($"Property {vectorProperty.DataModelPropertyName} has type {propertyType.FullName}, which is not supported by SQLite connector.");
        }

        var storagePropertyType = $"FLOAT[{vectorProperty.Dimensions}]";

        return storagePropertyType;
    }

    #endregion
}
