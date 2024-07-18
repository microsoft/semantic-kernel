// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Search;

/// <summary>
/// Optional options when calling <see cref="ITextSearch{T}.SearchAsync"/>.
/// </summary>
/// <remarks>
/// Implementors of <see cref="ITextSearch{T}"/> can extend this
/// if the service they are calling supports additional properties.
/// </remarks>
[Experimental("SKEXP0001")]
public class SearchOptions
{
    /// <summary>
    /// The name of the search index.
    /// </summary>
    public string? Index { get; set; }

    /// <summary>
    /// The filter expression to apply to the search query.
    /// </summary>
    public FormattableString? Filter { get; set; }

    /// <summary>
    /// Number of search results to return.
    /// </summary>
    public int Count { get; set; } = 1;

    /// <summary>
    /// The index of the first result to return.
    /// </summary>
    public int Offset { get; set; } = 0;
}
