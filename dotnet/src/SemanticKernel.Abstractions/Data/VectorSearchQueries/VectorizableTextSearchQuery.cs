// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Contains query information to use when searching a vector store using a
/// text string, where the text string will be turned into a vector either downstream
/// in the client pipeline or on the server, if the service supports this functionality.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class VectorizableTextSearchQuery : VectorSearchQuery
{
    /// <summary>
    /// Initializes a new instance of the <see cref="VectorizableTextSearchQuery"/> class.
    /// </summary>
    /// <param name="queryText">The text to search the vector store with.></param>
    /// <param name="searchOptions">Options that control the behavior of the search.</param>
    /// <exception cref="ArgumentException">Thrown when <paramref name="queryText"/> is not provided.</exception>
    internal VectorizableTextSearchQuery(string queryText, VectorSearchOptions? searchOptions)
        : base(VectorSearchQueryType.VectorizableTextSearchQuery, searchOptions)
    {
        Verify.NotNullOrWhiteSpace(queryText);

        if (searchOptions != null)
        {
            Verify.True(searchOptions.Limit > 0, "VectorSearchOptions.Limit must be greater than 0.", nameof(searchOptions));
            Verify.True(searchOptions.Offset >= 0, "VectorSearchOptions.Offset must be 0 or greater.", nameof(searchOptions));
        }

        this.QueryText = queryText;
        this.SearchOptions = searchOptions;
    }

    /// <summary>
    /// Gets the text to use when searching the vector store.
    /// </summary>
    public string QueryText { get; }

    /// <summary>
    /// Gets the options that control the behavior of the search.
    /// </summary>
    public new VectorSearchOptions? SearchOptions { get; }
}
