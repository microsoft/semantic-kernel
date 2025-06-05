// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Data.Common;
using System.Diagnostics;
using System.Runtime.InteropServices;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.SqliteVec;

/// <summary>
/// Contains helper methods with property mapping for SQLite.
/// </summary>
internal static class SqlitePropertyMapping
{
    public static byte[] MapVectorForStorageModel(ReadOnlyMemory<float> memory)
    {
        ReadOnlySpan<float> floatSpan = memory.Span;
        byte[] byteArray = new byte[floatSpan.Length * sizeof(float)];
        MemoryMarshal.AsBytes(floatSpan).CopyTo(byteArray);

        return byteArray;
    }

    public static List<SqliteColumn> GetColumns(IReadOnlyList<PropertyModel> properties, bool data)
    {
        const string DistanceMetricConfigurationName = "distance_metric";

        var columns = new List<SqliteColumn>();

        foreach (var property in properties)
        {
            var isPrimary = false;

            string propertyType;
            Dictionary<string, object>? configuration = null;

            if (property is VectorPropertyModel vectorProperty)
            {
                if (data)
                {
                    continue;
                }

                propertyType = GetStorageVectorPropertyType(vectorProperty);
                configuration = new()
                {
                    [DistanceMetricConfigurationName] = GetDistanceMetric(vectorProperty)
                };
            }
            else if (property is DataPropertyModel dataProperty)
            {
                if (!data)
                {
                    continue;
                }

                propertyType = GetStorageDataPropertyType(property);
            }
            else
            {
                // The Key column in included in both Vector and Data tables.
                Debug.Assert(property is KeyPropertyModel, "property is VectorStoreRecordKeyPropertyModel");

                propertyType = GetStorageDataPropertyType(property);
                isPrimary = true;
            }

            var column = new SqliteColumn(property.StorageName, propertyType, isPrimary)
            {
                Configuration = configuration,
                HasIndex = property is DataPropertyModel { IsIndexed: true }
            };

            columns.Add(column);
        }

        return columns;
    }

    public static TPropertyType? GetPropertyValue<TPropertyType>(DbDataReader reader, string propertyName)
    {
        int propertyIndex = reader.GetOrdinal(propertyName);

        // TODO: Check this
        return reader.IsDBNull(propertyIndex)
            ? default
            : reader.GetFieldValue<TPropertyType>(propertyIndex);
    }

    #region private

    private static string GetStorageDataPropertyType(PropertyModel property)
        => property.Type switch
        {
            // Integer types
            Type t when t == typeof(int) || t == typeof(int?) => "INTEGER",
            Type t when t == typeof(long) || t == typeof(long?) => "INTEGER",
            Type t when t == typeof(short) || t == typeof(short?) => "INTEGER",

            // Floating-point types
            Type t when t == typeof(float) || t == typeof(float?) => "REAL",
            Type t when t == typeof(double) || t == typeof(double?) => "REAL",

            // String type
            Type t when t == typeof(string) => "TEXT",

            // Boolean types - SQLite doesn't have a boolean type, represent it as 0/1
            Type t when t == typeof(bool) || t == typeof(bool?) => "INTEGER",

            // Byte array (BLOB)
            Type t when t == typeof(byte[]) => "BLOB",

            // Default fallback for unknown types
            _ => throw new NotSupportedException($"Property '{property.ModelName}' has type '{property.Type.Name}', which is not supported by SQLite connector.")
        };

    private static string GetDistanceMetric(VectorPropertyModel vectorProperty)
        => vectorProperty.DistanceFunction switch
        {
            DistanceFunction.CosineDistance or null => "cosine",
            DistanceFunction.ManhattanDistance => "l1",
            DistanceFunction.EuclideanDistance => "l2",
            _ => throw new NotSupportedException($"Distance function '{vectorProperty.DistanceFunction}' for {nameof(VectorStoreVectorProperty)} '{vectorProperty.ModelName}' is not supported by the SQLite connector.")
        };

    private static string GetStorageVectorPropertyType(VectorPropertyModel vectorProperty)
        => $"FLOAT[{vectorProperty.Dimensions}]";

    #endregion
}
