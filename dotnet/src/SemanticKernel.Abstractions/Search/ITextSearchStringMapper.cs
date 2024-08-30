// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Search;

/// <summary>
/// Interface for mapping between a text search data model, and a string value.
/// </summary>
[Experimental("SKEXP0001")]
public interface ITextSearchStringMapper
{
    /// <summary>
    /// Map from the text search data result to a string value.
    /// </summary>
    /// <param name="result">The instance of the text search result to map.</param>
    /// <returns>A string value.</returns>
    string MapFromResultToString(object result);
}
