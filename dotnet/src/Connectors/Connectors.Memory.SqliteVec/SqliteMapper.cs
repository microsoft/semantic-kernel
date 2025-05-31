// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Data.Common;
using System.Diagnostics;
using System.Runtime.InteropServices;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.SqliteVec;

/// <summary>
/// Class for mapping between a dictionary and the consumer data model.
/// </summary>
/// <typeparam name="TRecord">The consumer data model to map to or from.</typeparam>
internal sealed class SqliteMapper<TRecord>(CollectionModel model)
{
    public TRecord MapFromStorageToDataModel(DbDataReader reader, bool includeVectors)
    {
        var record = model.CreateRecord<TRecord>()!;

        var keyProperty = model.KeyProperty;
        keyProperty.SetValueAsObject(
            record,
            GetPropertyValue(reader, keyProperty.StorageName, keyProperty.Type));

        foreach (var property in model.DataProperties)
        {
            property.SetValueAsObject(
                record,
                GetPropertyValue(reader, property.StorageName, property.Type));
        }

        if (includeVectors)
        {
            foreach (var property in model.VectorProperties)
            {
                int ordinal = reader.GetOrdinal(property.StorageName);

                if (reader.IsDBNull(ordinal))
                {
                    continue;
                }

                // SqliteVec provides the vector data as a byte[], which we need to convert to a float[].
                // In modern .NET, we allocate a float[] of the right size, reinterpret-cast it into byte[],
                // and then read the data into that via Stream.
                // In .NET Framework, which doesn't have Span APIs on Stream, we just create a copy (inefficient).
#if NET8_0_OR_GREATER
                using var stream = reader.GetStream(ordinal);

                var length = stream.Length;
                if (length % 4 != 0)
                {
                    throw new InvalidOperationException($"Retrieved value for vector property '{property.StorageName}' which is not a valid byte array length (expected multiple of 4, got {stream.Length}).");
                }

                var floats = new float[length / 4];
                var bytes = MemoryMarshal.Cast<float, byte>(floats);
                stream.ReadExactly(bytes);
#else
                var floats = MemoryMarshal.Cast<byte, float>((byte[])reader[ordinal]).ToArray();
#endif

                property.SetValueAsObject(
                    record,
                    (Nullable.GetUnderlyingType(property.Type) ?? property.Type) switch
                    {
                        var t when t == typeof(ReadOnlyMemory<float>) => new ReadOnlyMemory<float>(floats),
                        var t when t == typeof(Embedding<float>) => new Embedding<float>(floats),
                        var t when t == typeof(float[]) => floats,

                        _ => throw new UnreachableException()
                    });
            }
        }

        return record;
    }

    private static object? GetPropertyValue(DbDataReader reader, string propertyName, Type propertyType)
    {
        int ordinal = reader.GetOrdinal(propertyName);

        if (reader.IsDBNull(ordinal))
        {
            return null;
        }

        return (Nullable.GetUnderlyingType(propertyType) ?? propertyType) switch
        {
            Type t when t == typeof(int) => reader.GetInt32(ordinal),
            Type t when t == typeof(long) => reader.GetInt64(ordinal),
            Type t when t == typeof(short) => reader.GetInt16(ordinal),
            Type t when t == typeof(bool) => reader.GetBoolean(ordinal),
            Type t when t == typeof(float) => reader.GetFloat(ordinal),
            Type t when t == typeof(double) => reader.GetDouble(ordinal),
            Type t when t == typeof(string) => reader.GetString(ordinal),
            Type t when t == typeof(byte[]) => (byte[])reader[ordinal],
            Type t when t == typeof(ReadOnlyMemory<float>) => (byte[])reader[ordinal],
            Type t when t == typeof(Embedding<float>) => (byte[])reader[ordinal],
            Type t when t == typeof(float[]) => (byte[])reader[ordinal],

            _ => throw new NotSupportedException($"Unsupported type: {propertyType} for property: {propertyName}")
        };
    }
}
