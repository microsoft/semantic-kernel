// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.AI.Embeddings.VectorOperations;

/// <summary>
/// Extension methods to calculate the Euclidean length of a vector.
/// </summary>
public static class EuclideanLengthOperation
{
    /// <summary>
    /// Calculate the Euclidean length of a vector of type <typeparamref name="TNumber"/>.
    /// </summary>
    /// <typeparam name="TNumber">The unmanaged data type (<see cref="float"/>, <see cref="double"/> currently supported).</typeparam>
    /// <param name="x">The vector.</param>
    /// <returns>Euclidean length as a <see cref="double"/></returns>
    public static double EuclideanLength<TNumber>(this ReadOnlySpan<TNumber> x)
        where TNumber : unmanaged
    {
        return Math.Sqrt(x.DotProduct(x));
    }

    /// <summary>
    /// Calculate the Euclidean length of a vector of type <typeparamref name="TNumber"/>.
    /// </summary>
    /// <typeparam name="TNumber">The unmanaged data type (<see cref="float"/>, <see cref="double"/> currently supported).</typeparam>
    /// <param name="x">The vector.</param>
    /// <returns>Euclidean length as a <see cref="double"/></returns>
    public static double EuclideanLength<TNumber>(this Span<TNumber> x)
        where TNumber : unmanaged
    {
        var readOnly = x.AsReadOnlySpan();
        return readOnly.EuclideanLength();
    }

    /// <summary>
    /// Calculate the Euclidean length of a vector of type <typeparamref name="TNumber"/>.
    /// </summary>
    /// <typeparam name="TNumber">The unmanaged data type (<see cref="float"/>, <see cref="double"/> currently supported).</typeparam>
    /// <param name="vector">The vector.</param>
    /// <returns>Euclidean length as a <see cref="double"/></returns>
    public static double EuclideanLength<TNumber>(this TNumber[] vector)
        where TNumber : unmanaged
    {
        return vector.AsReadOnlySpan().EuclideanLength();
    }
}
