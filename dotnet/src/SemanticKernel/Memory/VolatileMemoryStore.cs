// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory.Collections;
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
        if (limit <= 0)
        {
            return AsyncEnumerable.Empty<(IEmbeddingWithMetadata<TEmbedding>, double)>();
        }

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

        TopNCollection<IEmbeddingWithMetadata<TEmbedding>> embeddings = new(limit);

        foreach (var item in embeddingCollection)
        {
            if (item.Value != null)
            {
                EmbeddingReadOnlySpan<TEmbedding> itemSpan = new(item.Value.Embedding.AsReadOnlySpan());
                double similarity = embeddingSpan.CosineSimilarity(itemSpan);
                if (similarity >= minRelevanceScore)
                {
                    embeddings.Add(new(item.Value, similarity));
                }
            }
        }

        embeddings.SortByScore();

        return embeddings.Select(x => (x.Value, x.Score.Value)).ToAsyncEnumerable();
    }

    #region private ================================================================================

    #endregion
}

/// <summary>
/// Default constructor for a simple volatile memory embeddings store for embeddings.
/// The default embedding type is <see cref="float"/>.
/// </summary>
public class VolatileMemoryStore : VolatileMemoryStore<float>
{
}
