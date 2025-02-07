// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Options for hybrid search when using a dense vector and string keywords to do the search.
/// </summary>
public class KeywordVectorizedHybridSearchOptions
{
    /// <summary>
    /// Gets or sets a search filter to use before doing the hybrid search.
    /// </summary>
    public VectorSearchFilter? Filter { get; init; }

    /// <summary>
    /// Gets or sets the name of the target dense vector property to search on.
    /// Use the name of the vector property from your data model or as provided in the record definition.
    /// If not provided will default to the first vector property in the schema.
    /// </summary>
    public string? VectorPropertyName { get; init; }

    /// <summary>
    /// Gets or sets the name of the target text property to do the text/keyword search on.
    /// The property must have full text search enabled.
    /// Use the name of the data property from your data model or as provided in the record definition.
    /// If not provided will look if there is a text property with full text search enabled, and
    /// will throw if either none or multiple exist.
    /// </summary>
    public string? FullTextPropertyName { get; init; }

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
    /// Not all vector search implementations will support this option in which case the total
    /// count will be null even if requested via this option.
    /// </remarks>
    public bool IncludeTotalCount { get; init; } = false;
}
