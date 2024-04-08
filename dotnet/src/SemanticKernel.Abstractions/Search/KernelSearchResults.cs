// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Search;

/// <summary>
/// Represents the search results returned from a <see cref="ISearchService" /> service.
/// </summary>
public class KernelSearchResults<T>
{
    /// <summary>
    /// The total count of results found by the search operation, or null
    /// if the count was not requested.
    /// </summary>
    public long? TotalCount { get; internal set; }

    /// <summary>
    /// The inner content representation. Use this to bypass the current abstraction.
    /// </summary>
    /// <remarks>
    /// The usage of this property is considered "unsafe". Use it only if strictly necessary.
    /// </remarks>
    [JsonIgnore]
    public object? InnerContent { get; }

    /// <summary>
    /// The metadata associated with the content.
    /// </summary>
    public IReadOnlyDictionary<string, object?>? Metadata { get; }

    /// <summary>
    /// The search results.
    /// </summary>
    public IAsyncEnumerable<KernelSearchResult<T>> Results { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelSearchResults{T}"/> class.
    /// </summary>
    /// <param name="innerContent">The inner content representation</param>
    /// <param name="results">The search results</param>
    /// <param name="totalCount">The total count of results found by the search operation, or null if the count was not requested</param>
    /// <param name="metadata">Metadata associated with the search results</param>
    public KernelSearchResults(object? innerContent, IAsyncEnumerable<KernelSearchResult<T>> results, long? totalCount = null, IReadOnlyDictionary<string, object?>? metadata = null)
    {
        this.InnerContent = innerContent;
        this.Results = results;
        this.TotalCount = totalCount;
        this.Metadata = metadata;
    }
}
