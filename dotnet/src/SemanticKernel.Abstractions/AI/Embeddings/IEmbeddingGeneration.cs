// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.AI.Embeddings;

/// <summary>
/// Represents a generator of embeddings.
/// </summary>
/// <typeparam name="TValue">The type from which embeddings will be generated.</typeparam>
/// <typeparam name="TEmbedding">The numeric type of the embedding data.</typeparam>
public interface IEmbeddingGeneration<TValue, TEmbedding>
    where TEmbedding : unmanaged
{
    /// <summary>
    /// Generates an embedding from the given <paramref name="data"/>.
    /// </summary>
    /// <param name="data">List of strings to generate embeddings for</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>List of embeddings</returns>
    Task<IList<Embedding<TEmbedding>>> GenerateEmbeddingsAsync(IList<TValue> data, CancellationToken cancellationToken = default);
}

/// <summary>
/// Provides a collection of static methods for operating on <see cref="IEmbeddingGeneration{TValue,TEmbedding}"/> objects.
/// </summary>
public static class EmbeddingGenerationExtensions
{
    /// <summary>
    /// Generates an embedding from the given <paramref name="value"/>.
    /// </summary>
    /// <typeparam name="TValue">The type from which embeddings will be generated.</typeparam>
    /// <typeparam name="TEmbedding">The numeric type of the embedding data.</typeparam>
    /// <param name="generator">The embedding generator.</param>
    /// <param name="value">A value from which an <see cref="Embedding{TEmbedding}"/> will be generated.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A list of <see cref="Embedding{TEmbedding}"/> structs representing the input <paramref name="value"/>.</returns>
    public static async Task<Embedding<TEmbedding>> GenerateEmbeddingAsync<TValue, TEmbedding>
        (this IEmbeddingGeneration<TValue, TEmbedding> generator, TValue value, CancellationToken cancellationToken = default)
        where TEmbedding : unmanaged
    {
        Verify.NotNull(generator);
        return (await generator.GenerateEmbeddingsAsync(new[] { value }, cancellationToken).ConfigureAwait(false)).FirstOrDefault();
    }
}
