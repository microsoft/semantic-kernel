// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Contains a method for doing a hybrid search using a vector and keywords.
/// </summary>
/// <typeparam name="TRecord">The record data model to use for retrieving data from the store.</typeparam>
public interface IKeywordHybridSearch<TRecord>
{
    /// <summary>
    /// Performs a hybrid search for records that match the given embedding and keywords, after applying the provided filters.
    /// </summary>
    /// <typeparam name="TVector">The type of the vector.</typeparam>
    /// <param name="vector">The vector to search the store with.</param>
    /// <param name="keywords">A collection of keywords to search the store with.</param>
    /// <param name="options">The options that control the behavior of the search.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The records found by the hybrid search, including their result scores.</returns>
    Task<VectorSearchResults<TRecord>> HybridSearchAsync<TVector>(
        TVector vector,
        ICollection<string> keywords,
        HybridSearchOptions? options = default,
        CancellationToken cancellationToken = default);
}
