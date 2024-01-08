// Copyright (c) Microsoft. All rights reserved.

#if !NET6_0_OR_GREATER
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;

// NOTE: This is a copy of the PriorityQueue implementation from:
// https://github.com/dotnet/runtime/blob/14127ea770cf748509b9057b7a8ed5a3471ebfed/src/libraries/System.Collections/src/System/Collections/Generic/PriorityQueue.cs
// to serve as a polyfill when targeting netstandard2.0. The only changes made to it are:
// - Removed unnused members
// - Made it internal and sealed
// - Removed exception messages from resource files
// - Replaced/removed usage of APIs not available on netstandard2.0, e.g. ThrowIfNegative, IsReferenceOrContainsReferences
// - Auto-fixed style violations for this repo
// - ifdef'd it to only be included pre-net6.0

namespace System.Collections.Generic;

/// <summary>
///  Represents a min priority queue.
/// </summary>
/// <typeparam name="TElement">Specifies the type of elements in the queue.</typeparam>
/// <typeparam name="TPriority">Specifies the type of priority associated with enqueued elements.</typeparam>
/// <remarks>
///  Implements an array-backed quaternary min-heap. Each element is enqueued with an associated priority
///  that determines the dequeue order: elements with the lowest priority get dequeued first.
/// </remarks>
[DebuggerDisplay("Count = {Count}")]
internal sealed class PriorityQueue<TElement, TPriority>
{
    /// <summary>
    /// Represents an implicit heap-ordered complete d-ary tree, stored as an array.
    /// </summary>
    private (TElement Element, TPriority Priority)[] _nodes;

    /// <summary>
    /// Custom comparer used to order the heap.
    /// </summary>
    private readonly IComparer<TPriority>? _comparer;

    /// <summary>
    /// The number of nodes in the heap.
    /// </summary>
    private int _size;

    /// <summary>
    /// Specifies the arity of the d-ary heap, which here is quaternary.
    /// It is assumed that this value is a power of 2.
    /// </summary>
    private const int Arity = 4;

    /// <summary>
    /// The binary logarithm of <see cref="Arity" />.
    /// </summary>
    private const int Log2Arity = 2;

    /// <summary>
    ///  Initializes a new instance of the <see cref="PriorityQueue{TElement, TPriority}"/> class
    ///  with the specified initial capacity.
    /// </summary>
    /// <param name="initialCapacity">Initial capacity to allocate in the underlying heap array.</param>
    /// <exception cref="ArgumentOutOfRangeException">
    ///  The specified <paramref name="initialCapacity"/> was negative.
    /// </exception>
    public PriorityQueue(int initialCapacity)
        : this(initialCapacity, comparer: null)
    {
    }

    /// <summary>
    ///  Initializes a new instance of the <see cref="PriorityQueue{TElement, TPriority}"/> class
    ///  with the specified initial capacity and custom priority comparer.
    /// </summary>
    /// <param name="initialCapacity">Initial capacity to allocate in the underlying heap array.</param>
    /// <param name="comparer">
    ///  Custom comparer dictating the ordering of elements.
    ///  Uses <see cref="Comparer{T}.Default" /> if the argument is <see langword="null"/>.
    /// </param>
    /// <exception cref="ArgumentOutOfRangeException">
    ///  The specified <paramref name="initialCapacity"/> was negative.
    /// </exception>
    public PriorityQueue(int initialCapacity, IComparer<TPriority>? comparer)
    {
        Debug.Assert(initialCapacity >= 0);

        this._nodes = new (TElement, TPriority)[initialCapacity];
        this._comparer = InitializeComparer(comparer);
    }

    /// <summary>
    ///  Gets the number of elements contained in the <see cref="PriorityQueue{TElement, TPriority}"/>.
    /// </summary>
    public int Count => this._size;

    /// <summary>
    ///  Adds the specified element with associated priority to the <see cref="PriorityQueue{TElement, TPriority}"/>.
    /// </summary>
    /// <param name="element">The element to add to the <see cref="PriorityQueue{TElement, TPriority}"/>.</param>
    /// <param name="priority">The priority with which to associate the new element.</param>
    public void Enqueue(TElement element, TPriority priority)
    {
        // Virtually add the node at the end of the underlying array.
        // Note that the node being enqueued does not need to be physically placed
        // there at this point, as such an assignment would be redundant.

        int currentSize = this._size;

        if (this._nodes.Length == currentSize)
        {
            this.Grow(currentSize + 1);
        }

        this._size = currentSize + 1;

        if (this._comparer == null)
        {
            this.MoveUpDefaultComparer((element, priority), currentSize);
        }
        else
        {
            this.MoveUpCustomComparer((element, priority), currentSize);
        }
    }

    /// <summary>
    ///  Removes the minimal element and then immediately adds the specified element with associated priority to the <see cref="PriorityQueue{TElement, TPriority}"/>,
    /// </summary>
    /// <param name="element">The element to add to the <see cref="PriorityQueue{TElement, TPriority}"/>.</param>
    /// <param name="priority">The priority with which to associate the new element.</param>
    /// <exception cref="InvalidOperationException">The queue is empty.</exception>
    /// <returns>The minimal element removed before performing the enqueue operation.</returns>
    /// <remarks>
    ///  Implements an extract-then-insert heap operation that is generally more efficient
    ///  than sequencing Dequeue and Enqueue operations: in the worst case scenario only one
    ///  shift-down operation is required.
    /// </remarks>
    public TElement DequeueEnqueue(TElement element, TPriority priority)
    {
        if (this._size == 0)
        {
            throw new InvalidOperationException();
        }

        (TElement Element, TPriority Priority) root = this._nodes[0];

        if (this._comparer == null)
        {
            if (Comparer<TPriority>.Default.Compare(priority, root.Priority) > 0)
            {
                this.MoveDownDefaultComparer((element, priority), 0);
            }
            else
            {
                this._nodes[0] = (element, priority);
            }
        }
        else
        {
            if (this._comparer.Compare(priority, root.Priority) > 0)
            {
                this.MoveDownCustomComparer((element, priority), 0);
            }
            else
            {
                this._nodes[0] = (element, priority);
            }
        }

        return root.Element;
    }

    /// <summary>
    ///  Removes the minimal element from the <see cref="PriorityQueue{TElement, TPriority}"/>,
    ///  and copies it to the <paramref name="element"/> parameter,
    ///  and its associated priority to the <paramref name="priority"/> parameter.
    /// </summary>
    /// <param name="element">The removed element.</param>
    /// <param name="priority">The priority associated with the removed element.</param>
    /// <returns>
    ///  <see langword="true"/> if the element is successfully removed;
    ///  <see langword="false"/> if the <see cref="PriorityQueue{TElement, TPriority}"/> is empty.
    /// </returns>
    public bool TryDequeue([MaybeNullWhen(false)] out TElement element, [MaybeNullWhen(false)] out TPriority priority)
    {
        if (this._size != 0)
        {
            (element, priority) = this._nodes[0];
            this.RemoveRootNode();
            return true;
        }

        element = default;
        priority = default;
        return false;
    }

    /// <summary>
    /// Grows the priority queue to match the specified min capacity.
    /// </summary>
    private void Grow(int minCapacity)
    {
        Debug.Assert(this._nodes.Length < minCapacity);

        const int GrowFactor = 2;
        const int MinimumGrow = 4;

        int newcapacity = GrowFactor * this._nodes.Length;

        // Allow the queue to grow to maximum possible capacity (~2G elements) before encountering overflow.
        // Note that this check works even when _nodes.Length overflowed thanks to the (uint) cast
        const int ArrayMaxLength = 0X7FFFFFC7; // Array.MaxLength
        if ((uint)newcapacity > ArrayMaxLength)
        {
            newcapacity = ArrayMaxLength;
        }

        // Ensure minimum growth is respected.
        newcapacity = Math.Max(newcapacity, this._nodes.Length + MinimumGrow);

        // If the computed capacity is still less than specified, set to the original argument.
        // Capacities exceeding Array.MaxLength will be surfaced as OutOfMemoryException by Array.Resize.
        if (newcapacity < minCapacity)
        {
            newcapacity = minCapacity;
        }

        Array.Resize(ref this._nodes, newcapacity);
    }

    /// <summary>
    /// Removes the node from the root of the heap
    /// </summary>
    private void RemoveRootNode()
    {
        int lastNodeIndex = --this._size;

        if (lastNodeIndex > 0)
        {
            (TElement Element, TPriority Priority) lastNode = this._nodes[lastNodeIndex];
            if (this._comparer == null)
            {
                this.MoveDownDefaultComparer(lastNode, 0);
            }
            else
            {
                this.MoveDownCustomComparer(lastNode, 0);
            }
        }

        this._nodes[lastNodeIndex] = default;
    }

    /// <summary>
    /// Gets the index of an element's parent.
    /// </summary>
    private static int GetParentIndex(int index) => (index - 1) >> Log2Arity;

    /// <summary>
    /// Gets the index of the first child of an element.
    /// </summary>
    private static int GetFirstChildIndex(int index) => (index << Log2Arity) + 1;

    /// <summary>
    /// Moves a node up in the tree to restore heap order.
    /// </summary>
    private void MoveUpDefaultComparer((TElement Element, TPriority Priority) node, int nodeIndex)
    {
        // Instead of swapping items all the way to the root, we will perform
        // a similar optimization as in the insertion sort.

        Debug.Assert(this._comparer is null);
        Debug.Assert(0 <= nodeIndex && nodeIndex < this._size);

        (TElement Element, TPriority Priority)[] nodes = this._nodes;

        while (nodeIndex > 0)
        {
            int parentIndex = GetParentIndex(nodeIndex);
            (TElement Element, TPriority Priority) parent = nodes[parentIndex];

            if (Comparer<TPriority>.Default.Compare(node.Priority, parent.Priority) < 0)
            {
                nodes[nodeIndex] = parent;
                nodeIndex = parentIndex;
            }
            else
            {
                break;
            }
        }

        nodes[nodeIndex] = node;
    }

    /// <summary>
    /// Moves a node up in the tree to restore heap order.
    /// </summary>
    private void MoveUpCustomComparer((TElement Element, TPriority Priority) node, int nodeIndex)
    {
        // Instead of swapping items all the way to the root, we will perform
        // a similar optimization as in the insertion sort.

        Debug.Assert(this._comparer is not null);
        Debug.Assert(0 <= nodeIndex && nodeIndex < this._size);

        IComparer<TPriority> comparer = this._comparer!;
        (TElement Element, TPriority Priority)[] nodes = this._nodes;

        while (nodeIndex > 0)
        {
            int parentIndex = GetParentIndex(nodeIndex);
            (TElement Element, TPriority Priority) parent = nodes[parentIndex];

            if (comparer.Compare(node.Priority, parent.Priority) < 0)
            {
                nodes[nodeIndex] = parent;
                nodeIndex = parentIndex;
            }
            else
            {
                break;
            }
        }

        nodes[nodeIndex] = node;
    }

    /// <summary>
    /// Moves a node down in the tree to restore heap order.
    /// </summary>
    private void MoveDownDefaultComparer((TElement Element, TPriority Priority) node, int nodeIndex)
    {
        // The node to move down will not actually be swapped every time.
        // Rather, values on the affected path will be moved up, thus leaving a free spot
        // for this value to drop in. Similar optimization as in the insertion sort.

        Debug.Assert(this._comparer is null);
        Debug.Assert(0 <= nodeIndex && nodeIndex < this._size);

        (TElement Element, TPriority Priority)[] nodes = this._nodes;
        int size = this._size;

        int i;
        while ((i = GetFirstChildIndex(nodeIndex)) < size)
        {
            // Find the child node with the minimal priority
            (TElement Element, TPriority Priority) minChild = nodes[i];
            int minChildIndex = i;

            int childIndexUpperBound = Math.Min(i + Arity, size);
            while (++i < childIndexUpperBound)
            {
                (TElement Element, TPriority Priority) nextChild = nodes[i];
                if (Comparer<TPriority>.Default.Compare(nextChild.Priority, minChild.Priority) < 0)
                {
                    minChild = nextChild;
                    minChildIndex = i;
                }
            }

            // Heap property is satisfied; insert node in this location.
            if (Comparer<TPriority>.Default.Compare(node.Priority, minChild.Priority) <= 0)
            {
                break;
            }

            // Move the minimal child up by one node and
            // continue recursively from its location.
            nodes[nodeIndex] = minChild;
            nodeIndex = minChildIndex;
        }

        nodes[nodeIndex] = node;
    }

    /// <summary>
    /// Moves a node down in the tree to restore heap order.
    /// </summary>
    private void MoveDownCustomComparer((TElement Element, TPriority Priority) node, int nodeIndex)
    {
        // The node to move down will not actually be swapped every time.
        // Rather, values on the affected path will be moved up, thus leaving a free spot
        // for this value to drop in. Similar optimization as in the insertion sort.

        Debug.Assert(this._comparer is not null);
        Debug.Assert(0 <= nodeIndex && nodeIndex < this._size);

        IComparer<TPriority> comparer = this._comparer!;
        (TElement Element, TPriority Priority)[] nodes = this._nodes;
        int size = this._size;

        int i;
        while ((i = GetFirstChildIndex(nodeIndex)) < size)
        {
            // Find the child node with the minimal priority
            (TElement Element, TPriority Priority) minChild = nodes[i];
            int minChildIndex = i;

            int childIndexUpperBound = Math.Min(i + Arity, size);
            while (++i < childIndexUpperBound)
            {
                (TElement Element, TPriority Priority) nextChild = nodes[i];
                if (comparer.Compare(nextChild.Priority, minChild.Priority) < 0)
                {
                    minChild = nextChild;
                    minChildIndex = i;
                }
            }

            // Heap property is satisfied; insert node in this location.
            if (comparer.Compare(node.Priority, minChild.Priority) <= 0)
            {
                break;
            }

            // Move the minimal child up by one node and continue recursively from its location.
            nodes[nodeIndex] = minChild;
            nodeIndex = minChildIndex;
        }

        nodes[nodeIndex] = node;
    }

    /// <summary>
    /// Initializes the custom comparer to be used internally by the heap.
    /// </summary>
    private static IComparer<TPriority>? InitializeComparer(IComparer<TPriority>? comparer)
    {
        if (typeof(TPriority).IsValueType)
        {
            if (comparer == Comparer<TPriority>.Default)
            {
                // if the user manually specifies the default comparer,
                // revert to using the optimized path.
                return null;
            }

            return comparer;
        }

        // Currently the JIT doesn't optimize direct Comparer<T>.Default.Compare
        // calls for reference types, so we want to cache the comparer instance instead.
        // TODO https://github.com/dotnet/runtime/issues/10050: Update if this changes in the future.
        return comparer ?? Comparer<TPriority>.Default;
    }
}
#endif
