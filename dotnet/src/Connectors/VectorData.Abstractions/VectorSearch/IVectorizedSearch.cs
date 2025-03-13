// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Contains a method for doing a vector search using a vector.
/// </summary>
/// <typeparam name="TRecord">The record data model to use for retrieving data from the store.</typeparam>
public interface IVectorizedSearch<TRecord>
{
    /// <summary>
    /// Searches the vector store for records that are similar to given value.
    /// </summary>
    /// <remarks>
    /// When using this method, <paramref name="value"/> is converted to an embedding internally; depending on your database, you may need to configure an embedding generator.
    /// </remarks>
    /// <typeparam name="T">The type of the input value on which to perform the similarity search.</typeparam>
    /// <param name="value">The value on which to perform the similarity search.</param>
    /// <param name="options">The options that control the behavior of the search.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The records found by the vector search, including their result scores.</returns>
    Task<VectorSearchResults<TRecord>> SearchAsync<T>(
        T value,
        VectorSearchOptions<TRecord>? options = default,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Searches the vector store for records that are similar to given embedding.
    /// </summary>
    /// <remarks>
    /// This is a low-level method that requires embedding generation to be handled manually. Consider
    /// </remarks>
    /// <typeparam name="TVector">The type of the vector.</typeparam>
    /// <param name="vector">The vector to search the store with.</param>
    /// <param name="options">The options that control the behavior of the search.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The records found by the vector search, including their result scores.</returns>
    // TODO: We may also want to consider allowing the user to pass Embedding<ReadOnlyMemory<float>>, rather than just ReadOnlyMemory<float>.
    // TODO: However, if they have an Embedding, they likely got it from an IEmbeddingGenerator, at which point why not wire that up into MEVD and use SearchAsync?
    // TODO: So this raw embedding API is likely more for users who already have a ReadOnlyMemory<float> at hand and we don't want to force them to wrap it with Embedding.
    Task<VectorSearchResults<TRecord>> SearchEmbeddingAsync<TVector>(
        TVector vector,
        VectorSearchOptions<TRecord>? options = default,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Searches the vector store for records that match the given embedding and filter.
    /// </summary>
    /// <typeparam name="TVector">The type of the vector.</typeparam>
    /// <param name="vector">The vector to search the store with.</param>
    /// <param name="options">The options that control the behavior of the search.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The records found by the vector search, including their result scores.</returns>
    [Obsolete("Use either SearchEmbeddingAsync to search directly on embeddings, or SearchAsync to handle embedding generation internally as part of the call.")]
    Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(
        TVector vector,
        VectorSearchOptions<TRecord>? options = default,
        CancellationToken cancellationToken = default);
}
