// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Numerics.Tensors;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.InMemory;

/// <summary>
/// Contains mapping helpers to use when searching for documents using the InMemory store.
/// </summary>
internal static class InMemoryCollectionSearchMapping
{
    /// <summary>
    /// Compare the two vectors using the specified distance function.
    /// </summary>
    /// <param name="x">The first vector to compare.</param>
    /// <param name="y">The second vector to compare.</param>
    /// <param name="distanceFunction">The distance function to use for comparison.</param>
    /// <returns>The score of the comparison.</returns>
    /// <exception cref="NotSupportedException">Thrown when the distance function is not supported.</exception>
    public static float CompareVectors(ReadOnlySpan<float> x, ReadOnlySpan<float> y, string? distanceFunction)
    {
        switch (distanceFunction)
        {
            case null:
            case DistanceFunction.CosineSimilarity:
            case DistanceFunction.CosineDistance:
                return TensorPrimitives.CosineSimilarity(x, y);
            case DistanceFunction.DotProductSimilarity:
                return TensorPrimitives.Dot(x, y);
            case DistanceFunction.EuclideanDistance:
                return TensorPrimitives.Distance(x, y);
            default:
                throw new NotSupportedException($"The distance function '{distanceFunction}' is not supported by the InMemory connector.");
        }
    }

    /// <summary>
    /// Indicates whether result ordering should be descending or ascending, to get most similar results at the top, based on the distance function.
    /// </summary>
    /// <param name="distanceFunction">The distance function to use for comparison.</param>
    /// <returns>Whether to order descending or ascending.</returns>
    /// <exception cref="NotSupportedException">Thrown when the distance function is not supported.</exception>
    public static bool ShouldSortDescending(string? distanceFunction)
    {
        switch (distanceFunction)
        {
            case null:
            case DistanceFunction.CosineSimilarity:
            case DistanceFunction.DotProductSimilarity:
                return true;
            case DistanceFunction.CosineDistance:
            case DistanceFunction.EuclideanDistance:
                return false;
            default:
                throw new NotSupportedException($"The distance function '{distanceFunction}' is not supported by the InMemory connector.");
        }
    }

    /// <summary>
    /// Converts the provided score into the correct result depending on the distance function.
    /// The main purpose here is to convert from cosine similarity to cosine distance if cosine distance is requested,
    /// since the two are inversely related and the <see cref="TensorPrimitives"/> only supports cosine similarity so
    /// we are using cosine similarity for both similarity and distance.
    /// </summary>
    /// <param name="score">The score to convert.</param>
    /// <param name="distanceFunction">The distance function to use for comparison.</param>
    /// <returns>Whether to order descending or ascending.</returns>
    /// <exception cref="NotSupportedException">Thrown when the distance function is not supported.</exception>
    public static float ConvertScore(float score, string? distanceFunction)
    {
        switch (distanceFunction)
        {
            case DistanceFunction.CosineDistance:
                return 1 - score;
            case null:
            case DistanceFunction.CosineSimilarity:
            case DistanceFunction.DotProductSimilarity:
            case DistanceFunction.EuclideanDistance:
                return score;
            default:
                throw new NotSupportedException($"The distance function '{distanceFunction}' is not supported by the InMemory connector.");
        }
    }
}
