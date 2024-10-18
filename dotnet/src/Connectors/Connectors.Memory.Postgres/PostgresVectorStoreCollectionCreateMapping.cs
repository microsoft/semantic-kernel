// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

/// <summary>
/// Generates the PostgreSQL vector type name based on the dimensions of the vector property.
/// /// Provides methods to generate SQL statements for creating tables in /// a PostgreSQL database
/// for storing vector data.
/// </summary>
public static class PostgresVectorStoreCollectionCreateMapping
{
    /// <summary>
    /// Generates a SQL CREATE TABLE statement.
    /// </summary>
    /// <param name="schema">The schema name.</param>
    /// <param name="tableName">The table name.</param>
    /// <param name="KeyProperty">The key property.</param>
    /// <param name="DataProperties">The list of data properties.</param>
    /// <param name="VectorProperties">The list of vector properties.</param>
    /// <returns>The generated SQL CREATE TABLE statement.</returns>
    /// <exception cref="ArgumentException">Thrown when the table name is null or whitespace.</exception>
    public static string GenerateCreateTableStatement(string schema, string tableName, VectorStoreRecordKeyProperty KeyProperty, IEnumerable<VectorStoreRecordDataProperty> DataProperties, IEnumerable<VectorStoreRecordVectorProperty> VectorProperties)
    {
        if (string.IsNullOrWhiteSpace(tableName))
        {
            throw new ArgumentException("Table name cannot be null or whitespace", nameof(tableName));
        }

        var keyName = KeyProperty.StoragePropertyName ?? KeyProperty.DataModelPropertyName;

        StringBuilder createTableCommand = new();
        createTableCommand.AppendLine($"CREATE TABLE {schema}.{tableName} (");

        // Add the key column
        createTableCommand.AppendLine($"    {keyName} {GetPostgresTypeName(KeyProperty.PropertyType)},");

        // Add the data columns
        foreach (var dataProperty in DataProperties)
        {
            string columnName = dataProperty.StoragePropertyName ?? dataProperty.DataModelPropertyName;
            createTableCommand.AppendLine($"    {columnName} {GetPostgresTypeName(dataProperty.PropertyType)},");
        }

        // Add the vector columns
        foreach (var vectorProperty in VectorProperties)
        {
            string columnName = vectorProperty.StoragePropertyName ?? vectorProperty.DataModelPropertyName;
            createTableCommand.AppendLine($"    {columnName} {GetPgVectorTypeName(vectorProperty)},");
        }

        createTableCommand.AppendLine($"    PRIMARY KEY ({keyName})");

        createTableCommand.AppendLine(");");

        return createTableCommand.ToString();
    }

    /// <summary>
    /// Maps a .NET type to a PostgreSQL type name.
    /// </summary>
    /// <param name="propertyType">The .NET type.</param>
    /// <returns>The PostgreSQL type name.</returns>
    private static string GetPostgresTypeName(Type propertyType)
    {
        var pgType = propertyType switch
        {
            Type t when t == typeof(int) => "INTEGER",
            Type t when t == typeof(string) => "TEXT",
            Type t when t == typeof(bool) => "BOOLEAN",
            Type t when t == typeof(DateTime) => "TIMESTAMP",
            Type t when t == typeof(double) => "DOUBLE PRECISION",
            Type t when t == typeof(decimal) => "NUMERIC",
            Type t when t == typeof(float) => "REAL",
            Type t when t == typeof(byte[]) => "BYTEA",
            Type t when t == typeof(Guid) => "UUID",
            Type t when t == typeof(short) => "SMALLINT",
            Type t when t == typeof(long) => "BIGINT",
            _ => null
        };

        if (pgType != null) { return pgType; }

        // Handle arrays (PostgreSQL supports array types for most types)
        if (propertyType.IsArray)
        {
            Type elementType = propertyType.GetElementType() ?? throw new ArgumentException("Array type must have an element type.");
            return GetPostgresTypeName(elementType) + "[]";
        }

        // Handle nullable types (e.g. Nullable<int>)
        if (Nullable.GetUnderlyingType(propertyType) != null)
        {
            Type underlyingType = Nullable.GetUnderlyingType(propertyType) ?? throw new ArgumentException("Nullable type must have an underlying type.");
            return GetPostgresTypeName(underlyingType);
        }

        throw new NotSupportedException($"Type {propertyType.Name} is not supported by this store.");
    }

    /// <summary>
    /// Gets the PostgreSQL vector type name based on the dimensions of the vector property.
    /// </summary>
    /// <param name="vectorProperty">The vector property.</param>
    /// <returns>The PostgreSQL vector type name.</returns>
    private static string GetPgVectorTypeName(VectorStoreRecordVectorProperty vectorProperty)
    {
        if (vectorProperty.Dimensions <= 0)
        {
            throw new ArgumentException("Vector property must have a positive number of dimensions.");
        }

        return $"VECTOR({vectorProperty.Dimensions})";
    }
}