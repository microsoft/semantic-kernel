// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Embeddings;

namespace Memory.VectorStoreEmbeddingGeneration;

/// <summary>
/// Contains extension methods to help add text embedding generation to a <see cref="IVectorStore"/> or <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>
/// </summary>
/// <remarks>
/// This class is part of the <see cref="VectorStore_EmbeddingGeneration"/> sample.
/// </remarks>
public static class TextEmbeddingVectorStoreExtensions
{
    /// <summary>
    /// Add text embedding generation to a <see cref="IVectorStore"/>.
    /// </summary>
    /// <param name="vectorStore">The <see cref="IVectorStore"/> to add text embedding generation to.</param>
    /// <param name="textEmbeddingGenerationService">The service to use for generating text embeddings.</param>
    /// <returns>The <see cref="IVectorStore"/> with text embedding added.</returns>
    public static IVectorStore UseTextEmbeddingGeneration(this IVectorStore vectorStore, ITextEmbeddingGenerationService textEmbeddingGenerationService)
    {
        return new TextEmbeddingVectorStore(vectorStore, textEmbeddingGenerationService);
    }

    /// <summary>
    /// Add text embedding generation to a <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.
    /// </summary>
    /// <param name="vectorStoreRecordCollection">The <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> to add text embedding generation to.</param>
    /// <param name="textEmbeddingGenerationService">The service to use for generating text embeddings.</param>
    /// <typeparam name="TKey">The data type of the record key.</typeparam>
    /// <typeparam name="TRecord">The record data model to use for adding, updating and retrieving data from the store.</typeparam>
    /// <returns>The <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> with text embedding added.</returns>
    public static IVectorStoreRecordCollection<TKey, TRecord> UseTextEmbeddingGeneration<TKey, TRecord>(this IVectorStoreRecordCollection<TKey, TRecord> vectorStoreRecordCollection, ITextEmbeddingGenerationService textEmbeddingGenerationService)
        where TKey : notnull
    {
        return new TextEmbeddingVectorStoreRecordCollection<TKey, TRecord>(vectorStoreRecordCollection, textEmbeddingGenerationService);
    }
}
