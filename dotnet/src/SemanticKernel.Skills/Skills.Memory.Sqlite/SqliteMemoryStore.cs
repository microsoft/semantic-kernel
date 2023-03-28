// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.Embeddings.VectorOperations;
using Microsoft.SemanticKernel.Memory.Collections;
using Microsoft.SemanticKernel.Memory.Storage;
using Microsoft.SemanticKernel.Memory;
using SQLiteLibrary.Imported;
using Microsoft.Data.Sqlite;
using System.Linq;
using System.Threading.Tasks;

namespace SqliteMemory;
public class SqliteMemoryStore<TEmbedding> : SqliteDataStore<IEmbeddingWithMetadata<TEmbedding>>, IMemoryStore<TEmbedding>
    where TEmbedding : unmanaged
{
    public SqliteMemoryStore(SqliteConnection dbConnection)
        : base(dbConnection)
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

        IAsyncEnumerable<DataEntry<IEmbeddingWithMetadata<TEmbedding>>> asyncEmbeddingCollection = this.TryGetCollectionAsync(collection);
        IEnumerable<DataEntry<IEmbeddingWithMetadata<TEmbedding>>> embeddingCollection = asyncEmbeddingCollection.ToEnumerable();

        bool bEmpty = embeddingCollection?.Any() ?? false;
        if (bEmpty)
        {
            return AsyncEnumerable.Empty<(IEmbeddingWithMetadata<TEmbedding>, double)>();
        }

        EmbeddingReadOnlySpan<TEmbedding> embeddingSpan = new(embedding.AsReadOnlySpan());

        TopNCollection<IEmbeddingWithMetadata<TEmbedding>> embeddings = new(limit);

#pragma warning disable CS8602 // Dereference of a possibly null reference.
        // We checked to make sure embedding collection is not null a few lines ago.
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
#pragma warning restore CS8602 // Dereference of a possibly null reference.

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

//public class SqliteMemoryStore : SqliteMemoryStore<float>
//{
//    public SqliteMemoryStore(SqliteConnection dbConnection)
//        : base(dbConnection)
//    { }
//}
