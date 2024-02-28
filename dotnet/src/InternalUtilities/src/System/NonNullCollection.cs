// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides a collection of non-null items.
/// </summary>
[ExcludeFromCodeCoverage]
[SuppressMessage("Performance", "CA1812:Avoid uninstantiated internal classes", Justification = "This class is an internal utility.")]
internal sealed class NonNullCollection<T> : IList<T>, IReadOnlyList<T>
{
    /// <summary>
    /// The underlying list of items.
    /// </summary>
    private readonly List<T> _items;

    /// <summary>
    /// Initializes a new instance of the <see cref="NonNullCollection{T}"/> class.
    /// </summary>
    public NonNullCollection() => this._items = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="NonNullCollection{T}"/> class.
    /// </summary>
    /// <param name="items">The initial collection of items to populate this collection.</param>
    public NonNullCollection(IEnumerable<T> items)
    {
        Verify.NotNull(items);
        this._items = new(items);
    }

    /// <summary>
    /// Gets or sets the item at the specified index in the collection.
    /// </summary>
    /// <param name="index">The index of the item to get or set.</param>
    /// <returns>The item at the specified index.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="value"/> is null.</exception>
    /// <exception cref="ArgumentOutOfRangeException">The <paramref name="index"/> was not valid for this collection.</exception>
    public T this[int index]
    {
        get => this._items[index];
        set
        {
            Verify.NotNull(value);
            this._items[index] = value;
        }
    }

    /// <summary>
    /// Gets the number of items in the collection.
    /// </summary>
    public int Count => this._items.Count;

    /// <summary>
    /// Adds an item to the collection.
    /// </summary>
    /// <param name="item">The item to add.</param>
    /// <exception cref="ArgumentNullException"><paramref name="item"/> is null.</exception>
    public void Add(T item)
    {
        Verify.NotNull(item);
        this._items.Add(item);
    }

    /// <summary>
    /// Removes all items from the collection.
    /// </summary>
    public void Clear() => this._items.Clear();

    /// <summary>
    /// Determines whether an item is in the collection.
    /// </summary>
    /// <param name="item">The item to locate.</param>
    /// <returns>True if the item is found in the collection; otherwise, false.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="item"/> is null.</exception>
    public bool Contains(T item)
    {
        Verify.NotNull(item);
        return this._items.Contains(item);
    }

    /// <summary>
    /// Copies all of the items in the collection to an array, starting at the specified destination array index.
    /// </summary>
    /// <param name="array">The destination array into which the items should be copied.</param>
    /// <param name="arrayIndex">The zero-based index into <paramref name="array"/> at which copying should begin.</param>
    /// <exception cref="ArgumentNullException"><paramref name="array"/> is null.</exception>
    /// <exception cref="ArgumentException">The number of items in the collection is greater than the available space from <paramref name="arrayIndex"/> to the end of <paramref name="array"/>.</exception>
    /// <exception cref="ArgumentOutOfRangeException"><paramref name="arrayIndex"/> is less than 0.</exception>
    public void CopyTo(T[] array, int arrayIndex) => this._items.CopyTo(array, arrayIndex);

    /// <summary>
    /// Searches for the specified item and returns the index of the first occurrence.
    /// </summary>
    /// <param name="item">The item to locate.</param>
    /// <returns>The index of the first found occurrence of the specified item; -1 if the item could not be found.</returns>
    public int IndexOf(T item)
    {
        Verify.NotNull(item);
        return this._items.IndexOf(item);
    }

    /// <summary>
    /// Inserts an item into the collection at the specified index.
    /// </summary>
    /// <param name="index">The index at which the item should be inserted.</param>
    /// <param name="item">The item to insert.</param>
    /// <exception cref="ArgumentNullException"><paramref name="item"/> is null.</exception>
    public void Insert(int index, T item)
    {
        Verify.NotNull(item);
        this._items.Insert(index, item);
    }

    /// <summary>
    /// Removes the first occurrence of the specified item from the collection.
    /// </summary>
    /// <param name="item">The item to remove from the collection.</param>
    /// <returns>True if the item was successfully removed; false if it wasn't located in the collection.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="item"/> is null.</exception>
    public bool Remove(T item)
    {
        Verify.NotNull(item);
        return this._items.Remove(item);
    }

    /// <summary>
    /// Removes the item at the specified index from the collection.
    /// </summary>
    /// <param name="index">The index of the item to remove.</param>
    public void RemoveAt(int index) => this._items.RemoveAt(index);

    bool ICollection<T>.IsReadOnly => false;

    IEnumerator IEnumerable.GetEnumerator() => this._items.GetEnumerator();

    IEnumerator<T> IEnumerable<T>.GetEnumerator() => this._items.GetEnumerator();
}
