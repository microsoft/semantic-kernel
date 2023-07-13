// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.AI.Embeddings.VectorOperations;

namespace Microsoft.SemanticKernel.AI.Embeddings;

/// <summary>
/// A view of a vector that allows for low-level, optimized, read-only mathematical operations.
/// </summary>
/// <typeparam name="TEmbedding">The unmanaged data type (<see cref="float"/>, <see cref="double"/> currently supported).</typeparam>
public readonly ref struct EmbeddingReadOnlySpan<TEmbedding>
    where TEmbedding : unmanaged
{
    /// <summary>
    /// Constructor
    /// </summary>
    /// <param name="vector">A a vector of contiguous, unmanaged data.</param>
    /// <param name="isNormalized">Indicates whether the data was pre-normalized.</param>
    /// <remarks>
    /// This does not verify that the data is normalized, nor make any guarantees that it remains so,
    /// as the data can be modified at its source. The <paramref name="isNormalized"/> parameter simply
    /// directs these operations to perform faster if the data is known to be normalized.
    /// </remarks>
    public EmbeddingReadOnlySpan(ReadOnlySpan<TEmbedding> vector, bool isNormalized = false)
    {
        if (!Embedding.IsSupported<TEmbedding>())
        {
            EmbeddingSpan<TEmbedding>.ThrowTEmbeddingNotSupported();
        }

        this.ReadOnlySpan = vector;
        this.IsNormalized = isNormalized;
    }

    /// <summary>
    /// Constructor
    /// </summary>
    /// <param name="vector">A vector of contiguous, unmanaged data.</param>
    /// <param name="isNormalized">Indicates whether the data was pre-normalized.</param>
    /// <remarks>
    /// This does not verify that the data is normalized, nor make any guarantees that it remains so,
    /// as the data can be modified at its source. The <paramref name="isNormalized"/> parameter simply
    /// directs these operations to perform faster if the data is known to be normalized.
    /// </remarks>
    public EmbeddingReadOnlySpan(TEmbedding[] vector, bool isNormalized = false)
        : this(vector.AsReadOnlySpan(), isNormalized)
    {
    }

    /// <summary>
    /// Constructor
    /// </summary>
    /// <param name="span">A vector of contiguous, unmanaged data.</param>
    /// <param name="isNormalized">Indicates whether the data was pre-normalized.</param>
    /// <remarks>
    /// This does not verify that the data is normalized, nor make any guarantees that it remains so,
    /// as the data can be modified at its source. The <paramref name="isNormalized"/> parameter simply
    /// directs these operations to perform faster if the data is known to be normalized.
    /// </remarks>
    public EmbeddingReadOnlySpan(EmbeddingSpan<TEmbedding> span, bool isNormalized = false)
        : this(span.Span.AsReadOnlySpan(), isNormalized)
    {
    }

    /// <summary>
    /// Gets the underlying <see cref="ReadOnlySpan{T}"/> of unmanaged data.
    /// </summary>
    public ReadOnlySpan<TEmbedding> ReadOnlySpan { get; }

    /// <summary>
    /// True if the data was specified to be normalized at construction.
    /// </summary>
    public bool IsNormalized { get; }

    /// <summary>
    /// Calculates the dot product of this vector with another.
    /// </summary>
    /// <param name="other">The second vector.</param>
    /// <returns>The dot product as a <see cref="double"/></returns>
    public double Dot(EmbeddingReadOnlySpan<TEmbedding> other)
    {
        return this.ReadOnlySpan.DotProduct(other.ReadOnlySpan);
    }

    /// <summary>
    /// Calculates the Euclidean length of this vector.
    /// </summary>
    /// <returns>The Euclidean length as a <see cref="double"/></returns>
    public double EuclideanLength()
    {
        return this.ReadOnlySpan.EuclideanLength();
    }

    /// <summary>
    /// Calculates the cosine similarity of this vector with another.
    /// </summary>
    /// <param name="other">The second vector.</param>
    /// <returns>The cosine similarity as a <see cref="double"/>.</returns>
    public double CosineSimilarity(EmbeddingReadOnlySpan<TEmbedding> other)
    {
        if (this.IsNormalized && other.IsNormalized)
        {
            // Because Normalized embeddings already have normalized lengths, cosine similarity is much
            // faster - just a dot product. Don't have to compute lengths, square roots, etc.
            return this.Dot(other);
        }

        return this.ReadOnlySpan.CosineSimilarity(other.ReadOnlySpan);
    }
}
