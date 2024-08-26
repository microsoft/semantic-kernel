// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal static class WeaviateVectorStoreCollectionCreateMapping
{
    public static WeaviateCollectionSchema MapToSchema(
        string collectionName,
        IEnumerable<VectorStoreRecordDataProperty> dataProperties,
        IEnumerable<VectorStoreRecordVectorProperty> vectorProperties,
        Dictionary<string, string> storagePropertyNames)
    {
        var schema = new WeaviateCollectionSchema { CollectionName = collectionName };

        // Handle data properties.
        foreach (var property in dataProperties)
        {
            schema.Properties.Add(new WeaviateCollectionSchemaProperty
            {
                Name = storagePropertyNames[property.DataModelPropertyName],
                DataType = [MapType(property.PropertyType)],
                IndexFilterable = property.IsFilterable,
                IndexSearchable = property.IsFullTextSearchable
            });
        }

        // Handle vector properties.
        foreach (var property in vectorProperties)
        {
            var vectorPropertyName = storagePropertyNames[property.DataModelPropertyName];
            schema.VectorConfigurations.Add(vectorPropertyName, new WeaviateCollectionSchemaVectorConfig
            {
                VectorIndexType = MapIndexKind(property.IndexKind, vectorPropertyName),
                VectorIndexConfig = new WeaviateCollectionSchemaVectorIndexConfig
                {
                    Distance = MapDistanceFunction(property.DistanceFunction, vectorPropertyName)
                }
            });
        }

        return schema;
    }

    #region private

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
            _ => throw new InvalidOperationException($"Index kind '{indexKind}' on {nameof(VectorStoreRecordVectorProperty)} '{vectorPropertyName}' is not supported by the Weaviate VectorStore.")
        };
    }

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
            DistanceFunction.DotProductSimilarity => Dot,
            DistanceFunction.EuclideanSquaredDistance => EuclideanSquared,
            DistanceFunction.Hamming => Hamming,
            DistanceFunction.ManhattanDistance => Manhattan,
            _ => throw new InvalidOperationException($"Distance function '{distanceFunction}' on {nameof(VectorStoreRecordVectorProperty)} '{vectorPropertyName}' is not supported by the Weaviate VectorStore.")
        };
    }

    private static string MapType(Type type)
    {
        // Check if the type is a collection.
        if (typeof(IEnumerable).IsAssignableFrom(type) && type != typeof(string))
        {
            var elementType = GetCollectionElementType(type);

            // If type is a collection, handle collection element type.
            return MapType(elementType, isCollection: true);
        }

        // If type is not a collection, handle single type.
        return MapType(type, isCollection: false);
    }

    private static string MapType(Type type, bool isCollection)
    {
        return type switch
        {
            Type t when t == typeof(string) => isCollection ? "text[]" : "text",
            Type t when t == typeof(int) || t == typeof(long) || t == typeof(short) || t == typeof(byte) ||
                        t == typeof(int?) || t == typeof(long?) || t == typeof(short?) || t == typeof(byte?) => isCollection ? "int[]" : "int",
            Type t when t == typeof(float) || t == typeof(double) || t == typeof(decimal) ||
                        t == typeof(float?) || t == typeof(double?) || t == typeof(decimal?) => isCollection ? "number[]" : "number",
            Type t when t == typeof(DateTime) || t == typeof(DateTime?) => isCollection ? "date[]" : "date",
            Type t when t == typeof(Guid) || t == typeof(Guid?) => isCollection ? "uuid[]" : "uuid",
            Type t when t == typeof(bool) || t == typeof(bool?) => isCollection ? "boolean[]" : "boolean",
            _ => isCollection ? "object[]" : "object",
        };
    }

    /// <summary>
    /// Gets the element type of a collection.
    /// </summary>
    /// <remarks>
    /// For example, when <paramref name="type"/> is <see cref="List{T}"/>, returned type will be generic parameter <see langword="T"/>.
    /// </remarks>
    private static Type GetCollectionElementType(Type type)
    {
        if (type.IsArray)
        {
            var elementType = type.GetElementType();

            if (elementType is not null)
            {
                return elementType;
            }
        }

        if (type.IsGenericType)
        {
            return type.GetGenericArguments().First();
        }

        return typeof(object);
    }

    #endregion
}
