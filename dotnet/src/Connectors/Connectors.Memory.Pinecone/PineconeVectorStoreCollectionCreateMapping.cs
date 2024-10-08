// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Data;
using Pinecone;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Contains mapping helpers to use when creating a Pinecone vector collection.
/// </summary>
internal static class PineconeVectorStoreCollectionCreateMapping
{
    /// <summary>
    /// Maps information stored in <see cref="VectorStoreRecordVectorProperty"/> to a structure used by Pinecone SDK to create a serverless index.
    /// </summary>
    /// <param name="vectorProperty">The property to map.</param>
    /// <returns>The structure containing settings used to create a serverless index.</returns>
    /// <exception cref="InvalidOperationException">Thrown if the property is missing information or has unsupported options specified.</exception>
    public static (uint Dimension, Metric Metric) MapServerlessIndex(VectorStoreRecordVectorProperty vectorProperty)
    {
        if (vectorProperty!.Dimensions is not > 0)
        {
            throw new InvalidOperationException($"Property {nameof(vectorProperty.Dimensions)} on {nameof(VectorStoreRecordVectorProperty)} '{vectorProperty.DataModelPropertyName}' must be set to a positive integer to create a collection.");
        }

        return (Dimension: (uint)vectorProperty.Dimensions, Metric: GetSDKMetricAlgorithm(vectorProperty));
    }

    /// <summary>
    /// Get the configured <see cref="Metric"/> from the given <paramref name="vectorProperty"/>.
    /// If none is configured, the default is <see cref="Metric.Cosine"/>.
    /// </summary>
    /// <param name="vectorProperty">The vector property definition.</param>
    /// <returns>The chosen <see cref="Metric"/>.</returns>
    /// <exception cref="InvalidOperationException">Thrown if a distance function is chosen that isn't supported by Pinecone.</exception>
    public static Metric GetSDKMetricAlgorithm(VectorStoreRecordVectorProperty vectorProperty)
        => vectorProperty.DistanceFunction switch
        {
            DistanceFunction.CosineSimilarity => Metric.Cosine,
            DistanceFunction.DotProductSimilarity => Metric.DotProduct,
            DistanceFunction.EuclideanDistance => Metric.Euclidean,
            null => Metric.Cosine,
            _ => throw new InvalidOperationException($"Distance function '{vectorProperty.DistanceFunction}' for {nameof(VectorStoreRecordVectorProperty)} '{vectorProperty.DataModelPropertyName}' is not supported by the Pinecone VectorStore.")
        };
}
