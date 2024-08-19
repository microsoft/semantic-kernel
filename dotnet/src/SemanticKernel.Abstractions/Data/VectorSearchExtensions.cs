// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Contains extension methods for the <see cref="IVectorSearch{TRecord}"/> interface.
/// </summary>
[Experimental("SKEXP0001")]
public static class VectorSearchExtensions
{
    /// <summary>
    /// Search the vector store for records that match the given embedding and filter.
    /// </summary>
    /// <typeparam name="TRecord">The type of record stored in the database and returned by the search.</typeparam>
    /// <typeparam name="TVector">The type of the vector.</typeparam>
    /// <param name="search">The search interface that this method extends.</param>
    /// <param name="vector">The vector to search the store with.</param>
    /// <param name="options">The options that control the behavior of the search.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The records found by the vector search, including their result scores.</returns>
    public static IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TRecord, TVector>(
        this IVectorSearch<TRecord> search,
        TVector vector,
        VectorSearchOptions? options = default,
        CancellationToken cancellationToken = default)
        where TRecord : class
    {
        return search.SearchAsync(new VectorizedSearchQuery<TVector>(vector, options), cancellationToken);
    }

    /// <summary>
    /// Search the vector store for records that match the given text and filter. The text string will be vectorized downstream and used for the vector search.
    /// </summary>
    /// <typeparam name="TRecord">The type of record stored in the database and returned by the search.</typeparam>
    /// <param name="search">The search interface that this method extends.</param>
    /// <param name="searchText">The text to search the store with.</param>
    /// <param name="options">The options that control the behavior of the search.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The records found by the vector search, including their result scores.</returns>
    public static IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TRecord>(
        this IVectorSearch<TRecord> search,
        string searchText,
        VectorSearchOptions? options = default,
        CancellationToken cancellationToken = default)
        where TRecord : class
    {
        return search.SearchAsync(new VectorizableTextSearchQuery(searchText, options), cancellationToken);
    }
}
