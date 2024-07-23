// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Options that can be provided when creating a <see cref="KernelPlugin"/> from a <see cref="ITextSearch{T}"/>.
/// </summary>
public class KernelPluginFromTextSearchOptions<T>
{
    /// <summary>
    /// Options that can be provided when creating multiple <see cref="KernelFunction"/> instances for the plugin.
    /// </summary>
    public IEnumerable<KernelFunctionFromMethodOptions>? Functions { get; init; }

    /// <summary>
    /// Delegate to map a search result instance to a <see cref="string"/>
    /// </summary>
    public MapSearchResultToString<T>? MapToString { get; init; } = null;
}

/// <summary>
/// Delegate to map a search result instance to a <see cref="string"/>
/// </summary>
public delegate string MapSearchResultToString<T>(IEnumerable<T> resultList);
