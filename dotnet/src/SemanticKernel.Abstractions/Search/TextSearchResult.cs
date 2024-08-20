// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Search;

/// <summary>
/// Represents a search result retrieved from a <see cref="ITextSearch" /> instance.
/// </summary>
/// <remarks>
/// An instance of <see cref="TextSearchResult"/> is a normalised search result which provides access to:
/// - Name associated with the search result
/// - Value associated with the search result
/// - Link reference associated with the search result
/// </remarks>
[Experimental("SKEXP0001")]
public class TextSearchResult(string? name = null, string? value = null, string? link = null, object? innerResult = null)
{
    /// <summary>
    /// The text search result name.
    /// </summary>
    public string? Name { get; init; } = name;

    /// <summary>
    /// The link reference associated with the text search result.
    /// </summary>
    public string? Link { get; init; } = link;

    /// <summary>
    /// The text search result value.
    /// </summary>
    public string? Value { get; init; } = value;

    /// <summary>
    /// The inner result representation. Use this to bypass the current abstraction.
    /// </summary>
    /// <remarks>
    /// The usage of this property is considered "unsafe". Use it only if strictly necessary.
    /// </remarks>
    [JsonIgnore]
    public object? InnerResult { get; init; } = innerResult;
}
