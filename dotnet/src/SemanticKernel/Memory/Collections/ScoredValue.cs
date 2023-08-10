// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Memory.Collections;

/// <summary>
/// Structure for storing data which can be scored.
/// </summary>
/// <typeparam name="T">Data type.</typeparam>
public readonly struct ScoredValue<T> : IComparable<ScoredValue<T>>, IEquatable<ScoredValue<T>>
{
    public ScoredValue(T item, double score)
    {
        this.Value = item;
        this.Score = score;
    }

    public T Value { get; }
    public double Score { get; }

    public int CompareTo(ScoredValue<T> other)
    {
        var result = this.Score.CompareTo(other.Score);

        if (result == 0 && this.Value is IComparable<T> comparableValue)
        {
            result = comparableValue.CompareTo(other.Value);
        }

        return result;
    }

    public override string ToString()
    {
        return $"{this.Score}, {this.Value}";
    }

    public static explicit operator double(ScoredValue<T> src)
    {
        return src.Score;
    }

    public static explicit operator T(ScoredValue<T> src)
    {
        return src.Value;
    }

    public static implicit operator ScoredValue<T>(KeyValuePair<T, double> src)
    {
        return new ScoredValue<T>(src.Key, src.Value);
    }

    public override bool Equals(object obj)
    {
        return (obj is ScoredValue<T> other) && this.Equals(other);
    }

    public bool Equals(ScoredValue<T> other)
    {
        return this.CompareTo(other) == 0;
    }

    public override int GetHashCode()
    {
        return HashCode.Combine(this.Value, this.Score);
    }

    public static bool operator ==(ScoredValue<T> left, ScoredValue<T> right)
    {
        return left.Equals(right);
    }

    public static bool operator !=(ScoredValue<T> left, ScoredValue<T> right)
    {
        return !(left == right);
    }

    public static bool operator <(ScoredValue<T> left, ScoredValue<T> right)
    {
        return left.CompareTo(right) < 0;
    }

    public static bool operator <=(ScoredValue<T> left, ScoredValue<T> right)
    {
        return left.CompareTo(right) <= 0;
    }

    public static bool operator >(ScoredValue<T> left, ScoredValue<T> right)
    {
        return left.CompareTo(right) > 0;
    }

    public static bool operator >=(ScoredValue<T> left, ScoredValue<T> right)
    {
        return left.CompareTo(right) >= 0;
    }

    internal static ScoredValue<T> Min()
    {
        return new ScoredValue<T>(default!, double.MinValue);
    }
}
