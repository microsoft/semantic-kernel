// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Search;

/// <summary>
/// Interface for mapping between a text search data model, and a <see cref="TextSearchResult" /> instance.
/// </summary>
[Experimental("SKEXP0001")]
public interface ITextSearchResultMapper
{
    /// <summary>
    /// Map from the text search result to a a <see cref="TextSearchResult" /> instance.
    /// </summary>
    /// <param name="result">The instance of the text search result to map.</param>
    /// <returns>A <see cref="TextSearchResult" /> instance.</returns>
    TextSearchResult MapFromResultToTextSearchResult(object result);
}
