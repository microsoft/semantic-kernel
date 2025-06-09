// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using Npgsql;
using NpgsqlTypes;
using Pgvector;

namespace Microsoft.SemanticKernel.Connectors.PgVector;

internal static class PostgresPropertyMapping
{
    public static object? MapVectorForStorageModel(object? vector)
        => vector switch
        {
            ReadOnlyMemory<float> m => new Pgvector.Vector(m),
            Embedding<float> e => new Pgvector.Vector(e.Vector),
            float[] a => new Pgvector.Vector(a),

#if NET8_0_OR_GREATER
            ReadOnlyMemory<Half> m => new Pgvector.HalfVector(m),
            Embedding<Half> e => new Pgvector.HalfVector(e.Vector),
            Half[] a => new Pgvector.HalfVector(a),
#endif

            BitArray bitArray => bitArray,
            SparseVector sparseVector => sparseVector,

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

        // Npgsql returns array values as a .NET array - that's what GetValue() returns below.
        // If the .NET property is a List<T>, we need an explicit GetFieldValue<List<T>>() call instead.
        if (propertyType.IsGenericType && propertyType.GetGenericTypeDefinition() == typeof(List<>))
        {
            return propertyType switch
            {
                Type t when t == typeof(List<bool>) => reader.GetFieldValue<List<bool>>(propertyIndex),
                Type t when t == typeof(List<short>) => reader.GetFieldValue<List<short>>(propertyIndex),
                Type t when t == typeof(List<int>) => reader.GetFieldValue<List<int>>(propertyIndex),
                Type t when t == typeof(List<long>) => reader.GetFieldValue<List<long>>(propertyIndex),
                Type t when t == typeof(List<float>) => reader.GetFieldValue<List<float>>(propertyIndex),
                Type t when t == typeof(List<double>) => reader.GetFieldValue<List<double>>(propertyIndex),
                Type t when t == typeof(List<decimal>) => reader.GetFieldValue<List<decimal>>(propertyIndex),
                Type t when t == typeof(List<string>) => reader.GetFieldValue<List<string>>(propertyIndex),
                Type t when t == typeof(List<byte[]>) => reader.GetFieldValue<List<byte[]>>(propertyIndex),
                Type t when t == typeof(List<DateTime>) => reader.GetFieldValue<List<DateTime>>(propertyIndex),
                Type t when t == typeof(List<DateTimeOffset>) => reader.GetFieldValue<List<DateTimeOffset>>(propertyIndex),
                Type t when t == typeof(List<Guid>) => reader.GetFieldValue<List<Guid>>(propertyIndex),

                _ => new UnreachableException()

            };
        }

        return reader.GetValue(propertyIndex);
    }

    public static NpgsqlDbType? GetNpgsqlDbType(Type propertyType) =>
        (Nullable.GetUnderlyingType(propertyType) ?? propertyType) switch
        {
            Type t when t == typeof(bool) => NpgsqlDbType.Boolean,
            Type t when t == typeof(short) => NpgsqlDbType.Smallint,
            Type t when t == typeof(int) => NpgsqlDbType.Integer,
            Type t when t == typeof(long) => NpgsqlDbType.Bigint,
            Type t when t == typeof(float) => NpgsqlDbType.Real,
            Type t when t == typeof(double) => NpgsqlDbType.Double,
            Type t when t == typeof(decimal) => NpgsqlDbType.Numeric,
            Type t when t == typeof(string) => NpgsqlDbType.Text,
            Type t when t == typeof(byte[]) => NpgsqlDbType.Bytea,
            Type t when t == typeof(DateTime) => NpgsqlDbType.Timestamp,
            Type t when t == typeof(DateTimeOffset) => NpgsqlDbType.TimestampTz,
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
        static bool TryGetBaseType(Type type, [NotNullWhen(true)] out string? typeName)
        {
            typeName = type switch
            {
                Type t when t == typeof(bool) => "BOOLEAN",
                Type t when t == typeof(short) => "SMALLINT",
                Type t when t == typeof(int) => "INTEGER",
                Type t when t == typeof(long) => "BIGINT",
                Type t when t == typeof(float) => "REAL",
                Type t when t == typeof(double) => "DOUBLE PRECISION",
                Type t when t == typeof(decimal) => "NUMERIC",
                Type t when t == typeof(string) => "TEXT",
                Type t when t == typeof(byte[]) => "BYTEA",
                Type t when t == typeof(DateTime) => "TIMESTAMP",
                Type t when t == typeof(DateTimeOffset) => "TIMESTAMPTZ",
                Type t when t == typeof(Guid) => "UUID",
                _ => null
            };

            return typeName is not null;
        }

        // TODO: Handle NRTs properly via NullabilityInfoContext

        if (TryGetBaseType(propertyType, out string? pgType))
        {
            return (pgType, !propertyType.IsValueType);
        }

        // Handle nullable types (e.g. Nullable<int>)
        if (Nullable.GetUnderlyingType(propertyType) is Type unwrappedType
            && TryGetBaseType(unwrappedType, out string? underlyingPgType))
        {
            return (underlyingPgType, true);
        }

        // Handle collections
        if ((propertyType.IsArray && TryGetBaseType(propertyType.GetElementType()!, out string? elementPgType))
            || (propertyType.IsGenericType
                && propertyType.GetGenericTypeDefinition() == typeof(List<>)
                && TryGetBaseType(propertyType.GetGenericArguments()[0], out elementPgType)))
        {
            return (elementPgType + "[]", true);
        }

        throw new NotSupportedException($"Type {propertyType.Name} is not supported by this store.");
    }

    /// <summary>
    /// Gets the PostgreSQL vector type name based on the dimensions of the vector property.
    /// </summary>
    /// <param name="vectorProperty">The vector property.</param>
    /// <returns>The PostgreSQL vector type name.</returns>
    public static (string PgType, bool IsNullable) GetPgVectorTypeName(VectorPropertyModel vectorProperty)
    {
        var unwrappedEmbeddingType = Nullable.GetUnderlyingType(vectorProperty.EmbeddingType) ?? vectorProperty.EmbeddingType;

        var pgType = unwrappedEmbeddingType switch
        {
            Type t when t == typeof(ReadOnlyMemory<float>)
                || t == typeof(Embedding<float>)
                || t == typeof(float[])
                => "VECTOR",

#if NET8_0_OR_GREATER
            Type t when t == typeof(ReadOnlyMemory<Half>)
                || t == typeof(Embedding<Half>)
                || t == typeof(Half[])
                => "HALFVEC",
#endif

            Type t when t == typeof(SparseVector) => "SPARSEVEC",
            Type t when t == typeof(BitArray) => "BIT",

            _ => throw new NotSupportedException($"Type {vectorProperty.EmbeddingType.Name} is not supported by this store.")
        };

        return ($"{pgType}({vectorProperty.Dimensions})", unwrappedEmbeddingType != vectorProperty.EmbeddingType);
    }

    public static NpgsqlParameter GetNpgsqlParameter(object? value)
        => new() { Value = value ?? DBNull.Value };

    /// <summary>
    /// Returns information about indexes to create, validating that the dimensions of the vector are supported.
    /// </summary>
    /// <param name="properties">The properties of the vector store record.</param>
    /// <returns>A list of tuples containing the column name, index kind, and distance function for each property.</returns>
    /// <remarks>
    /// The default index kind is "Flat", which prevents the creation of an index.
    /// </remarks>
    public static List<(string column, string kind, string function, bool isVector)> GetIndexInfo(IReadOnlyList<PropertyModel> properties)
    {
        var vectorIndexesToCreate = new List<(string column, string kind, string function, bool isVector)>();
        foreach (var property in properties)
        {
            switch (property)
            {
                case KeyPropertyModel:
                    // There is no need to create a separate index for the key property.
                    break;

                case VectorPropertyModel vectorProperty:
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

                case DataPropertyModel dataProperty:
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
}
