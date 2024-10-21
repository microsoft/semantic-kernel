// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Options for searching the vector store without a search vector as input.
/// </summary>
public class VectorlessSearchOptions
{
    /// <summary>
    /// Gets or sets a search filter to filter the records in the store with during the search.
    /// </summary>
    public VectorlessSearchFilter? Filter { get; init; }

    /// <summary>
    /// Gets or sets the maximum number of results to return.
    /// </summary>
    public int Top { get; init; } = 3;

    /// <summary>
    /// Gets or sets the number of results to skip before returning results, i.e. the index of the first result to return.
    /// </summary>
    public int Skip { get; init; } = 0;

    /// <summary>
    /// Gets or sets a value indicating whether to include vectors in the retrieval result.
    /// </summary>
    public bool IncludeVectors { get; init; } = false;

    /// <summary>
    /// Gets or sets a value indicating whether the total count should be included in the results.
    /// </summary>
    /// <remarks>
    /// Default value is false.
    /// Not all vector stores will support this option in which case the total
    /// count will be null even if requested via this option.
    /// </remarks>
    public bool IncludeTotalCount { get; init; } = false;
}
