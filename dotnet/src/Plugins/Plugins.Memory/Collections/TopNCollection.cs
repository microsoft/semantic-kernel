// Copyright (c) Microsoft. All rights reserved.

using System.Collections;
using System.Collections.Generic;

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
<<<<<<< main
namespace Microsoft.SemanticKernel.Memory;
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
namespace Microsoft.SemanticKernel.Memory;
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
namespace Microsoft.SemanticKernel.Memory;
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
namespace Microsoft.SemanticKernel.Memory;
=======
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
/// A collector for Top N matches. Keeps only the best N matches by Score.
/// Automatically flushes out any not in the top N.
/// By default, items are not sorted by score until you call <see cref="TopNCollection{T}.SortByScore"/>.
/// </summary>
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
<<<<<<< main
=======
<<<<<<< HEAD
>>>>>>> origin/main
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
<<<<<<< HEAD
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
<<<<<<< HEAD
>>>>>>> main
=======
>>>>>>> head
internal sealed class TopNCollection<T>(int maxItems) : IEnumerable<ScoredValue<T>>
{
    private readonly MinHeap<ScoredValue<T>> _heap = new(ScoredValue<T>.Min(), maxItems);
    private bool _sorted = false;

    /// <summary>
    /// Gets the maximum number of items allowed in the collection.
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
    /// </summary>
    public int MaxItems { get; } = maxItems;
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
    /// </summary>
    public int MaxItems { get; } = maxItems;
<<<<<<< main
=======
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

    /// <summary>
    /// Gets the current number of items in the collection.
    /// </summary>
<<<<<<< Updated upstream
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
    /// </summary>
    public int MaxItems { get; } = maxItems;

    /// <summary>
    /// Gets the current number of items in the collection.
    /// </summary>
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
=======
public class TopNCollection<T> : IEnumerable<ScoredValue<T>>
{
    private readonly MinHeap<ScoredValue<T>> _heap;
    private bool _sorted = false;

    public TopNCollection(int maxItems)
    {
        this.MaxItems = maxItems;
        this._heap = new MinHeap<ScoredValue<T>>(ScoredValue<T>.Min(), maxItems);
    }

    public int MaxItems { get; }
>>>>>>> origin/main

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
    public int Count => this._heap.Count;

    internal ScoredValue<T> this[int i] => this._heap[i];
    internal ScoredValue<T> Top => this._heap.Top;

    /// <summary>
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
    /// Resets the collection, allowing it to be reused.
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
    /// Resets the collection, allowing it to be reused.
=======
    /// Call this to reuse the buffer
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
    /// </summary>
    public void Reset()
    {
        this._heap.Clear();
    }

    /// <summary>
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
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
>>>>>>> head
=======
<<<<<<< Updated upstream
>>>>>>> Stashed changes
    /// Adds a single scored value to the collection.
    /// </summary>
    /// <param name="value">The scored value to add.</param>
=======
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< head
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
    /// Adds a single scored value to the collection.
    /// </summary>
    /// <param name="value">The scored value to add.</param>
=======
    /// Adds a single scored value
    /// </summary>
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
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
    /// Adds a single scored value
    /// </summary>
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
    /// Adds a single scored value
    /// </summary>
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
    public void Add(ScoredValue<T> value)
    {
        if (this._sorted)
        {
            this._heap.Restore();
            this._sorted = false;
        }

        if (this._heap.Count == this.MaxItems)
        {
            // Queue is full. We will need to dequeue the item with lowest weight
            if (value.Score <= this.Top.Score)
            {
                // This score is lower than the lowest score on the queue right now. Ignore it
                return;
            }

            this._heap.RemoveTop();
        }

        this._heap.Add(value);
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
    /// Adds a value with a specified score to the collection.
    /// </summary>
    /// <param name="value">The value to add.</param>
    /// <param name="score">The score associated with the value.</param>
    public void Add(T value, double score)
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
    public void Add(T value, Score score)
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
=======
    public void Add(T value, Score score)
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
    public void Add(T value, Score score)
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
    public void Add(T value, Score score)
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
    public void Add(T value, Score score)
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
    public void Add(T value, Score score)
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
=======
    public void Add(T value, Score score)
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
=======
=======
    public void Add(T value, Score score)
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> Stashed changes
>>>>>>> head
    {
        this.Add(new ScoredValue<T>(value, score));
    }

    /// <summary>
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
    /// Sorts the collection in descending order by score.
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
    /// Sorts the collection in descending order by score.
=======
    /// Sort in relevancy order.
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
    /// </summary>
    public void SortByScore()
    {
        if (!this._sorted && this._heap.Count > 0)
        {
            this._heap.SortDescending();
            this._sorted = true;
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
    /// Returns a list containing the scored values in the collection.
    /// </summary>
    /// <returns>A list of scored values.</returns>
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
    public IList<ScoredValue<T>> ToList()
    {
        var list = new List<ScoredValue<T>>(this.Count);
        for (int i = 0, count = this.Count; i < count; ++i)
        {
            list.Add(this[i]);
        }

        return list;
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
    /// Returns an enumerator that iterates through the collection.
    /// </summary>
    /// <returns>An enumerator for the collection.</returns>
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
    public IEnumerator<ScoredValue<T>> GetEnumerator()
    {
        return this._heap.GetEnumerator();
    }

    IEnumerator IEnumerable.GetEnumerator()
    {
        return this._heap.GetEnumerator();
    }
}
