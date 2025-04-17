// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Qdrant.Client.Grpc;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// Contains mapping helpers to use when creating a qdrant vector collection.
/// </summary>
internal static class QdrantVectorStoreCollectionCreateMapping
{
    /// <summary>A dictionary of types and their matching qdrant index schema type.</summary>
    public static readonly Dictionary<Type, PayloadSchemaType> s_schemaTypeMap = new()
    {
        { typeof(short), PayloadSchemaType.Integer },
        { typeof(sbyte), PayloadSchemaType.Integer },
        { typeof(byte), PayloadSchemaType.Integer },
        { typeof(ushort), PayloadSchemaType.Integer },
        { typeof(int), PayloadSchemaType.Integer },
        { typeof(uint), PayloadSchemaType.Integer },
        { typeof(long), PayloadSchemaType.Integer },
        { typeof(ulong), PayloadSchemaType.Integer },
        { typeof(float), PayloadSchemaType.Float },
        { typeof(double), PayloadSchemaType.Float },
        { typeof(decimal), PayloadSchemaType.Float },

        { typeof(short?), PayloadSchemaType.Integer },
        { typeof(sbyte?), PayloadSchemaType.Integer },
        { typeof(byte?), PayloadSchemaType.Integer },
        { typeof(ushort?), PayloadSchemaType.Integer },
        { typeof(int?), PayloadSchemaType.Integer },
        { typeof(uint?), PayloadSchemaType.Integer },
        { typeof(long?), PayloadSchemaType.Integer },
        { typeof(ulong?), PayloadSchemaType.Integer },
        { typeof(float?), PayloadSchemaType.Float },
        { typeof(double?), PayloadSchemaType.Float },
        { typeof(decimal?), PayloadSchemaType.Float },

        { typeof(string), PayloadSchemaType.Keyword },
        { typeof(DateTimeOffset), PayloadSchemaType.Datetime },
        { typeof(bool), PayloadSchemaType.Bool },

        { typeof(DateTimeOffset?), PayloadSchemaType.Datetime },
        { typeof(bool?), PayloadSchemaType.Bool },
    };

    /// <summary>
    /// Maps a single <see cref="VectorStoreRecordVectorProperty"/> to a qdrant <see cref="VectorParams"/>.
    /// </summary>
    /// <param name="vectorProperty">The property to map.</param>
    /// <returns>The mapped <see cref="VectorParams"/>.</returns>
    /// <exception cref="InvalidOperationException">Thrown if the property is missing information or has unsupported options specified.</exception>
    public static VectorParams MapSingleVector(VectorStoreRecordVectorProperty vectorProperty)
    {
        if (vectorProperty!.Dimensions is not > 0)
        {
            throw new InvalidOperationException($"Property {nameof(vectorProperty.Dimensions)} on {nameof(VectorStoreRecordVectorProperty)} '{vectorProperty.DataModelPropertyName}' must be set to a positive integer to create a collection.");
        }

        if (vectorProperty!.IndexKind is not null && vectorProperty!.IndexKind != IndexKind.Hnsw)
        {
            throw new InvalidOperationException($"Index kind '{vectorProperty!.IndexKind}' for {nameof(VectorStoreRecordVectorProperty)} '{vectorProperty.DataModelPropertyName}' is not supported by the Qdrant VectorStore.");
        }

        return new VectorParams { Size = (ulong)vectorProperty.Dimensions, Distance = QdrantVectorStoreCollectionCreateMapping.GetSDKDistanceAlgorithm(vectorProperty) };
    }

    /// <summary>
    /// Maps a collection of <see cref="VectorStoreRecordVectorProperty"/> to a qdrant <see cref="VectorParamsMap"/>.
    /// </summary>
    /// <param name="vectorProperties">The properties to map.</param>
    /// <param name="storagePropertyNames">The mapping of property names to storage names.</param>
    /// <returns>THe mapped <see cref="VectorParamsMap"/>.</returns>
    /// <exception cref="InvalidOperationException">Thrown if the property is missing information or has unsupported options specified.</exception>
    public static VectorParamsMap MapNamedVectors(IEnumerable<VectorStoreRecordVectorProperty> vectorProperties, IReadOnlyDictionary<string, string> storagePropertyNames)
    {
        var vectorParamsMap = new VectorParamsMap();

        foreach (var vectorProperty in vectorProperties)
        {
            var storageName = storagePropertyNames[vectorProperty.DataModelPropertyName];

            // Add each vector property to the vectors map.
            vectorParamsMap.Map.Add(
                storageName,
                MapSingleVector(vectorProperty));
        }

        return vectorParamsMap;
    }

    /// <summary>
    /// Get the configured <see cref="Distance"/> from the given <paramref name="vectorProperty"/>.
    /// If none is configured, the default is <see cref="Distance.Cosine"/>.
    /// </summary>
    /// <param name="vectorProperty">The vector property definition.</param>
    /// <returns>The chosen <see cref="Distance"/>.</returns>
    /// <exception cref="InvalidOperationException">Thrown if a distance function is chosen that isn't supported by qdrant.</exception>
    public static Distance GetSDKDistanceAlgorithm(VectorStoreRecordVectorProperty vectorProperty)
    {
        if (vectorProperty.DistanceFunction is null)
        {
            return Distance.Cosine;
        }

        return vectorProperty.DistanceFunction switch
        {
            DistanceFunction.CosineSimilarity => Distance.Cosine,
            DistanceFunction.DotProductSimilarity => Distance.Dot,
            DistanceFunction.EuclideanDistance => Distance.Euclid,
            DistanceFunction.ManhattanDistance => Distance.Manhattan,
            _ => throw new InvalidOperationException($"Distance function '{vectorProperty.DistanceFunction}' for {nameof(VectorStoreRecordVectorProperty)} '{vectorProperty.DataModelPropertyName}' is not supported by the Qdrant VectorStore.")
        };
    }
}
