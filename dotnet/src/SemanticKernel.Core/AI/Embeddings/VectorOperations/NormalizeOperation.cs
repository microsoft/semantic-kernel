// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;

namespace Microsoft.SemanticKernel.AI.Embeddings.VectorOperations;

/// <summary>
/// Extension methods to normalize a vector.
/// </summary>
/// <remarks>
/// https://en.wikipedia.org/wiki/Unit_vector
/// </remarks>
[Obsolete("Numerical operations will be removed in a future release. Use System.Numerics.Tensors.TensorPrimitives instead.")]
[EditorBrowsable(EditorBrowsableState.Never)]
public static class NormalizeOperation
{
    /// <summary>
    /// Normalizes a vector in-place by dividing all elements by the scalar Euclidean length.
    /// The resulting length will be 1.0. Does not allocate new memory.
    /// </summary>
    /// <typeparam name="TNumber">The unmanaged data type (<see cref="float"/>, <see cref="double"/> currently supported).</typeparam>
    /// <param name="vector">The input vector.</param>
    public static void NormalizeInPlace<TNumber>(this Span<TNumber> vector)
        where TNumber : unmanaged
    {
        vector.DivideByInPlace(vector.EuclideanLength());
    }

    /// <summary>
    /// Normalizes a vector in-place by dividing all elements by the scalar Euclidean length.
    /// The resulting length will be 1.0. Does not allocate new memory.
    /// </summary>
    /// <typeparam name="TNumber">The unmanaged data type (<see cref="float"/>, <see cref="double"/> currently supported).</typeparam>
    /// <param name="vector">The input vector.</param>
    public static void NormalizeInPlace<TNumber>(this TNumber[] vector)
        where TNumber : unmanaged
    {
        vector.AsSpan().NormalizeInPlace();
    }
}
