// Copyright (c) Microsoft. All rights reserved.
using System;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Options which can be applied when using <see cref="ITextSearch"/>.
/// </summary>
public sealed class TextSearchOptions
{
    /// <summary>
    /// Default number of search results to return.
    /// </summary>
    public static readonly int DefaultTop = 5;

    /// <summary>
    /// Flag indicating the total count should be included in the results.
    /// </summary>
    /// <remarks>
    /// Default value is false.
    /// Not all text search implementations will support this option.
    /// </remarks>
    [Obsolete("This property is deprecated and will be removed in future versions. Total count will be returned if available via the last TextSearchResult.", false)]
    public bool IncludeTotalCount { get; init; } = false;

    /// <summary>
    /// The filter expression to apply to the search query.
    /// </summary>
    public TextSearchFilter? Filter { get; init; }

    /// <summary>
    /// Number of search results to return.
    /// </summary>
    [Obsolete("This property is deprecated and will be removed in future versions. Use the required top parameter instead.", false)]
    public int Top { get; init; } = DefaultTop;

    /// <summary>
    /// The index of the first result to return.
    /// </summary>
    public int Skip { get; init; } = 0;
}
