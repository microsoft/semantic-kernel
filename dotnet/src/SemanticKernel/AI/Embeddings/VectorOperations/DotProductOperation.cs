// Copyright (c) Microsoft. All rights reserved.

using System;
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

        SupportedTypes.ThrowTypeNotSupported<TNumber>();
        return default;
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

        if (x.Length % 4 == 0)
        {
            return DotProduct_Len4(x, y);
        }

        if (x.Length % 2 == 0)
        {
            return DotProduct_Len2(x, y);
        }

        // Vanilla Dot Product
        fixed (double* pxBuffer = x)
        {
            fixed (double* pyBuffer = y)
            {
                double dotSum = 0;
                double* px = pxBuffer;
                double* pxMax = px + x.Length;
                double* py = pyBuffer;
                while (px < pxMax)
                {
                    // Dot product
                    dotSum += *px * *py;
                    ++px;
                    ++py;
                }

                return dotSum;
            }
        }
    }

    private static unsafe double DotProductImplementation(ReadOnlySpan<float> x, ReadOnlySpan<float> y)
    {
        if (x.Length != y.Length)
        {
            throw new ArgumentException("Array lengths must be equal");
        }

        if (x.Length % 4 == 0)
        {
            return DotProduct_Len4(x, y);
        }

        if (x.Length % 2 == 0)
        {
            // Twice as fast
            return DotProduct_Len2(x, y);
        }

        // Vanilla dot product
        double dotSum = 0;
        fixed (float* pxBuffer = x)
        {
            fixed (float* pyBuffer = y)
            {
                float* px = pxBuffer;
                float* pxMax = px + x.Length;
                float* py = pyBuffer;
                while (px < pxMax)
                {
                    // Dot product
                    dotSum += *px * *py;
                    ++px;
                    ++py;
                }

                return dotSum;
            }
        }
    }

    /// <summary>
    /// Unrolled Dot Product for even length arrays. Should typically be twice as fast.
    /// </summary>
    /// <returns>Accumulates to <see cref="double"/>.</returns>
    private static unsafe double DotProduct_Len2(ReadOnlySpan<float> x, ReadOnlySpan<float> y)
    {
        if (x.Length != y.Length)
        {
            throw new ArgumentException("Array lengths must be equal");
        }

        if (x.Length % 4 != 0)
        {
            throw new ArgumentException("Array length must be a multiple of 2");
        }

        double dotSum1 = 0;
        double dotSum2 = 0;
        fixed (float* pxBuffer = x)
        {
            fixed (float* pyBuffer = y)
            {
                float* px = pxBuffer;
                float* pxMax = px + x.Length;
                float* py = pyBuffer;
                while (px < pxMax)
                {
                    // Dot product
                    dotSum1 += *px * *py;
                    dotSum2 += *(px + 1) * *(py + 1);
                    px += 2;
                    py += 2;
                }

                return dotSum1 + dotSum2;
            }
        }
    }

    /// <summary>
    /// Unrolled Dot Product for length of multiple of 4.
    /// </summary>
    /// <returns>Accumulates to <see cref="double"/>.</returns>
    private static unsafe double DotProduct_Len4(ReadOnlySpan<float> x, ReadOnlySpan<float> y)
    {
        if (x.Length != y.Length)
        {
            throw new ArgumentException("Array lengths must be equal");
        }

        if (x.Length % 4 != 0)
        {
            throw new ArgumentException("Array length must be a multiple of 4");
        }

        double dotSum1 = 0;
        double dotSum2 = 0;
        double dotSum3 = 0;
        double dotSum4 = 0;
        fixed (float* pxBuffer = x)
        {
            fixed (float* pyBuffer = y)
            {
                float* px = pxBuffer;
                float* pxMax = px + x.Length;
                float* py = pyBuffer;
                while (px < pxMax)
                {
                    // Dot product
                    dotSum1 += *px * *py;
                    dotSum2 += *(px + 1) * *(py + 1);
                    dotSum3 += *(px + 2) * *(py + 2);
                    dotSum4 += *(px + 3) * *(py + 3);
                    px += 4;
                    py += 4;
                }

                return dotSum1 + dotSum2 + dotSum3 + dotSum4;
            }
        }
    }

    /// <summary>
    /// Unrolled Dot Product for even length arrays. Should typically be twice as fast.
    /// </summary>
    private static unsafe double DotProduct_Len2(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        if (x.Length != y.Length)
        {
            throw new ArgumentException("Array lengths must be equal");
        }

        if (x.Length % 4 != 0)
        {
            throw new ArgumentException("Array length must be a multiple of 2");
        }

        fixed (double* pxBuffer = x)
        {
            fixed (double* pyBuffer = y)
            {
                double dotSum1 = 0;
                double dotSum2 = 0;
                double* px = pxBuffer;
                double* pxMax = px + x.Length;
                double* py = pyBuffer;
                while (px < pxMax)
                {
                    // Dot product
                    dotSum1 += *px * *py;
                    dotSum2 += *(px + 1) * *(py + 1);
                    px += 2;
                    py += 2;
                }

                return dotSum1 + dotSum2;
            }
        }
    }

    /// <summary>
    /// Unrolled Dot Product for length of multiple of 4.
    /// </summary>
    private static unsafe double DotProduct_Len4(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        if (x.Length != y.Length)
        {
            throw new ArgumentException("Array lengths must be equal");
        }

        if (x.Length % 4 != 0)
        {
            throw new ArgumentException("Array length must be a multiple of 4");
        }

        fixed (double* pxBuffer = x)
        {
            fixed (double* pyBuffer = y)
            {
                double dotSum1 = 0;
                double dotSum2 = 0;
                double dotSum3 = 0;
                double dotSum4 = 0;
                double* px = pxBuffer;
                double* pxMax = px + x.Length;
                double* py = pyBuffer;
                while (px < pxMax)
                {
                    // Dot product
                    dotSum1 += *px * *py;
                    dotSum2 += *(px + 1) * *(py + 1);
                    dotSum3 += *(px + 2) * *(py + 2);
                    dotSum4 += *(px + 3) * *(py + 3);
                    px += 4;
                    py += 4;
                }

                return dotSum1 + dotSum2 + dotSum3 + dotSum4;
            }
        }
    }

    #endregion
}
