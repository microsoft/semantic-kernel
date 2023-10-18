// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Numerics;
using System.Runtime.InteropServices;

namespace Microsoft.SemanticKernel.AI.Embeddings.VectorOperations;

/// <summary>
/// Extension methods to calculate the cosine similarity between two vectors.
/// </summary>
/// <remarks>
/// https://en.wikipedia.org/wiki/Cosine_similarity
/// </remarks>
[Obsolete("Numerical operations will be removed in a future release. Use System.Numerics.Tensors.TensorPrimitives instead.")]
[EditorBrowsable(EditorBrowsableState.Never)]
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

        throw new NotSupportedException();
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

        fixed (double* pxBuffer = x, pyBuffer = y)
        {
            double dotSum = 0, lenXSum = 0, lenYSum = 0;

            double* px = pxBuffer, py = pyBuffer;
            double* pxEnd = px + x.Length;

            if (Vector.IsHardwareAccelerated &&
                x.Length >= Vector<double>.Count)
            {
                double* pxOneVectorFromEnd = pxEnd - Vector<double>.Count;
                do
                {
                    Vector<double> xVec = *(Vector<double>*)px;
                    Vector<double> yVec = *(Vector<double>*)py;

                    dotSum += Vector.Dot(xVec, yVec); // Dot product
                    lenXSum += Vector.Dot(xVec, xVec); // For magnitude of x
                    lenYSum += Vector.Dot(yVec, yVec); // For magnitude of y

                    px += Vector<double>.Count;
                    py += Vector<double>.Count;
                } while (px <= pxOneVectorFromEnd);
            }

            while (px < pxEnd)
            {
                double xVal = *px;
                double yVal = *py;

                dotSum += xVal * yVal; // Dot product
                lenXSum += xVal * xVal; // For magnitude of x
                lenYSum += yVal * yVal; // For magnitude of y

                ++px;
                ++py;
            }

            // Cosine Similarity of X, Y
            // Sum(X * Y) / |X| * |Y|
            return dotSum / (Math.Sqrt(lenXSum) * Math.Sqrt(lenYSum));
        }
    }

    private static unsafe double CosineSimilarityImplementation(ReadOnlySpan<float> x, ReadOnlySpan<float> y)
    {
        if (x.Length != y.Length)
        {
            throw new ArgumentException("Array lengths must be equal");
        }

        fixed (float* pxBuffer = x, pyBuffer = y)
        {
            double dotSum = 0, lenXSum = 0, lenYSum = 0;

            float* px = pxBuffer, py = pyBuffer;
            float* pxEnd = px + x.Length;

            if (Vector.IsHardwareAccelerated &&
                x.Length >= Vector<float>.Count)
            {
                float* pxOneVectorFromEnd = pxEnd - Vector<float>.Count;
                do
                {
                    Vector<float> xVec = *(Vector<float>*)px;
                    Vector<float> yVec = *(Vector<float>*)py;

                    dotSum += Vector.Dot(xVec, yVec); // Dot product
                    lenXSum += Vector.Dot(xVec, xVec); // For magnitude of x
                    lenYSum += Vector.Dot(yVec, yVec); // For magnitude of y

                    px += Vector<float>.Count;
                    py += Vector<float>.Count;
                } while (px <= pxOneVectorFromEnd);
            }

            while (px < pxEnd)
            {
                float xVal = *px;
                float yVal = *py;

                dotSum += xVal * yVal; // Dot product
                lenXSum += xVal * xVal; // For magnitude of x
                lenYSum += yVal * yVal; // For magnitude of y

                ++px;
                ++py;
            }

            // Cosine Similarity of X, Y
            // Sum(X * Y) / |X| * |Y|
            return dotSum / (Math.Sqrt(lenXSum) * Math.Sqrt(lenYSum));
        }
    }

    #endregion
}
