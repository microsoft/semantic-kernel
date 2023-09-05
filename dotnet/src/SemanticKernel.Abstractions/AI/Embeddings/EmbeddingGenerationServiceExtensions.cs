// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.AI.Embeddings;

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
    /// <param name="value">A value from which an embedding will be generated.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>A list of embedding structs representing the input <paramref name="value"/>.</returns>
    public static async Task<ReadOnlyMemory<TEmbedding>> GenerateEmbeddingAsync<TValue, TEmbedding>
        (this IEmbeddingGeneration<TValue, TEmbedding> generator, TValue value, CancellationToken cancellationToken = default)
        where TEmbedding : unmanaged
    {
        Verify.NotNull(generator);
        return (await generator.GenerateEmbeddingsAsync(new[] { value }, cancellationToken).ConfigureAwait(false)).FirstOrDefault();
    }
}
