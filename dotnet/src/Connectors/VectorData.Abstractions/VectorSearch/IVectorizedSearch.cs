// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Contains a method for doing a vector search using a vector.
/// </summary>
/// <typeparam name="TRecord">The record data model to use for retrieving data from the store.</typeparam>
[Obsolete("This interface is obsolete, use either SearchEmbeddingAsync to search directly on embeddings, or SearchAsync to handle embedding generation internally as part of the call")]
public interface IVectorizedSearch<TRecord>
{
    /// <summary>
    /// Searches the vector store for records that match the given embedding and filter.
    /// </summary>
    /// <typeparam name="TVector">The type of the vector.</typeparam>
    /// <param name="vector">The vector to search the store with.</param>
    /// <param name="top">The maximum number of results to return.</param>
    /// <param name="options">The options that control the behavior of the search.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The records found by the vector search, including their result scores.</returns>
    [Obsolete("Use either SearchEmbeddingAsync to search directly on embeddings, or SearchAsync to handle embedding generation internally as part of the call.")]
    IAsyncEnumerable<VectorSearchResult<TRecord>> VectorizedSearchAsync<TVector>(
        TVector vector,
        int top,
        VectorSearchOptions<TRecord>? options = default,
        CancellationToken cancellationToken = default)
        where TVector : notnull;
}
