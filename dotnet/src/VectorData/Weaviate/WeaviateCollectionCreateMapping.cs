// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

/// <summary>
/// Class to construct Weaviate collection schema with configuration for data and vector properties.
/// More information here: <see href="https://weaviate.io/developers/weaviate/config-refs/schema"/>.
/// </summary>
internal static class WeaviateCollectionCreateMapping
{
    /// <summary>
    /// Maps record type properties to Weaviate collection schema for collection creation.
    /// </summary>
    /// <param name="collectionName">The name of the vector store collection.</param>
    /// <param name="hasNamedVectors">Gets a value indicating whether the vectors in the store are named and multiple vectors are supported, or whether there is just a single unnamed vector in Weaviate collection.</param>
    /// <param name="model">The model.</param>
    /// <returns>Weaviate collection schema.</returns>
    public static WeaviateCollectionSchema MapToSchema(string collectionName, bool hasNamedVectors, CollectionModel model)
    {
        var schema = new WeaviateCollectionSchema(collectionName);

        // Handle data properties.
        foreach (var property in model.DataProperties)
        {
            schema.Properties.Add(new WeaviateCollectionSchemaProperty
            {
                Name = property.StorageName,
                DataType = [MapType(property.Type)],
                IndexFilterable = property.IsIndexed,
                IndexSearchable = property.IsFullTextIndexed
            });
        }

        // Handle vector properties.
        if (hasNamedVectors)
        {
            foreach (var property in model.VectorProperties)
            {
                schema.VectorConfigurations.Add(property.StorageName, new WeaviateCollectionSchemaVectorConfig
                {
                    VectorIndexType = MapIndexKind(property.IndexKind, property.StorageName),
                    VectorIndexConfig = new WeaviateCollectionSchemaVectorIndexConfig
                    {
                        Distance = MapDistanceFunction(property.DistanceFunction, property.StorageName)
                    }
                });
            }
        }
        else
        {
            var vectorProperty = model.VectorProperty;
            schema.VectorIndexType = MapIndexKind(vectorProperty.IndexKind, vectorProperty.StorageName);
            schema.VectorIndexConfig = new WeaviateCollectionSchemaVectorIndexConfig
            {
                Distance = MapDistanceFunction(vectorProperty.DistanceFunction, vectorProperty.StorageName)
            };
        }

        return schema;
    }

    #region private

    /// <summary>
    /// Maps record vector property index kind to Weaviate index kind.
    /// More information here: <see href="https://weaviate.io/developers/weaviate/config-refs/schema/vector-index"/>.
    /// </summary>
    private static string MapIndexKind(string? indexKind, string vectorPropertyName)
    {
        const string Hnsw = "hnsw";
        const string Flat = "flat";
        const string Dynamic = "dynamic";

        // If index kind is not provided, use default one.
        if (string.IsNullOrWhiteSpace(indexKind))
        {
            return Hnsw;
        }

        return indexKind switch
        {
            IndexKind.Hnsw => Hnsw,
            IndexKind.Flat => Flat,
            IndexKind.Dynamic => Dynamic,
            _ => throw new InvalidOperationException(
                $"Index kind '{indexKind}' on {nameof(VectorStoreVectorProperty)} '{vectorPropertyName}' is not supported by the Weaviate VectorStore. " +
                $"Supported index kinds: {string.Join(", ",
                    IndexKind.Hnsw,
                    IndexKind.Flat,
                    IndexKind.Dynamic)}")
        };
    }

    /// <summary>
    /// Maps record vector property distance function to Weaviate distance function.
    /// More information here: <see href="https://weaviate.io/developers/weaviate/config-refs/distances"/>.
    /// </summary>
    private static string MapDistanceFunction(string? distanceFunction, string vectorPropertyName)
    {
        const string Cosine = "cosine";
        const string Dot = "dot";
        const string EuclideanSquared = "l2-squared";
        const string Hamming = "hamming";
        const string Manhattan = "manhattan";

        // If distance function is not provided, use default one.
        if (string.IsNullOrWhiteSpace(distanceFunction))
        {
            return Cosine;
        }

        return distanceFunction switch
        {
            DistanceFunction.CosineDistance => Cosine,
            DistanceFunction.NegativeDotProductSimilarity => Dot,
            DistanceFunction.EuclideanSquaredDistance => EuclideanSquared,
            DistanceFunction.HammingDistance => Hamming,
            DistanceFunction.ManhattanDistance => Manhattan,
            _ => throw new NotSupportedException(
                $"Distance function '{distanceFunction}' on {nameof(VectorStoreVectorProperty)} '{vectorPropertyName}' is not supported by the Weaviate VectorStore. " +
                $"Supported distance functions: {string.Join(", ",
                    DistanceFunction.CosineDistance,
                    DistanceFunction.NegativeDotProductSimilarity,
                    DistanceFunction.EuclideanSquaredDistance,
                    DistanceFunction.HammingDistance,
                    DistanceFunction.ManhattanDistance)}")
        };
    }

    /// <summary>
    /// Maps record property type to Weaviate data type taking into account if the type is a collection or single value.
    /// </summary>
    private static string MapType(Type type)
    {
        return type switch
        {
            var t when TryMapType(type, out var mappedType) => mappedType,
            var t when type.IsArray && TryMapType(type.GetElementType()!, out var mappedType) => mappedType + "[]",
            var t when type.IsGenericType && type.GetGenericTypeDefinition() == typeof(List<>)
                && TryMapType(type.GenericTypeArguments[0], out var mappedType) => mappedType + "[]",
            _ => throw new NotSupportedException($"Type '{type.Name}' is not supported by Weaviate.")
        };

        bool TryMapType(Type type, [NotNullWhen(true)] out string? mappedType)
        {
            mappedType = (Nullable.GetUnderlyingType(type) ?? type) switch
            {
                Type t when t == typeof(string) => "text",
                Type t when t == typeof(int) || t == typeof(long) || t == typeof(short) || t == typeof(byte) => "int",
                Type t when t == typeof(float) || t == typeof(double) || t == typeof(decimal) => "number",
                Type t when t == typeof(DateTime) || t == typeof(DateTimeOffset) => "date",
                Type t when t == typeof(Guid) => "uuid",
                Type t when t == typeof(bool) => "boolean",

                _ => null
            };

            return mappedType is not null;
        }
    }

    #endregion
}
