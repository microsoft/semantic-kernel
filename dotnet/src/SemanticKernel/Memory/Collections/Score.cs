// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;

namespace Microsoft.SemanticKernel.Memory.Collections;

/// <summary>
/// Structure for storing score value.
/// </summary>
public readonly struct Score : IComparable<Score>, IEquatable<Score>
{
    /// <summary>
    /// Gets the value of the score.
    /// </summary>
    public double Value { get; }

    /// <summary>
    /// Initializes a new instance of the Score struct with the specified value.
    /// </summary>
    /// <param name="value">The value of the score.</param>
    public Score(double value)
    {
        this.Value = value;
    }

    internal static Score Min => double.MinValue;

    /// <summary>
    /// Implicitly converts a double to a Score.
    /// </summary>
    /// <param name="score">The double value to convert.</param>
    public static implicit operator Score(double score)
    {
        return new Score(score);
    }

    /// <summary>
    /// Implicitly converts a Score to a double.
    /// </summary>
    /// <param name="src">The Score value to convert.</param>
    public static implicit operator double(Score src)
    {
        return src.Value;
    }

    /// <inheritdoc/>
    public int CompareTo(Score other)
    {
        return this.Value.CompareTo(other.Value);
    }

    /// <inheritdoc/>
    public override string ToString()
    {
        return this.Value.ToString(CultureInfo.InvariantCulture.NumberFormat);
    }

    /// <inheritdoc/>
    public override bool Equals(object obj)
    {
        return (obj is Score other) && this.Equals(other);
    }

    /// <inheritdoc/>
    public bool Equals(Score other)
    {
        return this.Value == other.Value;
    }

    /// <inheritdoc/>
    public override int GetHashCode()
    {
        return HashCode.Combine(this.Value);
    }

    /// <summary>
    /// Determines whether two Score instances are equal.
    /// </summary>
    /// <param name="left">The first Score instance.</param>
    /// <param name="right">The second Score instance.</param>
    /// <returns>True if the instances are equal, false otherwise.</returns>
    public static bool operator ==(Score left, Score right)
    {
        return left.Equals(right);
    }

    /// <summary>
    /// Determines whether two Score instances are not equal.
    /// </summary>
    /// <param name="left">The first Score instance.</param>
    /// <param name="right">The second Score instance.</param>
    /// <returns>True if the instances are not equal, false otherwise.</returns>
    public static bool operator !=(Score left, Score right)
    {
        return !(left == right);
    }

    /// <summary>
    /// Determines whether the left Score instance is less than the right Score instance.
    /// </summary>
    /// <param name="left">The left Score instance.</param>
    /// <param name="right">The right Score instance.</param>
    /// <returns>True if the left instance is less than the right instance, false otherwise.</returns>
    public static bool operator <(Score left, Score right)
    {
        return left.CompareTo(right) < 0;
    }

    /// <summary>
    /// Determines whether the left Score instance is less than or equal to the right Score instance.
    /// </summary>
    /// <param name="left">The left Score instance.</param>
    /// <param name="right">The right Score instance.</param>
    /// <returns>True if the left instance is less than or equal to the right instance, false otherwise.</returns>
    public static bool operator <=(Score left, Score right)
    {
        return left.CompareTo(right) <= 0;
    }

    /// <summary>
    /// Determines whether the left Score instance is greater than the right Score instance.
    /// </summary>
    /// <param name="left">The left Score instance.</param>
    /// <param name="right">The right Score instance.</param>
    /// <returns>True if the left instance is greater than the right instance, false otherwise.</returns>
    public static bool operator >(Score left, Score right)
    {
        return left.CompareTo(right) > 0;
    }

    /// <summary>
    /// Determines whether the left Score instance is greater than or equal to the right Score instance.
    /// </summary>
    /// <param name="left">The left Score instance.</param>
    /// <param name="right">The right Score instance.</param>
    /// <returns>True if the left instance is greater than or equal to the right instance, false otherwise.</returns>
    public static bool operator >=(Score left, Score right)
    {
        return left.CompareTo(right) >= 0;
    }
}
