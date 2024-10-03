// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using Microsoft.Data.Sqlite;
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel.Connectors.Sqlite;

/// <summary>
/// Contains helper methods with property mapping for SQLite.
/// </summary>
internal static class SqliteVectorStoreRecordPropertyMapping
{
    public static List<SqliteColumn> GetColumns(
        List<VectorStoreRecordProperty> properties,
        IReadOnlyDictionary<string, string> storagePropertyNames)
    {
        var columns = new List<SqliteColumn>();

        foreach (var property in properties)
        {
            var isPrimary = property is VectorStoreRecordKeyProperty;
            var propertyName = storagePropertyNames[property.DataModelPropertyName];
            var propertyType = property is VectorStoreRecordVectorProperty vectorProperty ?
                GetStorageVectorPropertyType(vectorProperty) :
                GetStorageDataPropertyType(property);

            columns.Add(new(propertyName, propertyType, isPrimary));
        }

        return columns;
    }

    public static object? GetPropertyValue(SqliteDataReader reader, string propertyName, Type propertyType)
    {
        int propertyIndex = reader.GetOrdinal(propertyName);

        if (reader.IsDBNull(propertyIndex))
        {
            return null;
        }

        return propertyType switch
        {
            Type t when t == typeof(int) || t == typeof(int?) => reader.GetInt32(propertyIndex),
            Type t when t == typeof(long) || t == typeof(long?) => reader.GetInt64(propertyIndex),
            Type t when t == typeof(ulong) || t == typeof(ulong?) => (ulong)reader.GetInt64(propertyIndex),
            Type t when t == typeof(short) || t == typeof(short?) => reader.GetInt16(propertyIndex),
            Type t when t == typeof(ushort) || t == typeof(ushort?) => (ushort)reader.GetInt16(propertyIndex),
            Type t when t == typeof(bool) || t == typeof(bool?) => reader.GetBoolean(propertyIndex),
            Type t when t == typeof(float) || t == typeof(float?) => reader.GetFloat(propertyIndex),
            Type t when t == typeof(double) || t == typeof(double?) => reader.GetDouble(propertyIndex),
            Type t when t == typeof(decimal) || t == typeof(decimal?) => reader.GetDecimal(propertyIndex),
            Type t when t == typeof(DateTime) || t == typeof(DateTime?) => reader.GetDateTime(propertyIndex),
            Type t when t == typeof(string) => reader.GetString(propertyIndex),
            Type t when t == typeof(byte[]) => (byte[])reader[propertyName],
            Type t when t == typeof(ReadOnlyMemory<float>) || t == typeof(ReadOnlyMemory<float>?) => GetReadOnlyMemory((byte[])reader[propertyName]),
            _ => throw new NotSupportedException($"Unsupported type: {propertyType} for property: {propertyName}")
        };
    }

    #region private

    private static ReadOnlyMemory<float> GetReadOnlyMemory(byte[] byteArray)
    {
        var array = MemoryMarshal.Cast<byte, float>(byteArray).ToArray();
        return new ReadOnlyMemory<float>(array);
    }

    private static string GetStorageDataPropertyType(VectorStoreRecordProperty property)
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

    private static string GetStorageVectorPropertyType(VectorStoreRecordVectorProperty vectorProperty)
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
