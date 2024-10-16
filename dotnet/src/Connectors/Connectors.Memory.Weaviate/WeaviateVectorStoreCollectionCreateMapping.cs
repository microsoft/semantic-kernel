﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

/// <summary>
/// Class to construct Weaviate collection schema with configuration for data and vector properties.
/// More information here: <see href="https://weaviate.io/developers/weaviate/config-refs/schema"/>.
/// </summary>
internal static class WeaviateVectorStoreCollectionCreateMapping
{
    /// <summary>
    /// Maps record type properties to Weaviate collection schema for collection creation.
    /// </summary>
    /// <param name="collectionName">The name of the vector store collection.</param>
    /// <param name="dataProperties">Collection of record data properties.</param>
    /// <param name="vectorProperties">Collection of record vector properties.</param>
    /// <param name="storagePropertyNames">A dictionary that maps from a property name to the storage name that should be used when serializing it to JSON for data and vector properties.</param>
    /// <returns>Weaviate collection schema.</returns>
    public static WeaviateCollectionSchema MapToSchema(
        string collectionName,
        IEnumerable<VectorStoreRecordDataProperty> dataProperties,
        IEnumerable<VectorStoreRecordVectorProperty> vectorProperties,
        IReadOnlyDictionary<string, string> storagePropertyNames)
    {
        var schema = new WeaviateCollectionSchema(collectionName);

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
                $"Index kind '{indexKind}' on {nameof(VectorStoreRecordVectorProperty)} '{vectorPropertyName}' is not supported by the Weaviate VectorStore. " +
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
            DistanceFunction.DotProductSimilarity => Dot,
            DistanceFunction.EuclideanSquaredDistance => EuclideanSquared,
            DistanceFunction.Hamming => Hamming,
            DistanceFunction.ManhattanDistance => Manhattan,
            _ => throw new InvalidOperationException(
                $"Distance function '{distanceFunction}' on {nameof(VectorStoreRecordVectorProperty)} '{vectorPropertyName}' is not supported by the Weaviate VectorStore. " +
                $"Supported distance functions: {string.Join(", ",
                    DistanceFunction.CosineDistance,
                    DistanceFunction.DotProductSimilarity,
                    DistanceFunction.EuclideanSquaredDistance,
                    DistanceFunction.Hamming,
                    DistanceFunction.ManhattanDistance)}")
        };
    }

    /// <summary>
    /// Maps record property type to Weaviate data type taking into account if the type is a collection or single value.
    /// </summary>
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

    /// <summary>
    /// Maps record property type to Weaviate data type.
    /// More information here: <see href="https://weaviate.io/developers/weaviate/config-refs/datatypes"/>.
    /// </summary>
    private static string MapType(Type type, bool isCollection)
    {
        return type switch
        {
            Type t when t == typeof(string) => isCollection ? "text[]" : "text",
            Type t when t == typeof(int) || t == typeof(long) || t == typeof(short) || t == typeof(byte) ||
                        t == typeof(int?) || t == typeof(long?) || t == typeof(short?) || t == typeof(byte?) => isCollection ? "int[]" : "int",
            Type t when t == typeof(float) || t == typeof(double) || t == typeof(decimal) ||
                        t == typeof(float?) || t == typeof(double?) || t == typeof(decimal?) => isCollection ? "number[]" : "number",
            Type t when t == typeof(DateTime) || t == typeof(DateTime?) ||
                        t == typeof(DateTimeOffset) || t == typeof(DateTimeOffset?) => isCollection ? "date[]" : "date",
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
