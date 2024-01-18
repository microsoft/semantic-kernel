// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides a collection of <see cref="IFunctionFilter"/> instances.
/// </summary>
[Experimental("SKEXP0004")]
internal sealed class FunctionFilterCollection : IList<IFunctionFilter>, IReadOnlyList<IFunctionFilter>
{
    /// <summary>
    /// The underlying dictionary of filters.
    /// </summary>
    private readonly List<IFunctionFilter> _filters;

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionFilterCollection"/> class.
    /// </summary>
    public FunctionFilterCollection() => this._filters = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionFilterCollection"/> class.
    /// </summary>
    /// <param name="filters">The initial collection of filters to populate this collection.</param>
    public FunctionFilterCollection(IEnumerable<IFunctionFilter> filters)
    {
        Verify.NotNull(filters);
        this._filters = new(filters);
    }

    /// <summary>
    /// Gets or sets the filter at the specified index in the collection.
    /// </summary>
    /// <param name="index">The index of the filter to get or set.</param>
    /// <returns>The filter at the specified index.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="value"/> is null.</exception>
    /// <exception cref="ArgumentOutOfRangeException">The <paramref name="index"/> was not valid for this collection.</exception>
    public IFunctionFilter this[int index]
    {
        get => this._filters[index];
        set
        {
            Verify.NotNull(value);
            this._filters[index] = value;
        }
    }

    /// <summary>
    /// Gets the number of filters in the collection.
    /// </summary>
    public int Count => this._filters.Count;

    /// <summary>
    /// Adds a filter to the collection.
    /// </summary>
    /// <param name="item">The filter to add.</param>
    /// <exception cref="ArgumentNullException"><paramref name="item"/> is null.</exception>
    public void Add(IFunctionFilter item)
    {
        Verify.NotNull(item);
        this._filters.Add(item);
    }

    /// <summary>
    /// Removes all filters from the collection.
    /// </summary>
    public void Clear() => this._filters.Clear();

    /// <summary>
    /// Determines whether a filter is in the collection.
    /// </summary>
    /// <param name="item">The filter to locate.</param>
    /// <returns>True if the filter is found in the collection; otherwise, false.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="item"/> is null.</exception>
    public bool Contains(IFunctionFilter item)
    {
        Verify.NotNull(item);
        return this._filters.Contains(item);
    }

    /// <summary>
    /// Copies all of the filters in the collection to an array, starting at the specified destination array index.
    /// </summary>
    /// <param name="array">The destination array into which the filters should be copied.</param>
    /// <param name="arrayIndex">The zero-based index into <paramref name="array"/> at which copying should begin.</param>
    /// <exception cref="ArgumentNullException"><paramref name="array"/> is null.</exception>
    /// <exception cref="ArgumentException">The number of filters in the collection is greater than the available space from <paramref name="arrayIndex"/> to the end of <paramref name="array"/>.</exception>
    /// <exception cref="ArgumentOutOfRangeException"><paramref name="arrayIndex"/> is less than 0.</exception>
    public void CopyTo(IFunctionFilter[] array, int arrayIndex) => this._filters.CopyTo(array, arrayIndex);

    /// <summary>
    /// Searches for the specified filter and returns the index of the first occurrence.
    /// </summary>
    /// <param name="item">The filter to locate.</param>
    /// <returns>The index of the first found occurrence of the specified filter; -1 if the filter could not be found.</returns>
    public int IndexOf(IFunctionFilter item)
    {
        Verify.NotNull(item);
        return this._filters.IndexOf(item);
    }

    /// <summary>
    /// Inserts a filter into the collection at the specified index.
    /// </summary>
    /// <param name="index">The index at which the filter should be inserted.</param>
    /// <param name="item">The filter to insert.</param>
    /// <exception cref="ArgumentNullException"><paramref name="item"/> is null.</exception>
    public void Insert(int index, IFunctionFilter item)
    {
        Verify.NotNull(item);
        this._filters.Insert(index, item);
    }

    /// <summary>
    /// Removes the first occurrence of the specified filter from the collection.
    /// </summary>
    /// <param name="item">The filter to remove from the collection.</param>
    /// <returns>True if the filter was successfully removed; false if it wasn't located in the collection.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="item"/> is null.</exception>
    public bool Remove(IFunctionFilter item)
    {
        Verify.NotNull(item);
        return this._filters.Remove(item);
    }

    /// <summary>
    /// Removes the filter at the specified index from the collection.
    /// </summary>
    /// <param name="index">The index of the filter to remove.</param>
    public void RemoveAt(int index) => this._filters.RemoveAt(index);

    bool ICollection<IFunctionFilter>.IsReadOnly => false;

    IEnumerator IEnumerable.GetEnumerator() => this._filters.GetEnumerator();

    IEnumerator<IFunctionFilter> IEnumerable<IFunctionFilter>.GetEnumerator() => this._filters.GetEnumerator();
}
