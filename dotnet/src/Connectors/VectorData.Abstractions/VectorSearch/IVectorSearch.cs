// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using Microsoft.Extensions.AI;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// An interface for performing vector searches on a vector store.
/// </summary>
/// <typeparam name="TRecord">The record data model to use for retrieving data from the store.</typeparam>
public interface IVectorSearch<TRecord>
{
    /// <summary>
    /// Searches the vector store for records that are similar to given value.
    /// </summary>
    /// <remarks>
    /// When using this method, <paramref name="value"/> is converted to an embedding internally; depending on your database, you may need to configure an embedding generator.
    /// </remarks>
    /// <typeparam name="TInput">The type of the input value on which to perform the similarity search.</typeparam>
    /// <param name="value">The value on which to perform the similarity search.</param>
    /// <param name="top">The maximum number of results to return.</param>
    /// <param name="options">The options that control the behavior of the search.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The records found by the vector search, including their result scores.</returns>
    IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TInput>(
        TInput value,
        int top,
        VectorSearchOptions<TRecord>? options = default,
        CancellationToken cancellationToken = default)
        where TInput : notnull;

    /// <summary>
    /// Searches the vector store for records that are similar to given embedding.
    /// </summary>
    /// <remarks>
    /// This is a low-level method that requires embedding generation to be handled manually.
    /// Consider configuring an <see cref="IEmbeddingGenerator"/> and using <see cref="SearchAsync"/> to have embeddings generated automatically.
    /// </remarks>
    /// <typeparam name="TVector">The type of the vector.</typeparam>
    /// <param name="vector">The vector to search the store with.</param>
    /// <param name="top">The maximum number of results to return.</param>
    /// <param name="options">The options that control the behavior of the search.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The records found by the vector search, including their result scores.</returns>
    // TODO: We may also want to consider allowing the user to pass Embedding<float>, rather than just ReadOnlyMemory<float> (#11701).
    // TODO: However, if they have an Embedding, they likely got it from an IEmbeddingGenerator, at which point why not wire that up into MEVD and use SearchAsync?
    // TODO: So this raw embedding API is likely more for users who already have a ReadOnlyMemory<float> at hand and we don't want to force them to wrap it with Embedding.
    IAsyncEnumerable<VectorSearchResult<TRecord>> SearchEmbeddingAsync<TVector>(
        TVector vector,
        int top,
        VectorSearchOptions<TRecord>? options = default,
        CancellationToken cancellationToken = default)
        where TVector : notnull;

    /// <summary>Asks the <see cref="IVectorSearch{TRecord}"/> for an object of the specified type <paramref name="serviceType"/>.</summary>
    /// <param name="serviceType">The type of object being requested.</param>
    /// <param name="serviceKey">An optional key that can be used to help identify the target service.</param>
    /// <returns>The found object, otherwise <see langword="null"/>.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="serviceType"/> is <see langword="null"/>.</exception>
    /// <remarks>
    /// The purpose of this method is to allow for the retrieval of strongly-typed services that might be provided by the <see cref="IVectorSearch{TRecord}"/>,
    /// including itself or any services it might be wrapping. For example, to access the <see cref="VectorStoreRecordCollectionMetadata"/> for the instance,
    /// <see cref="GetService"/> may be used to request it.
    /// </remarks>
    object? GetService(Type serviceType, object? serviceKey = null);
}
