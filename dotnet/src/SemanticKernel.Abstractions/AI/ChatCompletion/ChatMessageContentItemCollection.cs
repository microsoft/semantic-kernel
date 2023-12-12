// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.ChatCompletion;

#pragma warning disable CA1033 // Interface methods should be callable by child types

/// <summary>
/// Contains collection of chat message content items of type <see cref="KernelContent"/>.
/// </summary>
public class ChatMessageContentItemCollection : IList<KernelContent>, IReadOnlyList<KernelContent>
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ChatMessageContentItemCollection"/> class.
    /// </summary>
    public ChatMessageContentItemCollection()
    {
        this._items = new();
    }

    /// <summary>
    /// Gets or sets the content item at the specified index in the collection.
    /// </summary>
    /// <param name="index">The index of the content item to get or set.</param>
    /// <returns>The content item at the specified index.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="value"/> is null.</exception>
    /// <exception cref="ArgumentOutOfRangeException">The <paramref name="index"/> was not valid for this collection.</exception>
    public KernelContent this[int index]
    {
        get => this._items[index];
        set
        {
            Verify.NotNull(value);
            this._items[index] = value;
        }
    }

    /// <summary>
    /// Gets the number of content items in the collection.
    /// </summary>
    public int Count => this._items.Count;

    /// <summary>
    /// Adds a content item to the collection.
    /// </summary>
    /// <param name="item">The content item to add.</param>
    /// <exception cref="ArgumentNullException"><paramref name="item"/> is null.</exception>
    public void Add(KernelContent item)
    {
        Verify.NotNull(item);
        this._items.Add(item);
    }

    /// <summary>
    /// Removes all content items from the collection.
    /// </summary>
    public void Clear() => this._items.Clear();

    /// <summary>
    /// Determines whether a content item is in the collection.
    /// </summary>
    /// <param name="item">The content item to locate.</param>
    /// <returns>True if the content item is found in the collection; otherwise, false.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="item"/> is null.</exception>
    public bool Contains(KernelContent item)
    {
        Verify.NotNull(item);
        return this._items.Contains(item);
    }

    /// <summary>
    /// Copies all of the content items in the collection to an array, starting at the specified destination array index.
    /// </summary>
    /// <param name="array">The destination array into which the content items should be copied.</param>
    /// <param name="arrayIndex">The zero-based index into <paramref name="array"/> at which copying should begin.</param>
    /// <exception cref="ArgumentNullException"><paramref name="array"/> is null.</exception>
    /// <exception cref="ArgumentException">The number of content items in the collection is greater than the available space from <paramref name="arrayIndex"/> to the end of <paramref name="array"/>.</exception>
    /// <exception cref="ArgumentOutOfRangeException"><paramref name="arrayIndex"/> is less than 0.</exception>
    public void CopyTo(KernelContent[] array, int arrayIndex) => this._items.CopyTo(array, arrayIndex);

    /// <summary>
    /// Searches for the specified content item and returns the index of the first occurrence.
    /// </summary>
    /// <param name="item">The content item to locate.</param>
    /// <returns>The index of the first found occurrence of the specified content item; -1 if the content item could not be found.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="item"/> is null.</exception>
    public int IndexOf(KernelContent item)
    {
        Verify.NotNull(item);
        return this._items.IndexOf(item);
    }

    /// <summary>
    /// Inserts a content item into the collection at the specified index.
    /// </summary>
    /// <param name="index">The index at which the content item should be inserted.</param>
    /// <param name="item">The content item to insert.</param>
    /// <exception cref="ArgumentNullException"><paramref name="item"/> is null.</exception>
    public void Insert(int index, KernelContent item)
    {
        Verify.NotNull(item);
        this._items.Insert(index, item);
    }

    /// <summary>
    /// Removes the first occurrence of the specified content item from the collection.
    /// </summary>
    /// <param name="item">The content item to remove from the collection.</param>
    /// <returns>True if the item was successfully removed; false if it wasn't located in the collection.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="item"/> is null.</exception>
    public bool Remove(KernelContent item)
    {
        Verify.NotNull(item);
        return this._items.Remove(item);
    }

    /// <summary>
    /// Removes the content item at the specified index from the collection.
    /// </summary>
    /// <param name="index">The index of the content item to remove.</param>
    public void RemoveAt(int index) => this._items.RemoveAt(index);

    bool ICollection<KernelContent>.IsReadOnly => false;

    IEnumerator IEnumerable.GetEnumerator() => this._items.GetEnumerator();

    IEnumerator<KernelContent> IEnumerable<KernelContent>.GetEnumerator() => this._items.GetEnumerator();

    #region private

    private readonly List<KernelContent> _items;

    #endregion
}
