// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.ai.embeddings; // Copyright (c) Microsoft. All rights reserved.

import reactor.core.publisher.Mono;

import java.util.List;

/// <summary>
/// Represents a generator of embeddings.
/// </summary>
/// <typeparam name="TValue">The type from which embeddings will be generated.</typeparam>
/// <typeparam name="TEmbedding">The numeric type of the embedding data.</typeparam>
public interface EmbeddingGeneration<TValue, TEmbedding extends Number> {
    /// <summary>
    /// Generates an embedding from the given <paramref name="data"/>.
    /// </summary>
    /// <param name="data">List of strings to generate embeddings for</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>List of embeddings</returns>
    Mono<List<Embedding<TEmbedding>>> generateEmbeddingsAsync(List<TValue> data);
}

/*
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
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>A list of <see cref="Embedding{TEmbedding}"/> structs representing the input <paramref name="value"/>.</returns>
    public static async Task<Embedding<TEmbedding>> GenerateEmbeddingAsync<TValue, TEmbedding>
        (this IEmbeddingGeneration<TValue, TEmbedding> generator, TValue value, CancellationToken cancellationToken = default)
        where TEmbedding : unmanaged
    {
        Verify.NotNull(generator, "Embeddings generator cannot be NULL");
        return (await generator.GenerateEmbeddingsAsync(new[] { value }, cancellationToken)).FirstOrDefault();
    }
}
*/
