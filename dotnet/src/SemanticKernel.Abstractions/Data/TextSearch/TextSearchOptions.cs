// Copyright (c) Microsoft. All rights reserved.
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
    public bool IncludeTotalCount { get; init; } = false;

    /// <summary>
    /// The filter expression to apply to the search query.
    /// </summary>
    public TextSearchFilter? Filter { get; init; }

    /// <summary>
    /// Number of search results to return.
    /// </summary>
    public int Top { get; init; } = DefaultTop;

    /// <summary>
    /// The index of the first result to return.
    /// </summary>
    public int Skip { get; init; } = 0;
}
