﻿// Copyright (c) Microsoft. All rights reserved.

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
    public static string MapVector<TVector>(TVector vector)
    {
        if (vector is ReadOnlyMemory<float> memoryFloat)
        {
            return $"[{string.Join(", ", memoryFloat.ToArray())}]";
        }

        throw new NotSupportedException($"Mapping for type {typeof(TVector).FullName} is not supported.");
    }

    public static List<SqliteColumn> GetColumns(
        List<VectorStoreRecordProperty> properties,
        IReadOnlyDictionary<string, string> storagePropertyNames)
    {
        const string DistanceMetricConfigurationName = "distance_metric";

        var columns = new List<SqliteColumn>();

        foreach (var property in properties)
        {
            var isPrimary = property is VectorStoreRecordKeyProperty;
            var propertyName = storagePropertyNames[property.DataModelPropertyName];

            string propertyType;
            Dictionary<string, object>? configuration = null;

            if (property is VectorStoreRecordVectorProperty vectorProperty)
            {
                propertyType = GetStorageVectorPropertyType(vectorProperty);
                configuration = new()
                {
                    [DistanceMetricConfigurationName] = GetDistanceMetric(vectorProperty.DistanceFunction, vectorProperty.DataModelPropertyName)
                };
            }
            else
            {
                propertyType = GetStorageDataPropertyType(property);
            }

            var column = new SqliteColumn(propertyName, propertyType, isPrimary, configuration);

            columns.Add(column);
        }

        return columns;
    }

    public static TPropertyType? GetPropertyValue<TPropertyType>(SqliteDataReader reader, string propertyName)
    {
        int propertyIndex = reader.GetOrdinal(propertyName);

        if (reader.IsDBNull(propertyIndex))
        {
            return default;
        }

        return reader.GetFieldValue<TPropertyType>(propertyIndex);
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

    private static string GetDistanceMetric(string? distanceFunction, string vectorPropertyName)
    {
        const string Cosine = "cosine";
        const string L1 = "l1";
        const string L2 = "l2";

        if (string.IsNullOrWhiteSpace(distanceFunction))
        {
            return Cosine;
        }

        return distanceFunction switch
        {
            DistanceFunction.CosineDistance => Cosine,
            DistanceFunction.ManhattanDistance => L1,
            DistanceFunction.EuclideanDistance => L2,
            _ => throw new NotSupportedException($"Distance function '{distanceFunction}' for {nameof(VectorStoreRecordVectorProperty)} '{vectorPropertyName}' is not supported by the SQLite connector.")
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