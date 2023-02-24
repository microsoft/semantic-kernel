// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Runtime.InteropServices;

namespace Microsoft.SemanticKernel.AI.Embeddings.VectorOperations;

/// <summary>
/// Extension methods to multiply a vector by a scalar.
/// </summary>
public static class MultiplyOperation
{
    /// <summary>
    /// Multiplies all elements of a vector by the scalar <paramref name="multiplier"/> in-place.
    /// Does not allocate new memory.
    /// </summary>
    /// <typeparam name="TNumber">The unmanaged data type (<see cref="float"/>, <see cref="double"/> currently supported).</typeparam>
    /// <param name="vector">The input vector.</param>
    /// <param name="multiplier">The scalar.</param>
    public static void MultiplyByInPlace<TNumber>(this Span<TNumber> vector, double multiplier)
        where TNumber : unmanaged
    {
        if (typeof(TNumber) == typeof(float))
        {
            Span<float> floatSpan = MemoryMarshal.Cast<TNumber, float>(vector);
            MultiplyByInPlaceImplementation(floatSpan, (float)multiplier);
        }
        else if (typeof(TNumber) == typeof(double))
        {
            Span<double> doubleSpan = MemoryMarshal.Cast<TNumber, double>(vector);
            MultiplyByInPlaceImplementation(doubleSpan, multiplier);
        }
        else
        {
            SupportedTypes.ThrowTypeNotSupported(typeof(TNumber));
        }
    }

    /// <summary>
    /// Multiplies all elements of a vector by the scalar <paramref name="multiplier"/> in-place.
    /// Does not allocate new memory.
    /// </summary>
    /// <typeparam name="TNumber">The unmanaged data type (<see cref="float"/>, <see cref="double"/> currently supported).</typeparam>
    /// <param name="vector">The input vector.</param>
    /// <param name="multiplier">The scalar.</param>
    public static void MultiplyByInPlace<TNumber>(this TNumber[] vector, double multiplier)
        where TNumber : unmanaged
    {
        vector.AsSpan().MultiplyByInPlace(multiplier);
    }

    #region private ================================================================================

    private static unsafe void MultiplyByInPlaceImplementation(Span<float> x, float multiplier)
    {
        fixed (float* pxBuffer = x)
        {
            float* px = pxBuffer;
            float* pxMax = px + x.Length;
            while (px < pxMax)
            {
                *px = *px * multiplier;
                px++;
            }
        }
    }

    private static unsafe void MultiplyByInPlaceImplementation(Span<double> x, double multiplier)
    {
        fixed (double* pxBuffer = x)
        {
            double* px = pxBuffer;
            double* pxMax = px + x.Length;
            while (px < pxMax)
            {
                *px = *px * multiplier;
                px++;
            }
        }
    }

    #endregion
}
