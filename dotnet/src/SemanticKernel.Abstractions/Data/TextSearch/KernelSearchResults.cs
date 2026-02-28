// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Represents the search results returned from a <see cref="ITextSearch" /> service.
/// </summary>
/// <remarks>
/// Initializes a new instance of the <see cref="KernelSearchResults{T}"/> class.
/// </remarks>
/// <param name="results">The search results.</param>
/// <param name="totalCount">The total count of results found by the search operation, or null if the count was not requested.</param>
/// <param name="metadata">Metadata associated with the search results.</param>
[Obsolete("This class is deprecated and will be removed in future versions. Methods will return IAsyncEnumerable<T> instead.", false)]
public sealed class KernelSearchResults<T>(IAsyncEnumerable<T> results, long? totalCount = null, IReadOnlyDictionary<string, object?>? metadata = null)
{
    /// <summary>
    /// The total count of results found by the search operation, or null
    /// if the count was not requested or cannot be computed.
    /// </summary>
    /// <remarks>
    /// This value represents the total number of results that are available for the current query and not the number of results being returned.
    /// </remarks>
    public long? TotalCount { get; internal set; } = totalCount;

    /// <summary>
    /// The metadata associated with the content.
    /// </summary>
    public IReadOnlyDictionary<string, object?>? Metadata { get; } = metadata;

    /// <summary>
    /// The search results.
    /// </summary>
    public IAsyncEnumerable<T> Results { get; } = results;
}
