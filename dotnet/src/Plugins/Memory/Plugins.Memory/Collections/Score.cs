// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;

namespace Microsoft.SemanticKernel.Plugins.Memory.Collections;

/// <summary>
/// Structure for storing score value.
/// </summary>
public readonly struct Score : IComparable<Score>, IEquatable<Score>
{
    public double Value { get; }

    public Score(double value)
    {
        this.Value = value;
    }

    internal static Score Min => double.MinValue;

    public static implicit operator Score(double score)
    {
        return new Score(score);
    }

    public static implicit operator double(Score src)
    {
        return src.Value;
    }

    public int CompareTo(Score other)
    {
        return this.Value.CompareTo(other.Value);
    }

    public override string ToString()
    {
        return this.Value.ToString(CultureInfo.InvariantCulture.NumberFormat);
    }

    public override bool Equals(object obj)
    {
        return obj is Score other && this.Equals(other);
    }

    public bool Equals(Score other)
    {
        return this.Value == other.Value;
    }

    public override int GetHashCode()
    {
        return HashCode.Combine(this.Value);
    }

    public static bool operator ==(Score left, Score right)
    {
        return left.Equals(right);
    }

    public static bool operator !=(Score left, Score right)
    {
        return !(left == right);
    }

    public static bool operator <(Score left, Score right)
    {
        return left.CompareTo(right) < 0;
    }

    public static bool operator <=(Score left, Score right)
    {
        return left.CompareTo(right) <= 0;
    }

    public static bool operator >(Score left, Score right)
    {
        return left.CompareTo(right) > 0;
    }

    public static bool operator >=(Score left, Score right)
    {
        return left.CompareTo(right) >= 0;
    }
}
