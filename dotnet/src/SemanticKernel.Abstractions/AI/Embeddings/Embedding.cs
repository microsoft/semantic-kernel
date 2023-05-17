// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.AI.Embeddings;

/// <summary>
/// Represents a strongly typed vector of numeric data.
/// </summary>
/// <typeparam name="TEmbedding"></typeparam>
public readonly struct Embedding<TEmbedding> : IEquatable<Embedding<TEmbedding>>
    where TEmbedding : unmanaged
{
    /// <summary>
    /// An empty <see cref="Embedding{TEmbedding}"/> instance.
    /// </summary>
    [SuppressMessage("Design", "CA1000:Do not declare static members on generic types", Justification = "Static empty struct instance.")]
    public static Embedding<TEmbedding> Empty
    {
        get
        {
            if (!IsSupported)
            {
                ThrowNotSupportedEmbedding();
            }

            return default;
        }
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="Embedding{TEmbedding}"/> class that contains numeric elements copied from the specified collection.
    /// </summary>
    /// <param name="vector">The source data.</param>
    /// <exception cref="ArgumentException">An unsupported type is used as TEmbedding.</exception>
    /// <exception cref="ArgumentNullException">A <c>null</c> vector is passed in.</exception>
    [JsonConstructor]
    public Embedding(IEnumerable<TEmbedding> vector)
    {
        Verify.NotNull(vector);

        if (!IsSupported)
        {
            ThrowNotSupportedEmbedding();
        }

        // Create a local, protected copy
        this._vector = vector.ToArray();
    }

    private static void ThrowNotSupportedEmbedding()
    {
        throw new NotSupportedException($"Embeddings do not support type '{typeof(TEmbedding).Name}'. Supported types include: [ Single, Double ]");
    }

    /// <summary>
    /// Gets the vector as an <see cref="IEnumerable{TEmbedding}"/>
    /// </summary>
    [JsonPropertyName("vector")]
    public IEnumerable<TEmbedding> Vector => this._vector ?? Array.Empty<TEmbedding>();

    /// <summary>
    /// Gets a value that indicates whether <typeparamref name="TEmbedding"/> is supported.
    /// </summary>
    [JsonIgnore]
    [SuppressMessage("Design", "CA1000:Do not declare static members on generic types", Justification = "Following 'IsSupported' pattern of System.Numerics.")]
    public static bool IsSupported => typeof(TEmbedding) == typeof(float) || typeof(TEmbedding) == typeof(double);

    /// <summary>
    /// <c>true</c> if the vector is empty.
    /// </summary>
    [JsonIgnore]
    public bool IsEmpty
    {
        get
        {
            TEmbedding[]? vector = this._vector;
            return vector is null || vector.Length == 0;
        }
    }

    /// <summary>
    /// The number of elements in the vector.
    /// </summary>
    [JsonIgnore]
    public int Count => this._vector?.Length ?? 0;

    /// <summary>
    /// Gets the vector as a read-only span.
    /// </summary>
    public ReadOnlySpan<TEmbedding> AsReadOnlySpan()
    {
        return new(this._vector);
    }

    /// <summary>
    /// Serves as the default hash function.
    /// </summary>
    /// <returns>A hash code for the current object.</returns>
    public override int GetHashCode()
    {
        return this._vector?.GetHashCode() ?? 0;
    }

    /// <summary>
    /// Determines whether two object instances are equal.
    /// </summary>
    /// <param name="obj">The object to compare with the current object.</param>
    /// <returns><c>true</c> if the specified object is equal to the current object; otherwise, <c>false</c>.</returns>
    public override bool Equals(object obj)
    {
        return obj is Embedding<TEmbedding> other && this.Equals(other);
    }

    /// <summary>
    /// Compares two embeddings for equality.
    /// </summary>
    /// <param name="other">The <see cref="Embedding{TEmbedding}"/> to compare with the current object.</param>
    /// <returns>><c>true</c> if the specified object is equal to the current object; otherwise, <c>false</c>.</returns>
    public bool Equals(Embedding<TEmbedding> other)
    {
        TEmbedding[]? vector = this._vector;
        return vector is null ? other._vector is null : vector.Equals(other._vector);
    }

    /// <summary>
    /// Compares two embeddings for equality.
    /// </summary>
    /// <param name="left">The left <see cref="Embedding{TEmbedding}"/>.</param>
    /// <param name="right">The right <see cref="Embedding{TEmbedding}"/>.</param>
    /// <returns><c>true</c> if the embeddings contain identical data; <c>false</c> otherwise</returns>
    public static bool operator ==(Embedding<TEmbedding> left, Embedding<TEmbedding> right)
    {
        return left.Equals(right);
    }

    /// <summary>
    /// Compares two embeddings for inequality.
    /// </summary>
    /// <param name="left">The left <see cref="Embedding{TEmbedding}"/>.</param>
    /// <param name="right">The right <see cref="Embedding{TEmbedding}"/>.</param>
    /// <returns><c>true</c> if the embeddings do not contain identical data; <c>false</c> otherwise</returns>
    public static bool operator !=(Embedding<TEmbedding> left, Embedding<TEmbedding> right)
    {
        return !(left == right);
    }

    /// <summary>
    /// Implicit creation of an <see cref="Embedding{TEmbedding}"/> object from an array of data.>
    /// </summary>
    /// <param name="vector">An array of data.</param>
    public static explicit operator Embedding<TEmbedding>(TEmbedding[] vector)
    {
        return new Embedding<TEmbedding>(vector);
    }

    /// <summary>
    /// Implicit creation of an array of type <typeparamref name="TEmbedding"/> from a <see cref="Embedding{TEmbedding}"/>.
    /// </summary>
    /// <param name="embedding">Source <see cref="Embedding{TEmbedding}"/>.</param>
    /// <remarks>A clone of the underlying data.</remarks>
    public static explicit operator TEmbedding[](Embedding<TEmbedding> embedding)
    {
        return embedding._vector is null ? Array.Empty<TEmbedding>() : (TEmbedding[])embedding._vector.Clone();
    }

    /// <summary>
    /// Implicit creation of an <see cref="ReadOnlySpan{T}"/> from a <see cref="Embedding{TEmbedding}"/>.
    /// </summary>
    /// <param name="embedding">Source <see cref="Embedding{TEmbedding}"/>.</param>
    /// <remarks>A clone of the underlying data.</remarks>
    public static explicit operator ReadOnlySpan<TEmbedding>(Embedding<TEmbedding> embedding)
    {
        return embedding.AsReadOnlySpan();
    }

    #region private ================================================================================

    private readonly TEmbedding[]? _vector;

    #endregion
}

/// <summary>
/// Static class containing the supported types for <see cref="Embedding{TEmbedding}"/>.
/// </summary>
public static class Embedding
{
    /// <summary>
    /// Types supported by the <see cref="Embedding{TEmbedding}"/> struct.
    /// </summary>
    public static readonly Type[] SupportedTypes = { typeof(float), typeof(double) };
}
