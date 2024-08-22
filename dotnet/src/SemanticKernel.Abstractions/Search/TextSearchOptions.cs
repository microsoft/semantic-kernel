// Copyright (c) Microsoft. All rights reserved.
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Search;

/// <summary>
/// Options which can be applied when using <see cref="ITextSearch"/>.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class TextSearchOptions
{
    /// <summary>
    /// Default number of search results to return.
    /// </summary>
    public static readonly int DefaultCount = 5;

    /// <summary>
    /// Flag indicating the total count should be included in the results.
    /// </summary>
    /// <remarks>
    /// Default value is false.
    /// Not all text search implementations will support this option.
    /// </remarks>
    public bool IncludeTotalCount { get; set; } = false;

    /// <summary>
    /// The basic filter expression to apply to the search query.
    /// </summary>
    public BasicFilterOptions? BasicFilter { get; set; }

    /// <summary>
    /// Number of search results to return.
    /// </summary>
    public int Count { get; set; } = DefaultCount;

    /// <summary>
    /// The index of the first result to return.
    /// </summary>
    public int Offset { get; set; } = 0;
}
