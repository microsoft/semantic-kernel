// Copyright (c) Microsoft. All rights reserved.
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Search;

/// <summary>
/// Options which can be applied when using <see cref="ITextSearch"/>.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class TextSearchOptions
{
    /// <summary>
    /// The name of the search index.
    /// </summary>
    public string? Index { get; set; }

    /// <summary>
    /// The basic filter expression to apply to the search query.
    /// </summary>
    public BasicFilterOptions? BasicFilter { get; set; }

    /// <summary>
    /// Number of search results to return.
    /// </summary>
    public int Count { get; set; } = 2;

    /// <summary>
    /// The index of the first result to return.
    /// </summary>
    public int Offset { get; set; } = 0;
}
