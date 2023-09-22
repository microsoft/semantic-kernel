// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Numerics;
using System.Runtime.InteropServices;

namespace Microsoft.SemanticKernel.AI.Embeddings.VectorOperations;

/// <summary>
/// Extension methods for vector dot product.
/// </summary>
/// <remarks>
/// https://en.wikipedia.org/wiki/Dot_product
/// </remarks>
public static class DotProductOperation
{
    /// <summary>
    /// Calculate the dot products of two vectors of type <typeparamref name="TNumber"/>.
    /// </summary>
    /// <typeparam name="TNumber">The unmanaged data type (<see cref="float"/>, <see cref="double"/> currently supported).</typeparam>
    /// <param name="x">The first vector.</param>
    /// <param name="y">The second vector.</param>
    /// <returns>The dot product as a <see cref="double"/>.</returns>
    public static double DotProduct<TNumber>(this ReadOnlySpan<TNumber> x, ReadOnlySpan<TNumber> y)
        where TNumber : unmanaged
    {
        if (typeof(TNumber) == typeof(float))
        {
            ReadOnlySpan<float> floatSpanX = MemoryMarshal.Cast<TNumber, float>(x);
            ReadOnlySpan<float> floatSpanY = MemoryMarshal.Cast<TNumber, float>(y);
            return DotProductImplementation(floatSpanX, floatSpanY);
        }
        else if (typeof(TNumber) == typeof(double))
        {
            ReadOnlySpan<double> doubleSpanX = MemoryMarshal.Cast<TNumber, double>(x);
            ReadOnlySpan<double> doubleSpanY = MemoryMarshal.Cast<TNumber, double>(y);
            return DotProductImplementation(doubleSpanX, doubleSpanY);
        }
        else
        {
            throw new NotSupportedException();
        }
    }

    /// <summary>
    /// Calculate the dot products of two vectors of type <typeparamref name="TNumber"/>.
    /// </summary>
    /// <typeparam name="TNumber">The unmanaged data type (<see cref="float"/>, <see cref="double"/> currently supported).</typeparam>
    /// <param name="x">The first vector.</param>
    /// <param name="y">The second vector.</param>
    /// <returns>The dot product as a <see cref="double"/>.</returns>
    public static double DotProduct<TNumber>(this Span<TNumber> x, Span<TNumber> y)
        where TNumber : unmanaged
    {
        return x.AsReadOnlySpan().DotProduct(y.AsReadOnlySpan());
    }

    /// <summary>
    /// Calculate the dot products of two vectors of type <typeparamref name="TNumber"/>.
    /// </summary>
    /// <typeparam name="TNumber">The unmanaged data type (<see cref="float"/>, <see cref="double"/> currently supported).</typeparam>
    /// <param name="x">The first vector.</param>
    /// <param name="y">The second vector.</param>
    /// <returns>The dot product as a <see cref="double"/>.</returns>
    public static double DotProduct<TNumber>(this TNumber[] x, TNumber[] y)
        where TNumber : unmanaged
    {
        return x.AsReadOnlySpan().DotProduct(y.AsReadOnlySpan());
    }

    #region private ================================================================================

    private static unsafe double DotProductImplementation(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        if (x.Length != y.Length)
        {
            throw new ArgumentException("Array lengths must be equal");
        }

        fixed (double* pxBuffer = x, pyBuffer = y)
        {
            double* px = pxBuffer, py = pyBuffer;
            double* pxEnd = px + x.Length;

            double dotSum = 0;

            if (Vector.IsHardwareAccelerated &&
                x.Length >= Vector<double>.Count)
            {
                double* pxOneVectorFromEnd = pxEnd - Vector<double>.Count;
                do
                {
                    dotSum += Vector.Dot(*(Vector<double>*)px, *(Vector<double>*)py); // Dot product

                    px += Vector<double>.Count;
                    py += Vector<double>.Count;
                } while (px <= pxOneVectorFromEnd);
            }

            while (px < pxEnd)
            {
                dotSum += *px * *py; // Dot product

                ++px;
                ++py;
            }

            return dotSum;
        }
    }

    private static unsafe double DotProductImplementation(ReadOnlySpan<float> x, ReadOnlySpan<float> y)
    {
        if (x.Length != y.Length)
        {
            throw new ArgumentException("Array lengths must be equal");
        }

        fixed (float* pxBuffer = x, pyBuffer = y)
        {
            float* px = pxBuffer, py = pyBuffer;
            float* pxEnd = px + x.Length;

            double dotSum = 0;

            if (Vector.IsHardwareAccelerated &&
                x.Length >= Vector<float>.Count)
            {
                float* pxOneVectorFromEnd = pxEnd - Vector<float>.Count;
                do
                {
                    dotSum += Vector.Dot(*(Vector<float>*)px, *(Vector<float>*)py); // Dot product

                    px += Vector<float>.Count;
                    py += Vector<float>.Count;
                } while (px <= pxOneVectorFromEnd);
            }

            while (px < pxEnd)
            {
                dotSum += *px * *py; // Dot product

                ++px;
                ++py;
            }

            return dotSum;
        }
    }

    #endregion
}
