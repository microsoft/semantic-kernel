// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Contains a method for doing a vector search using text that will be vectorized downstream.
/// </summary>
/// <typeparam name="TRecord">The record data model to use for retrieving data from the store.</typeparam>
public interface IVectorizableTextSearch<TRecord>
{
    /// <summary>
    /// Searches the vector store for records that match the given text and filter. The text string will be vectorized downstream and used for the vector search.
    /// </summary>
    /// <param name="searchText">The text to search the store with.</param>
    /// <param name="options">The options that control the behavior of the search.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The records found by the vector search, including their result scores.</returns>
    Task<VectorSearchResults<TRecord>> VectorizableTextSearchAsync(
        string searchText,
        VectorSearchOptions<TRecord>? options = default,
        CancellationToken cancellationToken = default);

    /// <summary>Asks the <see cref="IVectorizableTextSearch{TRecord}"/> for an object of the specified type <paramref name="serviceType"/>.</summary>
    /// <param name="serviceType">The type of object being requested.</param>
    /// <param name="serviceKey">An optional key that can be used to help identify the target service.</param>
    /// <returns>The found object, otherwise <see langword="null"/>.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="serviceType"/> is <see langword="null"/>.</exception>
    /// <remarks>
    /// The purpose of this method is to allow for the retrieval of strongly-typed services that might be provided by the <see cref="IVectorizableTextSearch{TRecord}"/>,
    /// including itself or any services it might be wrapping. For example, to access the <see cref="VectorStoreRecordCollectionMetadata"/> for the instance,
    /// <see cref="GetService"/> may be used to request it.
    /// </remarks>
    [Experimental("SKEXP0020")]
    object? GetService(Type serviceType, object? serviceKey = null);
}
