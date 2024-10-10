// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Represents a search result retrieved from a <see cref="ITextSearch" /> instance.
/// </summary>
/// <remarks>
/// An instance of <see cref="TextSearchResult"/> is a normalized search result which provides access to:
/// - Name associated with the search result
/// - Value associated with the search result
/// - Link reference associated with the search result
/// </remarks>
/// <param name="name">The text search result name.</param>
/// <param name="value">The text search result value.</param>
/// <param name="link">The link reference associated with the text search result.</param>
[Experimental("SKEXP0001")]
public sealed class TextSearchResult(string? name = null, string? value = null, string? link = null)
{
    /// <summary>
    /// The text search result name.
    /// </summary>
    /// <remarks>
    /// This represents the name associated with the result.
    /// If the text search was for a web search engine this would typically be the name of the web page associated with the search result.
    /// </remarks>
    public string? Name { get; init; } = name;

    /// <summary>
    /// The link reference associated with the text search result.
    /// </summary>
    /// <remarks>
    /// This represents a possible link associated with the result.
    /// If the text search was for a web search engine this would typically be the URL of the web page associated with the search result.
    /// </remarks>
    public string? Link { get; init; } = link;

    /// <summary>
    /// The text search result value.
    /// </summary>
    /// <remarks>
    /// This represents the text value associated with the result.
    /// If the text search was for a web search engine this would typically be the snippet describing the web page associated with the search result.
    /// </remarks>
    public string? Value { get; init; } = value;
}
