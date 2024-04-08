// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Search;

/// <summary>
/// Represents a search result retrieved from a <see cref="KernelSearchResults{T}" /> instance.
/// </summary>
public class KernelSearchResult<T>
{
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
    /// The search result value.
    /// </summary>
    public T Value { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelSearchResult{T}"/> class.
    /// </summary>
    /// <param name="value">The search result value</param>
    /// <param name="innerContent">The inner content representation</param>
    /// <param name="metadata">Metadata associated with the search results</param>
    public KernelSearchResult(T value, object? innerContent, IReadOnlyDictionary<string, object?>? metadata = null)
    {
        this.Value = value;
        this.InnerContent = innerContent;
        this.Metadata = metadata;
    }
}
