// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Numerics;
using System.Runtime.InteropServices;

namespace Microsoft.SemanticKernel.AI.Embeddings.VectorOperations;

/// <summary>
/// Extension methods to multiply a vector by a scalar.
/// </summary>
[Obsolete("Numerical operations will be removed in a future release. Use System.Numerics.Tensors.TensorPrimitives instead.")]
[EditorBrowsable(EditorBrowsableState.Never)]
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
            throw new NotSupportedException();
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
            float* pxEnd = px + x.Length;

            if (Vector.IsHardwareAccelerated &&
                x.Length >= Vector<float>.Count)
            {
                Vector<float> multiplierVec = new(multiplier);
                float* pxOneVectorFromEnd = pxEnd - Vector<float>.Count;
                do
                {
                    *(Vector<float>*)px *= multiplierVec;
                    px += Vector<float>.Count;
                } while (px <= pxOneVectorFromEnd);
            }

            while (px < pxEnd)
            {
                *px *= multiplier;
                px++;
            }
        }
    }

    private static unsafe void MultiplyByInPlaceImplementation(Span<double> x, double multiplier)
    {
        fixed (double* pxBuffer = x)
        {
            double* px = pxBuffer;
            double* pxEnd = px + x.Length;

            if (Vector.IsHardwareAccelerated &&
                x.Length >= Vector<double>.Count)
            {
                Vector<double> multiplierVec = new(multiplier);
                double* pxOneVectorFromEnd = pxEnd - Vector<double>.Count;
                do
                {
                    *(Vector<double>*)px *= multiplierVec;
                    px += Vector<double>.Count;
                } while (px <= pxOneVectorFromEnd);
            }

            while (px < pxEnd)
            {
                *px *= multiplier;
                px++;
            }
        }
    }

    #endregion
}
