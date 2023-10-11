// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Numerics;
using System.Runtime.InteropServices;

namespace Microsoft.SemanticKernel.AI.Embeddings.VectorOperations;

/// <summary>
/// Extension methods for vector division.
/// </summary>
[Obsolete("Numerical operations will be removed in a future release. Use System.Numerics.Tensors.TensorPrimitives instead.")]
[EditorBrowsable(EditorBrowsableState.Never)]
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
            throw new NotSupportedException();
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
            float* pxEnd = px + x.Length;

            if (Vector.IsHardwareAccelerated &&
                x.Length >= Vector<float>.Count)
            {
                Vector<float> divisorVec = new(divisor);
                float* pxOneVectorFromEnd = pxEnd - Vector<float>.Count;
                do
                {
                    *(Vector<float>*)px /= divisorVec;
                    px += Vector<float>.Count;
                } while (px <= pxOneVectorFromEnd);
            }

            while (px < pxEnd)
            {
                *px /= divisor;
                px++;
            }
        }
    }

    private static unsafe void DivideByInPlaceImplementation(Span<double> x, double divisor)
    {
        fixed (double* pxBuffer = x)
        {
            double* px = pxBuffer;
            double* pxEnd = px + x.Length;

            if (Vector.IsHardwareAccelerated &&
                x.Length >= Vector<double>.Count)
            {
                Vector<double> divisorVec = new(divisor);
                double* pxOneVectorFromEnd = pxEnd - Vector<double>.Count;
                do
                {
                    *(Vector<double>*)px /= divisorVec;
                    px += Vector<double>.Count;
                } while (px <= pxOneVectorFromEnd);
            }

            while (px < pxEnd)
            {
                *px /= divisor;
                px++;
            }
        }
    }

    #endregion
}
