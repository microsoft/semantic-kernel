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

#if NET
            ReadOnlyMemory<Half> m => new Pgvector.HalfVector(m),
            Embedding<Half> e => new Pgvector.HalfVector(e.Vector),
            Half[] a => new Pgvector.HalfVector(a),
#endif

            BitArray bitArray => bitArray,
            BinaryEmbedding binaryEmbedding => binaryEmbedding.Vector,
            SparseVector sparseVector => sparseVector,

            null => null,

            var value => throw new NotSupportedException($"Mapping for type '{value.GetType().Name}' to a vector is not supported.")
        };

    /// <summary>
    /// Gets the NpgsqlDbType for a property, taking into account any store type annotation.
    /// </summary>
    internal static NpgsqlDbType? GetNpgsqlDbType(PropertyModel property)
        => (Nullable.GetUnderlyingType(property.Type) ?? property.Type) switch
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
            Type t when t == typeof(Guid) => NpgsqlDbType.Uuid,
            Type t when t == typeof(DateTimeOffset) => NpgsqlDbType.TimestampTz,

            // DateTime properties map to PG's "timestamp with time zone" (UTC timestamps) by default, aligning with Npgsql/EF/etc.
            // Users can explicitly opt into "timestamp without time zone".
            Type t when t == typeof(DateTime) && property.IsTimestampWithoutTimezone() => NpgsqlDbType.Timestamp,
            Type t when t == typeof(DateTime) => NpgsqlDbType.TimestampTz,

            _ => null
        };

    /// <summary>
    /// Maps a .NET type to a PostgreSQL type name, taking into account any store type annotation on the property.
    /// </summary>
    internal static (string PgType, bool IsNullable) GetPostgresTypeName(PropertyModel property)
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
                Type t when t == typeof(DateTime) => "TIMESTAMPTZ",
                Type t when t == typeof(DateTimeOffset) => "TIMESTAMPTZ",
                Type t when t == typeof(Guid) => "UUID",
                _ => null
            };

            return typeName is not null;
        }

        var propertyType = property.Type;

        // TODO: Handle NRTs properly via NullabilityInfoContext

        (string PgType, bool IsNullable) result;

        if (TryGetBaseType(propertyType, out string? pgType))
        {
            result = (pgType, !propertyType.IsValueType);
        }
        // Handle nullable types (e.g. Nullable<int>)
        else if (Nullable.GetUnderlyingType(propertyType) is Type unwrappedType
            && TryGetBaseType(unwrappedType, out string? underlyingPgType))
        {
            result = (underlyingPgType, true);
        }
        // Handle collections
        else if ((propertyType.IsArray && TryGetBaseType(propertyType.GetElementType()!, out string? elementPgType))
            || (propertyType.IsGenericType
                && propertyType.GetGenericTypeDefinition() == typeof(List<>)
                && TryGetBaseType(propertyType.GetGenericArguments()[0], out elementPgType)))
        {
            result = (elementPgType + "[]", true);
        }
        else
        {
            throw new NotSupportedException($"Type {propertyType.Name} is not supported by this store.");
        }

        if (property.IsTimestampWithoutTimezone())
        {
            // Replace TIMESTAMPTZ with TIMESTAMP in the PG type name.
            // This handles both "TIMESTAMPTZ" and "TIMESTAMPTZ[]" cases.
            result = ("TIMESTAMP", result.IsNullable);
        }

        return result;
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

#if NET
            Type t when t == typeof(ReadOnlyMemory<Half>)
                || t == typeof(Embedding<Half>)
                || t == typeof(Half[])
                => "HALFVEC",
#endif

            Type t when t == typeof(SparseVector) => "SPARSEVEC",
            Type t when t == typeof(BitArray) => "BIT",
            Type t when t == typeof(BinaryEmbedding) => "BIT",

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
    /// <returns>A list of tuples containing the column name, index kind, distance function, and full-text language for each property.</returns>
    /// <remarks>
    /// The default index kind is "Flat", which prevents the creation of an index.
    /// </remarks>
    public static List<(string column, string kind, string function, bool isVector, bool isFullText, string? fullTextLanguage)> GetIndexInfo(IReadOnlyList<PropertyModel> properties)
    {
        var vectorIndexesToCreate = new List<(string column, string kind, string function, bool isVector, bool isFullText, string? fullTextLanguage)>();
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

                        vectorIndexesToCreate.Add((vectorProperty.StorageName, indexKind, distanceFunction, isVector: true, isFullText: false, fullTextLanguage: null));
                    }

                    break;

                case DataPropertyModel dataProperty:
                    if (dataProperty.IsIndexed)
                    {
                        vectorIndexesToCreate.Add((dataProperty.StorageName, kind: "", function: "", isVector: false, isFullText: false, fullTextLanguage: null));
                    }

                    if (dataProperty.IsFullTextIndexed)
                    {
                        var language = dataProperty.GetFullTextSearchLanguageOrDefault();
                        vectorIndexesToCreate.Add((dataProperty.StorageName, kind: "", function: "", isVector: false, isFullText: true, fullTextLanguage: language));
                    }
                    break;

                default:
                    throw new UnreachableException();
            }
        }

        return vectorIndexesToCreate;
    }
}
