// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Options for vector search.
/// </summary>
[Experimental("SKEXP0001")]
public class VectorSearchOptions
{
    /// <summary>
    /// Gets or sets a search filter to use before doing the vector search.
    /// </summary>
    public VectorSearchFilter? Filter { get; init; }

    /// <summary>
    /// Gets or sets the name of the vector property to search on.
    /// Use the name of the vector property from your data model or as provided in the record definition.
    /// If not provided will default to the first vector property in the schema.
    /// </summary>
    public string? VectorPropertyName { get; init; }

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
}
