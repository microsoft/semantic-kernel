// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Runtime.InteropServices;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Npgsql;
using NpgsqlTypes;
using Pgvector;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

internal static class PostgresVectorStoreRecordPropertyMapping
{
    public static Vector? MapVectorForStorageModel(object? vector)
        => vector switch
        {
            ReadOnlyMemory<float> floatMemory
                => new Pgvector.Vector(
                    MemoryMarshal.TryGetArray(floatMemory, out ArraySegment<float> segment) &&
                    segment.Count == segment.Array!.Length ? segment.Array : floatMemory.ToArray()),

            // TODO: Implement support for Half, binary, sparse embeddings (#11083)

            null => null,

            var value => throw new NotSupportedException($"Mapping for type '{value.GetType().Name}' to a vector is not supported.")
        };

    public static object? GetPropertyValue(NpgsqlDataReader reader, string propertyName, Type propertyType)
    {
        int propertyIndex = reader.GetOrdinal(propertyName);

        if (reader.IsDBNull(propertyIndex))
        {
            return null;
        }

        // Check if the type implements IEnumerable<T>
        if (propertyType.IsGenericType && propertyType.GetInterfaces().Any(i => i.IsGenericType && i.GetGenericTypeDefinition() == typeof(IEnumerable<>)))
        {
            var enumerable = (IEnumerable)reader.GetValue(propertyIndex);
            return VectorStoreRecordMapping.CreateEnumerable(enumerable.Cast<object>(), propertyType);
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
            Type t when t == typeof(DateTimeOffset) || t == typeof(DateTimeOffset?) => reader.GetFieldValue<DateTimeOffset>(propertyIndex),
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
            Type t when t == typeof(DateTimeOffset) || t == typeof(DateTimeOffset?) => NpgsqlDbType.TimestampTz,
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
            Type t when t == typeof(DateTimeOffset) => ("TIMESTAMPTZ", false),
            Type t when t == typeof(Guid) => ("UUID", false),
            _ => (null, false)
        };

        if (pgType != null)
        {
            return (pgType, isNullable);
        }

        // Handle enumerables
        if (VectorStoreRecordPropertyVerification.IsSupportedEnumerableType(propertyType))
        {
            Type elementType = propertyType.IsArray ? propertyType.GetElementType()! : propertyType.GetGenericArguments()[0];
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
    public static (string PgType, bool IsNullable) GetPgVectorTypeName(VectorStoreRecordVectorPropertyModel vectorProperty)
    {
        return ($"VECTOR({vectorProperty.Dimensions})", Nullable.GetUnderlyingType(vectorProperty.EmbeddingType) != null);
    }

    public static NpgsqlParameter GetNpgsqlParameter(object? value)
    {
        if (value == null)
        {
            return new NpgsqlParameter() { Value = DBNull.Value };
        }

        // If it's an IEnumerable<T>, use reflection to determine if it needs to be converted to a list
        if (value is IEnumerable enumerable && !(value is string))
        {
            Type propertyType = value.GetType();
            if (propertyType.IsGenericType && propertyType.GetGenericTypeDefinition() == typeof(List<>))
            {
                // If it's already a List<T>, return it directly
                return new NpgsqlParameter() { Value = value };
            }

            return new NpgsqlParameter() { Value = ConvertToListIfNecessary(enumerable) };
        }

        // Return the value directly if it's not IEnumerable
        return new NpgsqlParameter() { Value = value };
    }

    /// <summary>
    /// Returns information about indexes to create, validating that the dimensions of the vector are supported.
    /// </summary>
    /// <param name="properties">The properties of the vector store record.</param>
    /// <returns>A list of tuples containing the column name, index kind, and distance function for each property.</returns>
    /// <remarks>
    /// The default index kind is "Flat", which prevents the creation of an index.
    /// </remarks>
    public static List<(string column, string kind, string function, bool isVector)> GetIndexInfo(IReadOnlyList<VectorStoreRecordPropertyModel> properties)
    {
        var vectorIndexesToCreate = new List<(string column, string kind, string function, bool isVector)>();
        foreach (var property in properties)
        {
            switch (property)
            {
                case VectorStoreRecordKeyPropertyModel:
                    // There is no need to create a separate index for the key property.
                    break;

                case VectorStoreRecordVectorPropertyModel vectorProperty:
                    var indexKind = vectorProperty.IndexKind ?? PostgresConstants.DefaultIndexKind;
                    var distanceFunction = vectorProperty.DistanceFunction ?? PostgresConstants.DefaultDistanceFunction;

                    // Index kind of "Flat" to prevent the creation of an index. This is the default behavior.
                    // Otherwise, the index will be created with the specified index kind and distance function, if supported.
                    if (indexKind != IndexKind.Flat)
                    {
                        // Ensure the dimensionality of the vector is supported for indexing.
                        if (PostgresConstants.IndexMaxDimensions.TryGetValue(indexKind, out int maxDimensions) && vectorProperty.Dimensions > maxDimensions)
                        {
                            throw new NotSupportedException(
                                $"The provided vector property {vectorProperty.ModelName} has {vectorProperty.Dimensions} dimensions, " +
                                $"which is not supported by the {indexKind} index. The maximum number of dimensions supported by the {indexKind} index " +
                                $"is {maxDimensions}. Please reduce the number of dimensions or use a different index."
                            );
                        }

                        vectorIndexesToCreate.Add((vectorProperty.StorageName, indexKind, distanceFunction, isVector: true));
                    }

                    break;

                case VectorStoreRecordDataPropertyModel dataProperty:
                    if (dataProperty.IsIndexed)
                    {
                        vectorIndexesToCreate.Add((dataProperty.StorageName, "", "", isVector: false));
                    }
                    break;

                default:
                    throw new UnreachableException();
            }
        }

        return vectorIndexesToCreate;
    }

    // Helper method to convert an IEnumerable to a List if necessary
    private static object ConvertToListIfNecessary(IEnumerable enumerable)
    {
        // Get an enumerator to manually iterate over the collection
        var enumerator = enumerable.GetEnumerator();

        // Check if the collection is empty by attempting to move to the first element
        if (!enumerator.MoveNext())
        {
            return enumerable; // Return the original enumerable if it's empty
        }

        // Determine the type of the first element
        var firstItem = enumerator.Current;
        var itemType = firstItem?.GetType() ?? typeof(object);

        // Create a strongly-typed List<T> based on the type of the first element
        var typedList = Activator.CreateInstance(typeof(List<>).MakeGenericType(itemType)) as IList;
        typedList!.Add(firstItem); // Add the first element to the typed list

        // Continue iterating through the rest of the enumerable and add items to the list
        while (enumerator.MoveNext())
        {
            typedList.Add(enumerator.Current);
        }

        return typedList;
    }
}
