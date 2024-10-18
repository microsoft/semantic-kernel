// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using Npgsql;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

internal static class PostgresVectorStoreRecordPropertyMapping
{
    internal static float[] GetOrCreateArray(ReadOnlyMemory<float> memory) =>
        MemoryMarshal.TryGetArray(memory, out ArraySegment<float> array) &&
        array.Count == array.Array!.Length ?
            array.Array :
            memory.ToArray();

    public static TPropertyType? GetPropertyValue<TPropertyType>(NpgsqlDataReader reader, string propertyName)
    {
        int propertyIndex = reader.GetOrdinal(propertyName);

        if (reader.IsDBNull(propertyIndex))
        {
            return default;
        }

        return reader.GetFieldValue<TPropertyType>(propertyIndex);
    }

    public static object? GetPropertyValue(NpgsqlDataReader reader, string propertyName, Type propertyType)
    {
        int propertyIndex = reader.GetOrdinal(propertyName);

        if (reader.IsDBNull(propertyIndex))
        {
            return null;
        }

        // Check if the type is a List<T>
        if (propertyType.IsGenericType && propertyType.GetGenericTypeDefinition() == typeof(List<>))
        {
            var elementType = propertyType.GetGenericArguments()[0];
            var list = (IEnumerable)reader.GetValue(propertyIndex);
            // Convert list to the correct element type
            return ConvertList(list, elementType);
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
            Type t when t == typeof(string) => reader.GetString(propertyIndex),
            _ => reader.GetValue(propertyIndex)
        };
    }

    // Helper method to convert lists
    private static object ConvertList(IEnumerable list, Type elementType)
    {
        var listType = typeof(List<>).MakeGenericType(elementType);
        var convertedList = (IList)Activator.CreateInstance(listType)!;

        foreach (var item in list)
        {
            convertedList.Add(Convert.ChangeType(item, elementType));
        }

        return convertedList;
    }
}