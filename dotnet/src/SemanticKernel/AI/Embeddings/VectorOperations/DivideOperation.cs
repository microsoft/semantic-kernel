// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Runtime.InteropServices;

namespace Microsoft.SemanticKernel.AI.Embeddings.VectorOperations;

/// <summary>
/// Extension methods for vector division.
/// </summary>
public static class DivideOperation
{
    /// <summary>
    /// Divide all elements of <see cref="Span{T}"/> of type <typeparamref name="TNumber"/> by <paramref name="divisor"/>.
    /// </summary>
    /// <typeparam name="TNumber">The unmanaged data type (<see cref="float"/>, <see cref="double"/> currently supported).</typeparam>
    /// <param name="span">The data vector</param>
    /// <param name="divisor">The value to divide by.</param>
    public static void DivideByInPlace<TNumber>(this Span<TNumber> span, double divisor)
        where TNumber : unmanaged
    {
        if (typeof(TNumber) == typeof(float))
        {
            Span<float> floatSpan = MemoryMarshal.Cast<TNumber, float>(span);
            DivideByInPlaceImplementation(floatSpan, (float)divisor);
        }
        else if (typeof(TNumber) == typeof(double))
        {
            Span<double> doubleSpan = MemoryMarshal.Cast<TNumber, double>(span);
            DivideByInPlaceImplementation(doubleSpan, divisor);
        }
        else
        {
            SupportedTypes.ThrowTypeNotSupported<TNumber>();
        }
    }

    /// <summary>
    /// Divide all elements of an array of type <typeparamref name="TNumber"/> by <paramref name="divisor"/>.
    /// </summary>
    /// <typeparam name="TNumber">The unmanaged data type (<see cref="float"/>, <see cref="double"/> currently supported).</typeparam>
    /// <param name="vector">The data vector</param>
    /// <param name="divisor">The value to divide by.</param>
    public static void DivideByInPlace<TNumber>(this TNumber[] vector, double divisor)
        where TNumber : unmanaged
    {
        vector.AsSpan().DivideByInPlace(divisor);
    }

    #region private ================================================================================

    private static unsafe void DivideByInPlaceImplementation(Span<float> x, float divisor)
    {
        fixed (float* pxBuffer = x)
        {
            float* px = pxBuffer;
            float* pxMax = px + x.Length;
            while (px < pxMax)
            {
                *px = *px / divisor;
                px++;
            }
        }
    }

    private static unsafe void DivideByInPlaceImplementation(Span<double> x, double divisor)
    {
        fixed (double* pxBuffer = x)
        {
            double* px = pxBuffer;
            double* pxMax = px + x.Length;
            while (px < pxMax)
            {
                *px = *px / divisor;
                px++;
            }
        }
    }

    #endregion
}
