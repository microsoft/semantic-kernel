// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Interface for mapping between a <see cref="ITextSearch" /> implementation result value, and a <see cref="TextSearchResult" /> instance.
/// </summary>
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

/// <summary>
/// Delegate to map from an <see cref="object"/> which represents a result value associated with a <see cref="ITextSearch" /> implementation
/// to a a <see cref="TextSearchResult" /> instance.
/// </summary>
/// <param name="result">The result value to map.</param>
/// <returns>A <see cref="TextSearchResult" /> instance.</returns>
public delegate TextSearchResult MapFromResultToTextSearchResult(object result);

/// <summary>
/// Default implementation of <see cref="ITextSearchResultMapper" /> that use the <see cref="MapFromResultToTextSearchResult" /> delegate.
/// </summary>
/// <param name="mapFromResultToTextSearchResult">MapFromResultToTextSearchResult delegate</param>
public class TextSearchResultMapper(MapFromResultToTextSearchResult mapFromResultToTextSearchResult) : ITextSearchResultMapper
{
    /// <inheritdoc />
    public TextSearchResult MapFromResultToTextSearchResult(object result)
    {
        return mapFromResultToTextSearchResult(result);
    }
}
