// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Interface for mapping between a <see cref="ITextSearch" /> implementation result value, and a <see cref="TextSearchResult" /> instance.
/// </summary>
[Experimental("SKEXP0001")]
public interface ITextSearchResultMapper
{
    /// <summary>
    /// Map from an <see cref="object"/> which represents a result value associated with a <see cref="ITextSearch" /> implementation
    /// to a a <see cref="TextSearchResult" /> instance.
    /// </summary>
    /// <param name="result">The result value to map.</param>
    /// <returns>A <see cref="TextSearchResult" /> instance.</returns>
    TextSearchResult MapFromResultToTextSearchResult(object result);
}
