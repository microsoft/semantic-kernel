// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Search;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Options that can be provided when creating a <see cref="KernelPlugin"/> from a <see cref="ITextSearch{T}"/>.
/// </summary>
public sealed class KernelPluginFromTextSearchOptions
{
    /// <summary>
    /// Options that can be provided when creating multiple <see cref="KernelFunction"/> instances for the plugin.
    /// </summary>
    public IEnumerable<KernelFunctionFromTextSearchOptions>? Functions { get; init; }

    /// <summary>
    /// Delegate to map a search result instance to a <see cref="string"/>
    /// </summary>
    public MapSearchResultToString? MapToString { get; init; } = null;

    /// <summary>
    /// Create the associated <see cref="KernelFunction"/> instances.
    /// </summary>
    public IEnumerable<KernelFunction> CreateKernelFunctions()
    {
        List<KernelFunction> functions = [];

        if (this.Functions is not null)
        {
            foreach (var functionOptions in this.Functions)
            {
                functions.Add(functionOptions.CreateKernelFunction());
            }
        }

        return functions;
    }
}

/// <summary>
/// Delegate to map a search result instance to a <see cref="string"/>
/// </summary>
public delegate string MapSearchResultToString(object result);
