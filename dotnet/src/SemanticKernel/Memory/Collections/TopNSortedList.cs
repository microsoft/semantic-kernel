// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;

namespace Microsoft.SemanticKernel.Memory.Collections;

/// <summary>
/// A sorted list that only keeps the top N items.
/// </summary>
/// <typeparam name="T">Type of the item.</typeparam>
internal class TopNSortedList<T> : SortedList<double, IEnumerable<T>>
{
    /// <summary>
    /// Creates an instance of the <see cref="TopNSortedList{T}"/> class.
    /// </summary>
    /// <param name="maxSize">The maximum number of items this collection can store.</param>
    public TopNSortedList(int maxSize)
        : base(new DescendingDoubleComparer())
    {
        this._maxSize = maxSize;
    }

    /// <summary>
    /// Adds a new item to the list.
    /// </summary>
    /// <param name="score">The item's score.</param>
    /// <param name="value">The item's value.</param>
    public void Add(double score, T value)
    {
        if (this.Count >= this._maxSize)
        {
            if (score < this.Keys.Last())
            {
                // If the key is less than the smallest key in the list, then we don't need to add it.
                return;
            }

            // Remove the smallest key.
            this.RemoveAt(this.Count - 1);
        }

        if (this.TryGetValue(score, out IEnumerable<T> items))
        {
            _ = items.Append(value);
        }
        else
        {
            this.Add(score, new List<T> { value });
        }
    }

    /// <summary>
    /// Converts collection to flatten enumerable collection.
    /// </summary>
    /// <returns>Flatten <see cref="IEnumerable{T}"/> collection.</returns>
    public IEnumerable<(T, double)> ToTuples()
    {
        return this.SelectMany(x => x.Value.Select(v => (v, x.Key)));
    }

    private readonly int _maxSize;

    private class DescendingDoubleComparer : IComparer<double>
    {
        public int Compare(double x, double y)
        {
            int compareResult = Comparer<double>.Default.Compare(x, y);

            // Invert the result for descending order.
            return 0 - compareResult;
        }
    }
}
