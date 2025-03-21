// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;

#pragma warning disable IDE0009 // use this directive
#pragma warning disable CA1716

// Original source from
// https://raw.githubusercontent.com/dotnet/extensions/main/src/Shared/EmptyCollections/EmptyReadOnlyList.cs

[System.Diagnostics.CodeAnalysis.ExcludeFromCodeCoverage]
[System.Diagnostics.CodeAnalysis.SuppressMessage("Design", "CA1001:Types that own disposable fields should be disposable", Justification = "Static field, lifetime matches the process")]
internal sealed class EmptyReadOnlyList<T> : IReadOnlyList<T>, ICollection<T>
{
    public static readonly EmptyReadOnlyList<T> Instance = new();
    private readonly Enumerator _enumerator = new();

    public IEnumerator<T> GetEnumerator() => _enumerator;
    IEnumerator IEnumerable.GetEnumerator() => _enumerator;
    public int Count => 0;
    public T this[int index] => throw new ArgumentOutOfRangeException(nameof(index));

    void ICollection<T>.CopyTo(T[] array, int arrayIndex)
    {
        // nop
    }

    bool ICollection<T>.Contains(T item) => false;
    bool ICollection<T>.IsReadOnly => true;
    void ICollection<T>.Add(T item) => throw new NotSupportedException();
    bool ICollection<T>.Remove(T item) => false;

    void ICollection<T>.Clear()
    {
        // nop
    }

    internal sealed class Enumerator : IEnumerator<T>
    {
        public void Dispose()
        {
            // nop
        }

        public void Reset()
        {
            // nop
        }

        public bool MoveNext() => false;
        public T Current => throw new InvalidOperationException();
        object IEnumerator.Current => throw new InvalidOperationException();
    }
}
