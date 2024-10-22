// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using Microsoft.Extensions.VectorData;
using Npgsql;
using NpgsqlTypes;
using Pgvector;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

internal static class PostgresVectorStoreRecordPropertyMapping
{
    internal static float[] GetOrCreateArray(ReadOnlyMemory<float> memory) =>
        MemoryMarshal.TryGetArray(memory, out ArraySegment<float> array) &&
        array.Count == array.Array!.Length ?
            array.Array :
            memory.ToArray();

    public static Vector? MapVectorForStorageModel<TVector>(TVector vector)
    {
        if (vector == null)
        {
            return null;
        }

        if (vector is ReadOnlyMemory<float> floatMemory)
        {
            var vecArray = MemoryMarshal.TryGetArray(floatMemory, out ArraySegment<float> array) &&
                array.Count == array.Array!.Length ?
                        array.Array :
                        floatMemory.ToArray();
            return new Vector(vecArray);
        }

        throw new NotSupportedException($"Mapping for type {typeof(TVector).FullName} to a vector is not supported.");
    }

    public static ReadOnlyMemory<float>? MapVectorForDataModel(object? vector)
    {
        var pgVector = vector is Vector pgv ? pgv : null;
        if (pgVector == null) { return null; }
        var vecArray = pgVector.ToArray();
        return vecArray != null && vecArray.Length != 0 ? (ReadOnlyMemory<float>)vecArray : null;
    }

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
            Type t when t == typeof(bool) || t == typeof(bool?) => reader.GetBoolean(propertyIndex),
            Type t when t == typeof(short) || t == typeof(short?) => reader.GetInt16(propertyIndex),
            Type t when t == typeof(int) || t == typeof(int?) => reader.GetInt32(propertyIndex),
            Type t when t == typeof(long) || t == typeof(long?) => reader.GetInt64(propertyIndex),
            Type t when t == typeof(float) || t == typeof(float?) => reader.GetFloat(propertyIndex),
            Type t when t == typeof(double) || t == typeof(double?) => reader.GetDouble(propertyIndex),
            Type t when t == typeof(decimal) || t == typeof(decimal?) => reader.GetDecimal(propertyIndex),
            Type t when t == typeof(string) => reader.GetString(propertyIndex),
            Type t when t == typeof(byte[]) => reader.GetFieldValue<byte[]>(propertyIndex),
            Type t when t == typeof(DateTime) || t == typeof(DateTime?) => reader.GetDateTime(propertyIndex),
            Type t when t == typeof(Guid) => reader.GetFieldValue<Guid>(propertyIndex),
            _ => reader.GetValue(propertyIndex)
        };
    }

    public static NpgsqlDbType? GetNpgsqlDbType(Type propertyType) =>
        propertyType switch
        {
            Type t when t == typeof(bool) || t == typeof(bool?) => NpgsqlDbType.Boolean,
            Type t when t == typeof(short) || t == typeof(short?) => NpgsqlDbType.Smallint,
            Type t when t == typeof(int) || t == typeof(int?) => NpgsqlDbType.Integer,
            Type t when t == typeof(long) || t == typeof(long?) => NpgsqlDbType.Bigint,
            Type t when t == typeof(float) || t == typeof(float?) => NpgsqlDbType.Real,
            Type t when t == typeof(double) || t == typeof(double?) => NpgsqlDbType.Double,
            Type t when t == typeof(decimal) || t == typeof(decimal?) => NpgsqlDbType.Numeric,
            Type t when t == typeof(string) => NpgsqlDbType.Text,
            Type t when t == typeof(byte[]) => NpgsqlDbType.Bytea,
            Type t when t == typeof(DateTime) || t == typeof(DateTime?) => NpgsqlDbType.Timestamp,
            Type t when t == typeof(Guid) => NpgsqlDbType.Uuid,
            _ => null
        };

    /// <summary>
    /// Maps a .NET type to a PostgreSQL type name.
    /// </summary>
    /// <param name="propertyType">The .NET type.</param>
    /// <returns>Tuple of the the PostgreSQL type name and whether it can be NULL</returns>
    public static (string PgType, bool IsNullable) GetPostgresTypeName(Type propertyType)
    {
        var (pgType, isNullable) = propertyType switch
        {
            Type t when t == typeof(bool) => ("BOOLEAN", false),
            Type t when t == typeof(short) => ("SMALLINT", false),
            Type t when t == typeof(int) => ("INTEGER", false),
            Type t when t == typeof(long) => ("BIGINT", false),
            Type t when t == typeof(float) => ("REAL", false),
            Type t when t == typeof(double) => ("DOUBLE PRECISION", false),
            Type t when t == typeof(decimal) => ("NUMERIC", false),
            Type t when t == typeof(string) => ("TEXT", true),
            Type t when t == typeof(byte[]) => ("BYTEA", true),
            Type t when t == typeof(DateTime) => ("TIMESTAMP", false),
            Type t when t == typeof(Guid) => ("UUID", false),
            _ => (null, false)
        };

        if (pgType != null)
        {
            return (pgType, isNullable);
        }

        // Handle lists
        if (propertyType.IsGenericType && propertyType.GetGenericTypeDefinition() == typeof(List<>))
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
    public static (string PgType, bool IsNullable) GetPgVectorTypeName(VectorStoreRecordVectorProperty vectorProperty)
    {
        if (vectorProperty.Dimensions <= 0)
        {
            throw new ArgumentException("Vector property must have a positive number of dimensions.");
        }

        return ($"VECTOR({vectorProperty.Dimensions})", Nullable.GetUnderlyingType(vectorProperty.PropertyType) != null);
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
