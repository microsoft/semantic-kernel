// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.AI.Embeddings.VectorOperations;

namespace Microsoft.SemanticKernel.AI.Embeddings;

/// <summary>
/// A view of a vector that allows for low-level, optimized, read-write mathematical operations.
/// </summary>
/// <typeparam name="TEmbedding">The unmanaged data type (<see cref="float"/>, <see cref="double"/> currently supported).</typeparam>
public readonly ref struct EmbeddingSpan<TEmbedding>
    where TEmbedding : unmanaged
{
    /// <summary>
    /// Constructor
    /// </summary>
    /// <param name="vector">A a vector of contiguous, unmanaged data.</param>
    public EmbeddingSpan(Span<TEmbedding> vector)
    {
        if (!Embedding.IsSupported<TEmbedding>())
        {
            ThrowTEmbeddingNotSupported();
        }

        this.Span = vector;
    }

    internal static void ThrowTEmbeddingNotSupported() =>
        throw new NotSupportedException($"Embeddings do not support type '{typeof(TEmbedding).Name}'. Supported types include: [ Single, Double ]");

    /// <summary>
    /// Constructor
    /// </summary>
    /// <param name="vector">A vector of contiguous, unmanaged data.</param>
    public EmbeddingSpan(TEmbedding[] vector)
        : this(vector.AsSpan())
    {
    }

    /// <summary>
    /// Gets the underlying <see cref="Span{T}"/> of unmanaged data.
    /// </summary>
    public Span<TEmbedding> Span { get; }

    /// <summary>
    /// Normalizes the underlying vector in-place, such that the Euclidean length is 1.
    /// </summary>
    /// <returns>A <see cref="EmbeddingReadOnlySpan{TEmbedding}"/> with 'IsNormalized' set to true.</returns>
    public EmbeddingReadOnlySpan<TEmbedding> Normalize()
    {
        this.Span.NormalizeInPlace();
        return new EmbeddingReadOnlySpan<TEmbedding>(this.Span, true);
    }

    /// <summary>
    /// Calculates the dot product of this vector with another.
    /// </summary>
    /// <param name="other">The second vector.</param>
    /// <returns>The dot product as a <see cref="double"/></returns>
    public double Dot(EmbeddingSpan<TEmbedding> other)
    {
        return this.Span.DotProduct(other.Span);
    }

    /// <summary>
    /// Calculates the Euclidean length of this vector.
    /// </summary>
    /// <returns>The Euclidean length as a <see cref="double"/></returns>
    public double EuclideanLength()
    {
        return this.Span.EuclideanLength();
    }

    /// <summary>
    /// Calculates the cosine similarity of this vector with another.
    /// </summary>
    /// <param name="other">The second vector.</param>
    /// <returns>The cosine similarity as a <see cref="double"/>.</returns>
    /// <remarks>This operation can be performed much faster if the vectors are known to be normalized, by
    /// converting to a <see cref="EmbeddingReadOnlySpan{TEmbedding}"/> with constructor parameter 'isNormalized' true.</remarks>
    public double CosineSimilarity(EmbeddingSpan<TEmbedding> other)
    {
        return this.Span.CosineSimilarity(other.Span);
    }
}
