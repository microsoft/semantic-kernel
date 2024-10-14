// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Contains the full list of search results for a vector search operation with metadata.
/// </summary>
/// <typeparam name="TRecord">The record data model to use for retrieving data from the store.</typeparam>
/// <param name="results">The list of records returned by the search operation.</param>
public class VectorSearchResults<TRecord>(IAsyncEnumerable<VectorSearchResult<TRecord>> results)
{
    /// <summary>
    /// The total count of results found by the search operation, or null
    /// if the count was not requested or cannot be computed.
    /// </summary>
    /// <remarks>
    /// This value represents the total number of results that are available for the current query and not the number of results being returned.
    /// </remarks>
    public long? TotalCount { get; init; }

    /// <summary>
    /// The metadata associated with the content.
    /// </summary>
    public IReadOnlyDictionary<string, object?>? Metadata { get; init; }

    /// <summary>
    /// The search results.
    /// </summary>
    public IAsyncEnumerable<VectorSearchResult<TRecord>> Results { get; } = results;
}
