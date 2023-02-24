// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.Embeddings.VectorOperations;
using Microsoft.SemanticKernel.Memory.Storage;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// A simple volatile memory embeddings store.
/// TODO: multiple enumerations
/// </summary>
/// <typeparam name="TEmbedding">Embedding type</typeparam>
public class VolatileMemoryStore<TEmbedding> : VolatileDataStore<IEmbeddingWithMetadata<TEmbedding>>, IMemoryStore<TEmbedding>
    where TEmbedding : unmanaged
{
    /// <inheritdoc/>
    public IAsyncEnumerable<(IEmbeddingWithMetadata<TEmbedding>, double)> GetNearestMatchesAsync(
        string collection,
        Embedding<TEmbedding> embedding,
        int limit = 1,
        double minRelevanceScore = 0)
    {
        IEnumerable<DataEntry<IEmbeddingWithMetadata<TEmbedding>>>? embeddingCollection = null;
        if (this.TryGetCollection(collection, out var collectionDict))
        {
            embeddingCollection = collectionDict.Values;
        }

        if (embeddingCollection == null || !embeddingCollection.Any())
        {
            return AsyncEnumerable.Empty<(IEmbeddingWithMetadata<TEmbedding>, double)>();
        }

        EmbeddingReadOnlySpan<TEmbedding> embeddingSpan = new(embedding.AsReadOnlySpan());

        TopNSortedList<IEmbeddingWithMetadata<TEmbedding>> sortedEmbeddings = new(limit);
        foreach (var item in embeddingCollection)
        {
            if (item.Value != null)
            {
                EmbeddingReadOnlySpan<TEmbedding> itemSpan = new(item.Value.Embedding.AsReadOnlySpan());
                double similarity = embeddingSpan.CosineSimilarity(itemSpan);
                if (similarity >= minRelevanceScore)
                {
                    sortedEmbeddings.Add(similarity, item.Value);
                }
            }
        }

        return sortedEmbeddings.Select(x => (x.Value, x.Key)).ToAsyncEnumerable();
    }

    #region private ================================================================================

    /// <summary>
    /// Calculates the cosine similarity between an <see cref="Embedding{TEmbedding}"/> and an <see cref="IEmbeddingWithMetadata{TEmbedding}"/>
    /// </summary>
    /// <param name="embedding">The input <see cref="Embedding{TEmbedding}"/> to be compared.</param>
    /// <param name="embeddingWithData">The input <see cref="IEmbeddingWithMetadata{TEmbedding}"/> to be compared.</param>
    /// <returns>A tuple consisting of the <see cref="IEmbeddingWithMetadata{TEmbedding}"/> cosine similarity result.</returns>
    private (IEmbeddingWithMetadata<TEmbedding>, double) PairEmbeddingWithSimilarity(Embedding<TEmbedding> embedding,
        IEmbeddingWithMetadata<TEmbedding> embeddingWithData)
    {
        var similarity = embedding.Vector.ToArray().CosineSimilarity(embeddingWithData.Embedding.Vector.ToArray());
        return (embeddingWithData, similarity);
    }

    /// <summary>
    /// A sorted list that only keeps the top N items.
    /// </summary>
    /// <typeparam name="T"></typeparam>
    private class TopNSortedList<T> : SortedList<double, T>
    {
        /// <summary>
        /// Creates an instance of the <see cref="TopNSortedList{T}"/> class.
        /// </summary>
        /// <param name="maxSize"></param>
        public TopNSortedList(int maxSize)
            : base(new DescendingDoubleComparer())
        {
            this._maxSize = maxSize;
        }

        /// <summary>
        /// Adds a new item to the list.
        /// </summary>
        /// <param name="score">The item's score</param>
        /// <param name="value">The item's value</param>
        public new void Add(double score, T value)
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

            base.Add(score, value);
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

    #endregion
}

/// <summary>
/// Default constructor for a simple volatile memory embeddings store for embeddings.
/// The default embedding type is <see cref="float"/>.
/// </summary>
public class VolatileMemoryStore : VolatileMemoryStore<float>
{
}
