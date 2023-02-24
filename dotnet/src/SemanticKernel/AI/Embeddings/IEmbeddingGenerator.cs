// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.AI.Embeddings;

/// <summary>
/// Represents a generator of embeddings.
/// </summary>
/// <typeparam name="TValue">The type from which embeddings will be generated.</typeparam>
/// <typeparam name="TEmbedding">The numeric type of the embedding data.</typeparam>
public interface IEmbeddingGenerator<TValue, TEmbedding>
    where TEmbedding : unmanaged
{
    /// <summary>
    /// Generates an embedding from the given <paramref name="data"/>.
    /// </summary>
    /// <param name="data">List of strings to generate embeddings for</param>
    /// <returns>List of embeddings</returns>
    Task<IList<Embedding<TEmbedding>>> GenerateEmbeddingsAsync(IList<TValue> data);
}

/// <summary>
/// Provides a collection of static methods for operating on <see cref="IEmbeddingGenerator{TValue, TEmbedding}"/> objects.
/// </summary>
public static class EmbeddingGeneratorExtensions
{
    /// <summary>
    /// Generates an embedding from the given <paramref name="value"/>.
    /// </summary>
    /// <typeparam name="TValue">The type from which embeddings will be generated.</typeparam>
    /// <typeparam name="TEmbedding">The numeric type of the embedding data.</typeparam>
    /// <param name="generator">The embedding generator.</param>
    /// <param name="value">A value from which an <see cref="Embedding{TEmbedding}"/> will be generated.</param>
    /// <returns>A list of <see cref="Embedding{TEmbedding}"/> structs representing the input <paramref name="value"/>.</returns>
    public static async Task<Embedding<TEmbedding>> GenerateEmbeddingAsync<TValue, TEmbedding>
        (this IEmbeddingGenerator<TValue, TEmbedding> generator, TValue value)
        where TEmbedding : unmanaged
    {
        Verify.NotNull(generator, "Embeddings generator cannot be NULL");
        return (await generator.GenerateEmbeddingsAsync(new[] { value })).FirstOrDefault();
    }
}
