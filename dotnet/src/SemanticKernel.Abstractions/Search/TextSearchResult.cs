// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Search;

/// <summary>
/// Represents a search result retrieved from a <see cref="KernelSearchResults{T}" /> instance.
/// </summary>
/// <remarks>
/// Initializes a new instance of the <see cref="TextSearchResult"/> class.
/// </remarks>
[Experimental("SKEXP0001")]
public class TextSearchResult(string? name, string? value, string? link, object? innerContent)
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
    /// The inner content representation. Use this to bypass the current abstraction.
    /// </summary>
    /// <remarks>
    /// The usage of this property is considered "unsafe". Use it only if strictly necessary.
    /// </remarks>
    [JsonIgnore]
    public object? InnerContent { get; init; } = innerContent;
}
