// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> origin/main
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Memory;
=======
<<<<<<< head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Memory;
<<<<<<< main
=======
=======
=======
>>>>>>> origin/main

#pragma warning disable IDE0130 // Namespace does not match folder structure
namespace Microsoft.SemanticKernel.Memory.Collections;
#pragma warning restore IDE0130 // Namespace does not match folder structure
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main

/// <summary>
/// Structure for storing data which can be scored.
/// </summary>
/// <typeparam name="T">Data type.</typeparam>
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< HEAD
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> origin/main
internal readonly struct ScoredValue<T>(T item, double score) : IComparable<ScoredValue<T>>, IEquatable<ScoredValue<T>>
{
    /// <summary>
    /// Gets the value of the scored item.
    /// </summary>
    public T Value { get; } = item;
    /// <summary>
    /// Gets the score of the item.
    /// </summary>
    public double Score { get; } = score;

    /// <summary>
    /// Compares the current instance with another instance of <see cref="ScoredValue{T}"/>.
    /// </summary>
    /// <param name="other">The other instance of <see cref="ScoredValue{T}"/> to compare with.</param>
    /// <returns>A value indicating the relative order of the instances.</returns>
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
public readonly struct ScoredValue<T> : IComparable<ScoredValue<T>>, IEquatable<ScoredValue<T>>
{
    public ScoredValue(T item, double score)
    {
        this.Value = item;
        this.Score = score;
    }

    public T Value { get; }
    public Score Score { get; }

>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
    public int CompareTo(ScoredValue<T> other)
    {
        return this.Score.CompareTo(other.Score);
    }

<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> origin/main
    /// <summary>
    /// Returns a string representation of the current instance.
    /// </summary>
    /// <returns>A string representation of the current instance.</returns>
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> origin/main
    public override string ToString()
    {
        return $"{this.Score}, {this.Value}";
    }

<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> origin/main
    /// <summary>
    /// Converts the score of the current instance to a double.
    /// </summary>
    /// <param name="src">The current instance of <see cref="ScoredValue{T}"/>.</param>
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> origin/main
    public static explicit operator double(ScoredValue<T> src)
    {
        return src.Score;
    }

<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> origin/main
    /// <summary>
    /// Converts the value of the current instance to the specified type.
    /// </summary>
    /// <param name="src">The current instance of <see cref="ScoredValue{T}"/>.</param>
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> origin/main
    public static explicit operator T(ScoredValue<T> src)
    {
        return src.Value;
    }

<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> origin/main
    /// <summary>
    /// Converts a <see cref="KeyValuePair{TKey, TValue}"/> to a <see cref="ScoredValue{T}"/>.
    /// </summary>
    /// <param name="src">The <see cref="KeyValuePair{TKey, TValue}"/> to convert.</param>
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> origin/main
    public static implicit operator ScoredValue<T>(KeyValuePair<T, double> src)
    {
        return new ScoredValue<T>(src.Key, src.Value);
    }

<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    /// <inheritdoc/>
    public override bool Equals([NotNullWhen(true)] object? obj)
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    /// <inheritdoc/>
    public override bool Equals([NotNullWhen(true)] object? obj)
=======
    public override bool Equals(object obj)
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
    /// <inheritdoc/>
    public override bool Equals([NotNullWhen(true)] object? obj)
=======
    public override bool Equals(object obj)
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> origin/main
    {
        return (obj is ScoredValue<T> other) && this.Equals(other);
    }

<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> origin/main
    /// <summary>
    /// Determines whether the current instance is equal to another instance of <see cref="ScoredValue{T}"/>.
    /// </summary>
    /// <param name="other">The other instance of <see cref="ScoredValue{T}"/> to compare with.</param>
    /// <returns>True if the instances are equal, false otherwise.</returns>
    public bool Equals(ScoredValue<T> other)
    {
        return EqualityComparer<T>.Default.Equals(this.Value, other.Value) &&
                this.Score.Equals(other.Score);
    }

    /// <inheritdoc/>
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
    public bool Equals(ScoredValue<T> other)
    {
        return EqualityComparer<T>.Default.Equals(other.Value) &&
               this.Score.Equals(other.Score);
    }

>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
    public override int GetHashCode()
    {
        return HashCode.Combine(this.Value, this.Score);
    }

<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    /// <summary>
    /// Determines whether two instances of <see cref="ScoredValue{T}"/> are equal.
    /// </summary>
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
<<<<<<< HEAD
    /// <summary>
    /// Determines whether two instances of <see cref="ScoredValue{T}"/> are equal.
    /// </summary>
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
    public static bool operator ==(ScoredValue<T> left, ScoredValue<T> right)
    {
        return left.Equals(right);
    }

<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> origin/main
    /// <summary>
    /// Determines whether two instances of <see cref="ScoredValue{T}"/> are not equal.
    /// </summary>
=======
<<<<<<< head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    /// <summary>
    /// Determines whether two instances of <see cref="ScoredValue{T}"/> are not equal.
    /// </summary>
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> origin/main
    public static bool operator !=(ScoredValue<T> left, ScoredValue<T> right)
    {
        return !(left == right);
    }

<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    /// <summary>
    /// Determines whether the left instance of <see cref="ScoredValue{T}"/> is less than the right instance.
    /// </summary>
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
<<<<<<< HEAD
    /// <summary>
    /// Determines whether the left instance of <see cref="ScoredValue{T}"/> is less than the right instance.
    /// </summary>
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
    public static bool operator <(ScoredValue<T> left, ScoredValue<T> right)
    {
        return left.CompareTo(right) < 0;
    }

<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> origin/main
    /// <summary>
    /// Determines whether the left instance of <see cref="ScoredValue{T}"/> is less than or equal to the right instance.
    /// </summary>
=======
<<<<<<< head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    /// <summary>
    /// Determines whether the left instance of <see cref="ScoredValue{T}"/> is less than or equal to the right instance.
    /// </summary>
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> origin/main
    public static bool operator <=(ScoredValue<T> left, ScoredValue<T> right)
    {
        return left.CompareTo(right) <= 0;
    }

<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    /// <summary>
    /// Determines whether the left instance of <see cref="ScoredValue{T}"/> is greater than the right instance.
    /// </summary>
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
<<<<<<< HEAD
    /// <summary>
    /// Determines whether the left instance of <see cref="ScoredValue{T}"/> is greater than the right instance.
    /// </summary>
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
    public static bool operator >(ScoredValue<T> left, ScoredValue<T> right)
    {
        return left.CompareTo(right) > 0;
    }

<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> origin/main
    /// <summary>
    /// Determines whether the left instance of <see cref="ScoredValue{T}"/> is greater than or equal to the right instance.
    /// </summary>
=======
<<<<<<< head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    /// <summary>
    /// Determines whether the left instance of <see cref="ScoredValue{T}"/> is greater than or equal to the right instance.
    /// </summary>
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> origin/main
    public static bool operator >=(ScoredValue<T> left, ScoredValue<T> right)
    {
        return left.CompareTo(right) >= 0;
    }

<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> origin/main
    /// <summary>
    /// Returns the minimum possible value of a <see cref="ScoredValue{T}"/>.
    /// </summary>
    internal static ScoredValue<T> Min()
    {
        return new ScoredValue<T>(default!, double.MinValue);
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
    internal static ScoredValue<T> Min()
    {
        return new ScoredValue<T>(default!, Score.Min);
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
    }
}
