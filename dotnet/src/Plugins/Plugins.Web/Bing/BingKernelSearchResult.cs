// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Search;

namespace Microsoft.SemanticKernel.Plugins.Web.Bing;

/// <summary>
/// Bing implementation of <see cref="KernelSearchResult{T}"/>.
/// </summary>
/// <typeparam name="T"></typeparam>
public class BingKernelSearchResult<T> : KernelSearchResult<T>
{
    /// <summary>
    /// Initializes a new instance of the <see cref="BingKernelSearchResult{T}"/> class.
    /// </summary>
    public BingKernelSearchResult(WebPages<T> webPages, T webPage) : base(webPage, webPages, GetResultsMetadata(webPages))
    {
    }

    static private Dictionary<string, object?>? GetResultsMetadata(WebPages<T> webPages)
    {
        return new Dictionary<string, object?>()
        {
            { "TotalEstimatedMatches", webPages.TotalEstimatedMatches },
            { "SomeResultsRemoved", webPages.SomeResultsRemoved },
        };
    }
}
