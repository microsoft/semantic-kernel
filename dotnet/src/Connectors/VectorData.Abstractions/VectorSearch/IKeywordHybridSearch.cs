// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;

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
    /// <param name="top">The maximum number of results to return.</param>
    /// <param name="options">The options that control the behavior of the search.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The records found by the hybrid search, including their result scores.</returns>
    IAsyncEnumerable<VectorSearchResult<TRecord>> HybridSearchAsync<TVector>(
        TVector vector,
        ICollection<string> keywords,
        int top,
        HybridSearchOptions<TRecord>? options = default,
        CancellationToken cancellationToken = default);

    /// <summary>Asks the <see cref="IKeywordHybridSearch{TRecord}"/> for an object of the specified type <paramref name="serviceType"/>.</summary>
    /// <param name="serviceType">The type of object being requested.</param>
    /// <param name="serviceKey">An optional key that can be used to help identify the target service.</param>
    /// <returns>The found object, otherwise <see langword="null"/>.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="serviceType"/> is <see langword="null"/>.</exception>
    /// <remarks>
    /// The purpose of this method is to allow for the retrieval of strongly-typed services that might be provided by the <see cref="IKeywordHybridSearch{TRecord}"/>,
    /// including itself or any services it might be wrapping. For example, to access the <see cref="VectorStoreRecordCollectionMetadata"/> for the instance,
    /// <see cref="GetService"/> may be used to request it.
    /// </remarks>
    object? GetService(Type serviceType, object? serviceKey = null);
}
