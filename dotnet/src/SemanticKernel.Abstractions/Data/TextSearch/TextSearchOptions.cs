// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Linq.Expressions;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Options which can be applied when using <see cref="ITextSearch{TRecord}"/>.
/// </summary>
/// <typeparam name="TRecord">The type of record being searched.</typeparam>
[Experimental("SKEXP0001")]
public sealed class TextSearchOptions<TRecord>
{
    /// <summary>
    /// Default number of search results to return.
    /// </summary>
    public static readonly int DefaultTop = 5;

    /// <summary>
    /// Flag indicating the total count should be included in the results.
    /// </summary>
    /// <remarks>
    /// Default value is false.
    /// Not all text search implementations will support this option.
    /// </remarks>
    public bool IncludeTotalCount { get; init; } = false;

    /// <summary>
    /// The LINQ-based filter expression to apply to the search query.
    /// </summary>
    /// <remarks>
    /// This uses modern LINQ expressions for type-safe filtering, providing
    /// compile-time safety and IntelliSense support.
    /// </remarks>
    public Expression<Func<TRecord, bool>>? Filter { get; init; }

    /// <summary>
    /// Number of search results to return.
    /// </summary>
    public int Top { get; init; } = DefaultTop;

    /// <summary>
    /// The index of the first result to return.
    /// </summary>
    public int Skip { get; init; } = 0;
}

/// <summary>
/// Options which can be applied when using <see cref="ITextSearch"/>.
/// </summary>
#pragma warning disable CS0618 // TextSearchFilter is obsolete - TextSearchOptions itself is obsolete
[Obsolete("Use TextSearchOptions<TRecord> with ITextSearch<TRecord> instead. This type will be removed in a future version.")]
public sealed class TextSearchOptions
{
    /// <summary>
    /// Default number of search results to return.
    /// </summary>
    public static readonly int DefaultTop = 5;

    /// <summary>
    /// Flag indicating the total count should be included in the results.
    /// </summary>
    /// <remarks>
    /// Default value is false.
    /// Not all text search implementations will support this option.
    /// </remarks>
    public bool IncludeTotalCount { get; init; } = false;

    /// <summary>
    /// The filter expression to apply to the search query.
    /// </summary>
    public TextSearchFilter? Filter { get; init; }

    /// <summary>
    /// Number of search results to return.
    /// </summary>
    public int Top { get; init; } = DefaultTop;

    /// <summary>
    /// The index of the first result to return.
    /// </summary>
    public int Skip { get; init; } = 0;
}
