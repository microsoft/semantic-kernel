// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Runtime.InteropServices;

namespace Microsoft.SemanticKernel.AI.Embeddings.VectorOperations;

/// <summary>
/// Extension methods to calculate the cosine similarity between two vectors.
/// </summary>
/// <remarks>
/// https://en.wikipedia.org/wiki/Cosine_similarity
/// </remarks>
public static class CosineSimilarityOperation
{
    /// <summary>
    /// Calculate the cosine similarity between two vectors of type <typeparamref name="TNumber"/>.
    /// </summary>
    /// <typeparam name="TNumber">The unmanaged data type (<see cref="float"/>, <see cref="double"/> currently supported).</typeparam>
    /// <param name="x">The first vector.</param>
    /// <param name="y">The second vector.</param>
    public static double CosineSimilarity<TNumber>(this ReadOnlySpan<TNumber> x, ReadOnlySpan<TNumber> y)
        where TNumber : unmanaged
    {
        if (typeof(TNumber) == typeof(float))
        {
            ReadOnlySpan<float> floatSpanX = MemoryMarshal.Cast<TNumber, float>(x);
            ReadOnlySpan<float> floatSpanY = MemoryMarshal.Cast<TNumber, float>(y);
            return CosineSimilarityImplementation(floatSpanX, floatSpanY);
        }
        else if (typeof(TNumber) == typeof(double))
        {
            ReadOnlySpan<double> doubleSpanX = MemoryMarshal.Cast<TNumber, double>(x);
            ReadOnlySpan<double> doubleSpanY = MemoryMarshal.Cast<TNumber, double>(y);
            return CosineSimilarityImplementation(doubleSpanX, doubleSpanY);
        }

        SupportedTypes.ThrowTypeNotSupported<TNumber>();
        return default;
    }

    /// <summary>
    /// Calculate the cosine similarity between two vectors of type <typeparamref name="TNumber"/>.
    /// </summary>
    /// <typeparam name="TNumber">The unmanaged data type (<see cref="float"/>, <see cref="double"/> currently supported).</typeparam>
    /// <param name="x">The first vector.</param>
    /// <param name="y">The second vector.</param>
    public static double CosineSimilarity<TNumber>(this Span<TNumber> x, Span<TNumber> y)
        where TNumber : unmanaged
    {
        return x.AsReadOnlySpan().CosineSimilarity(y.AsReadOnlySpan());
    }

    /// <summary>
    /// Calculate the cosine similarity between two vectors of type <typeparamref name="TNumber"/>.
    /// </summary>
    /// <typeparam name="TNumber">The unmanaged data type (<see cref="float"/>, <see cref="double"/> currently supported).</typeparam>
    /// <param name="x">The first vector.</param>
    /// <param name="y">The second vector.</param>
    public static double CosineSimilarity<TNumber>(this TNumber[] x, TNumber[] y)
        where TNumber : unmanaged
    {
        return x.AsReadOnlySpan().CosineSimilarity(y.AsReadOnlySpan());
    }

    #region private ================================================================================

    private static unsafe double CosineSimilarityImplementation(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        if (x.Length != y.Length)
        {
            throw new ArgumentException("Array lengths must be equal");
        }

        double dotSum = 0;
        double lenXSum = 0;
        double lenYSum = 0;
        fixed (double* pxBuffer = x)
        {
            fixed (double* pyBuffer = y)
            {
                double* px = pxBuffer;
                double* pxMax = px + x.Length;
                double* py = pyBuffer;
                while (px < pxMax)
                {
                    double xVal = *px;
                    double yVal = *py;
                    // Dot product
                    dotSum += xVal * yVal;
                    // For magnitude of x
                    lenXSum += xVal * xVal;
                    // For magnitude of y
                    lenYSum += yVal * yVal;
                    ++px;
                    ++py;
                }

                // Cosine Similarity of X, Y
                // Sum(X * Y) / |X| * |Y|
                return dotSum / (Math.Sqrt(lenXSum) * Math.Sqrt(lenYSum));
            }
        }
    }

    private static unsafe double CosineSimilarityImplementation(ReadOnlySpan<float> x, ReadOnlySpan<float> y)
    {
        if (x.Length != y.Length)
        {
            throw new ArgumentException("Array lengths must be equal");
        }

        double dotSum = 0;
        double lenXSum = 0;
        double lenYSum = 0;
        fixed (float* pxBuffer = x)
        {
            fixed (float* pyBuffer = y)
            {
                float* px = pxBuffer;
                float* pxMax = px + x.Length;
                float* py = pyBuffer;
                while (px < pxMax)
                {
                    float xVal = *px;
                    float yVal = *py;
                    // Dot product
                    dotSum += xVal * yVal;
                    // For magnitude of x
                    lenXSum += xVal * xVal;
                    // For magnitude of y
                    lenYSum += yVal * yVal;
                    ++px;
                    ++py;
                }

                // Cosine Similarity of X, Y
                // Sum(X * Y) / |X| * |Y|
                return dotSum / (Math.Sqrt(lenXSum) * Math.Sqrt(lenYSum));
            }
        }
    }

    #endregion
}
