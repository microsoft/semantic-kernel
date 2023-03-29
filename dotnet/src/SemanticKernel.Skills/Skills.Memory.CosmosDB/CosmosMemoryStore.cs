// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Microsoft.Azure.Cosmos;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.Embeddings.VectorOperations;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Memory.Collections;

namespace Skills.Memory.CosmosDB;
public class CosmosMemoryStore<TEmbedding> : CosmosDataStore<IEmbeddingWithMetadata<TEmbedding>>, IMemoryStore<TEmbedding>
    where TEmbedding : unmanaged
{
    public CosmosMemoryStore(CosmosClient client, string databaseName, string containerName)
    : base(client, databaseName, containerName)
    { }

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

        var asyncEmbeddingCollection = this.TryGetCollectionAsync(collection);
        var embeddingCollection = asyncEmbeddingCollection.ToEnumerable();

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

    #endregion
}

/// <summary>
/// Default constructor for a simple volatile memory embeddings store for embeddings.
/// The default embedding type is <see cref="float"/>.
/// </summary>
public class CosmosMemoryStore : CosmosMemoryStore<float>
{
    public CosmosMemoryStore(CosmosClient client, string databaseName, string containerName)
        : base(client, databaseName, containerName)
    { }
}
