// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Embeddings;

/// <summary>
/// Provides a collection of static methods for operating on <see cref="IEmbeddingGenerationService{TValue,TEmbedding}"/> objects.
/// </summary>
[Experimental("SKEXP0001")]
public static class EmbeddingGenerationExtensions
{
    /// <summary>
    /// Generates an embedding from the given <paramref name="value"/>.
    /// </summary>
    /// <typeparam name="TValue">The type from which embeddings will be generated.</typeparam>
    /// <typeparam name="TEmbedding">The numeric type of the embedding data.</typeparam>
    /// <param name="generator">The embedding generator.</param>
    /// <param name="value">A value from which an embedding will be generated.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>A list of embedding structs representing the input <paramref name="value"/>.</returns>
    [Experimental("SKEXP0001")]
    public static async Task<ReadOnlyMemory<TEmbedding>> GenerateEmbeddingAsync<TValue, TEmbedding>(
        this IEmbeddingGenerationService<TValue, TEmbedding> generator,
        TValue value,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
        where TEmbedding : unmanaged
    {
        Verify.NotNull(generator);
        return (await generator.GenerateEmbeddingsAsync(new[] { value }, kernel, cancellationToken).ConfigureAwait(false)).FirstOrDefault();
    }
}
