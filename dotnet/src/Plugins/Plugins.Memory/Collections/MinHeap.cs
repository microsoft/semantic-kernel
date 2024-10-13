// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream

namespace Microsoft.SemanticKernel.Memory;
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
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD

namespace Microsoft.SemanticKernel.Memory;
<<<<<<< main
=======
<<<<<<< div
=======
<<<<<<< HEAD

namespace Microsoft.SemanticKernel.Memory;
>>>>>>> main
=======
>>>>>>> head
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< HEAD

namespace Microsoft.SemanticKernel.Memory;
>>>>>>> origin/main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
using Microsoft.SemanticKernel.Diagnostics;

#pragma warning disable IDE0130 // Namespace does not match folder structure
namespace Microsoft.SemanticKernel.Memory.Collections;
#pragma warning restore IDE0130 // Namespace does not match folder structure
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head

/// <summary>
/// Implements the classic 'heap' data structure. By default, the item with the lowest value is at the top of the heap.
/// </summary>
/// <typeparam name="T">Data type.</typeparam>
internal sealed class MinHeap<T> : IEnumerable<T> where T : IComparable<T>
{
    private const int DefaultCapacity = 7;
    private const int MinCapacity = 0;

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    private static readonly T[] s_emptyBuffer = [];
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
>>>>>>> Stashed changes
<<<<<<< main
    private static readonly T[] s_emptyBuffer = [];
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
    private static readonly T[] s_emptyBuffer = [];
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
    private static readonly T[] s_emptyBuffer = [];
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
    private static readonly T[] s_emptyBuffer = [];
=======
    private static readonly T[] s_emptyBuffer = Array.Empty<T>();
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head

    private T[] _items;
    private int _count;

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
>>>>>>> head
    /// <summary>
    /// Initializes a new instance of the <see cref="MinHeap{T}"/> class.
    /// </summary>
    /// <param name="minValue">Heap minimum value, which will be used as first item in collection.</param>
    /// <param name="capacity">Number of elements that collection can hold.</param>
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
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
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
>>>>>>> head
    public MinHeap(T minValue, int capacity = DefaultCapacity)
    {
        if (capacity < MinCapacity)
        {
            Verify.ThrowArgumentOutOfRangeException(nameof(capacity), capacity, $"MinHeap capacity must be greater than {MinCapacity}.");
        }

        this._items = new T[capacity + 1];
        //
        // The 0'th item is a sentinel entry that simplifies the code
        //
        this._items[0] = minValue;
    }

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
>>>>>>> head
    /// <summary>
    /// Initializes a new instance of the <see cref="MinHeap{T}"/> class.
    /// </summary>
    /// <param name="minValue">Heap minimum value, which will be used as first item in collection.</param>
    /// <param name="items">List of items to add.</param>
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
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
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
>>>>>>> head
    public MinHeap(T minValue, IList<T> items)
        : this(minValue, items.Count)
    {
        this.Add(items);
    }

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    /// <summary>
    /// Gets the current number of items in the collection.
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
<<<<<<< Updated upstream
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
<<<<<<< HEAD
    /// <summary>
    /// Gets the current number of items in the collection.
    /// </summary>
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
    public int Count
    {
        get => this._count;
        internal set
        {
            Debug.Assert(value <= this.Capacity);
            this._count = value;
        }
    }

<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
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
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
<<<<<<< div
=======
<<<<<<< HEAD
>>>>>>> main
=======
>>>>>>> head
    /// <summary>
    /// Gets the number of elements that collection can hold.
    /// </summary>
    public int Capacity => this._items.Length - 1; // 0'th item is always a sentinel to simplify code

    /// <summary>
    /// Gets the element at the specified index.
    /// </summary>
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
    public int Capacity => this._items.Length - 1; // 0'th item is always a sentinel to simplify code

>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
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
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
    public T this[int index]
    {
        get => this._items[index + 1];
        internal set { this._items[index + 1] = value; }
    }

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
>>>>>>> head
    /// <summary>
    /// Gets first item in collection.
    /// </summary>
    public T Top => this._items[1];

    /// <summary>
    /// Gets the boolean flag which indicates if collection is empty.
    /// </summary>
    public bool IsEmpty => (this._count == 0);

    /// <summary>
    /// Sets collection item count to zero.
    /// </summary>
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
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
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
    public T Top => this._items[1];

    public bool IsEmpty => (this._count == 0);

>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
    public void Clear()
    {
        this._count = 0;
    }

<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< div
=======
<<<<<<< HEAD
>>>>>>> main
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> origin/main
>>>>>>> head
=======
<<<<<<< Updated upstream
>>>>>>> Stashed changes
    /// <summary>
    /// Sets collection item count to zero and removes all items in collection.
    /// </summary>
=======
<<<<<<< div
<<<<<<< div
=======
<<<<<<< head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
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
    /// Sets collection item count to zero and removes all items in collection.
    /// </summary>
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
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
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
    public void Erase()
    {
        Array.Clear(this._items, 1, this._count);
        this._count = 0;
    }

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    /// <summary>
    /// Removes all items in collection and returns them.
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
<<<<<<< Updated upstream
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
<<<<<<< HEAD
    /// <summary>
    /// Removes all items in collection and returns them.
    /// </summary>
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
    public T[] DetachBuffer()
    {
        T[] buf = this._items;
        this._items = s_emptyBuffer;
        this._count = 0;
        return buf;
    }

<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> origin/main
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
<<<<<<< div
=======
<<<<<<< HEAD
>>>>>>> main
=======
>>>>>>> head
    /// <summary>
    /// Adds new item to collection.
    /// </summary>
    /// <param name="item">Item to add.</param>
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
>>>>>>> head
    public void Add(T item)
    {
        //
        // the 0'th item is always a sentinel and not included in this._count.
        // The length of the buffer is always this._count + 1
        //
        this._count++;
        this.EnsureCapacity();
        this._items[this._count] = item;
        this.UpHeap(this._count);
    }

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
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
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
>>>>>>> head
    /// <summary>
    /// Adds new items to collection.
    /// </summary>
    /// <param name="items">Items to add.</param>
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
>>>>>>> head
    public void Add(IEnumerable<T> items)
    {
        foreach (T item in items)
        {
            this.Add(item);
        }
    }

<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
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
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
<<<<<<< div
=======
<<<<<<< HEAD
>>>>>>> main
=======
>>>>>>> head
    /// <summary>
    /// Adds new items starting from specified index.
    /// </summary>
    /// <param name="items">Items to add.</param>
    /// <param name="startAt">Starting point of items to add.</param>
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> origin/main
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
<<<<<<< div
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> main
=======
>>>>>>> head
    public void Add(IList<T> items, int startAt = 0)
    {
        Verify.NotNull(items);

        int newItemCount = items.Count;
        if (startAt >= newItemCount)
        {
            Verify.ThrowArgumentOutOfRangeException(nameof(startAt), startAt, $"{nameof(startAt)} value must be less than {nameof(items)}.{nameof(items.Count)}.");
        }

        this.EnsureCapacity(this._count + (newItemCount - startAt));
        for (int i = startAt; i < newItemCount; ++i)
        {
            //
            // the 0'th item is always a sentinel and not included in this._count.
            // The length of the buffer is always this._count + 1
            //
            this._count++;
            this._items[this._count] = items[i];
            this.UpHeap(this._count);
        }
    }

<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< div
=======
<<<<<<< HEAD
>>>>>>> main
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> origin/main
>>>>>>> head
=======
<<<<<<< Updated upstream
>>>>>>> Stashed changes
    /// <summary>
    /// Removes first item in collection and returns it.
    /// </summary>
=======
<<<<<<< div
<<<<<<< div
=======
<<<<<<< head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
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
    /// Removes first item in collection and returns it.
    /// </summary>
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
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
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> main
=======
>>>>>>> head
    public T RemoveTop()
    {
        if (this._count == 0)
        {
            throw new InvalidOperationException("MinHeap is empty.");
        }

        T item = this._items[1];
        this._items[1] = this._items[this._count--];
        this.DownHeap(1);
        return item;
    }

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    /// <summary>
    /// Removes all items in collection and returns them.
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
<<<<<<< Updated upstream
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
<<<<<<< HEAD
    /// <summary>
    /// Removes all items in collection and returns them.
    /// </summary>
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
    public IEnumerable<T> RemoveAll()
    {
        while (this._count > 0)
        {
            yield return this.RemoveTop();
        }
    }

<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
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
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
<<<<<<< div
=======
<<<<<<< HEAD
>>>>>>> main
=======
>>>>>>> head
    /// <summary>
    /// Resizes collection to specified capacity.
    /// </summary>
    /// <param name="capacity">Number of elements that collection can hold.</param>
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
>>>>>>> head
    public void EnsureCapacity(int capacity)
    {
        if (capacity < MinCapacity)
        {
            Verify.ThrowArgumentOutOfRangeException(nameof(capacity), capacity, $"MinHeap capacity must be greater than {MinCapacity}.");
        }

        // 0th item is always a sentinel
        capacity++;
        if (capacity > this._items.Length)
        {
            Array.Resize(ref this._items, capacity);
        }
    }

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    /// <summary>
    /// Doubles collection capacity.
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
<<<<<<< Updated upstream
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
<<<<<<< HEAD
    /// <summary>
    /// Doubles collection capacity.
    /// </summary>
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
    public void EnsureCapacity()
    {
        if (this._count == this._items.Length)
        {
            Array.Resize(ref this._items, (this._count * 2) + 1);
        }
    }

    private void UpHeap(int startAt)
    {
        int i = startAt;
        T[] items = this._items;
        T item = items[i];
        int parent = i >> 1; //i / 2;

        while (parent > 0 && items[parent].CompareTo(item) > 0)
        {
            // Child > parent. Exchange with parent, thus moving the child up the queue
            items[i] = items[parent];
            i = parent;
            parent = i >> 1; //i / 2;
        }

        items[i] = item;
    }

    private void DownHeap(int startAt)
    {
        int i = startAt;
        int count = this._count;
        int maxParent = count >> 1;
        T[] items = this._items;
        T item = items[i];

        while (i <= maxParent)
        {
            int child = i + i;
            //
            // Exchange the item with the smaller of its two children - if one is smaller, i.e.
            //
            // First, find the smaller child
            //
            if (child < count && items[child].CompareTo(items[child + 1]) > 0)
            {
                child++;
            }

            if (item.CompareTo(items[child]) <= 0)
            {
                // Heap condition is satisfied. Parent <= both its children
                break;
            }

            // Else, swap parent with the smallest child
            items[i] = items[child];
            i = child;
        }

        items[i] = item;
    }

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    /// <summary>
    /// Returns an enumerator that iterates through the collection.
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
<<<<<<< Updated upstream
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
<<<<<<< HEAD
    /// <summary>
    /// Returns an enumerator that iterates through the collection.
    /// </summary>
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
    public IEnumerator<T> GetEnumerator()
    {
        // The 0'th item in the queue is a sentinel. i is 1 based.
        for (int i = 1; i <= this._count; ++i)
        {
            yield return this._items[i];
        }
    }

    System.Collections.IEnumerator System.Collections.IEnumerable.GetEnumerator()
    {
        return this.GetEnumerator();
    }

    /// <summary>
    /// Heap Sort in-place.
    /// This is destructive. Once you do this, the heap order is lost.
    /// The advantage on in-place is that we don't need to do another allocation
    /// </summary>
    public void SortDescending()
    {
        int count = this._count;
        int i = count; // remember that the 0'th item in the queue is always a sentinel. So i is 1 based

        while (this._count > 0)
        {
            //
            // this dequeues the item with the current LOWEST relevancy
            // We take that and place it at the 'back' of the array - thus inverting it
            //
            T item = this.RemoveTop();
            this._items[i--] = item;
        }

        this._count = count;
    }

    /// <summary>
    /// Restores heap order
    /// </summary>
    internal void Restore()
    {
        this.Clear();
        this.Add(this._items, 1);
    }

    internal void Sort(IComparer<T> comparer)
    {
        Array.Sort(this._items, 1, this._count, comparer);
    }
}
