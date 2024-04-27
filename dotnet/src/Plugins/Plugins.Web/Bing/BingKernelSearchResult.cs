// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Search;

namespace Microsoft.SemanticKernel.Plugins.Web.Bing;

/// <summary>
/// Bing implementation of <see cref="KernelSearchResult{T}"/>.
/// </summary>
/// <typeparam name="T"></typeparam>
/// <remarks>
/// Initializes a new instance of the <see cref="BingKernelSearchResult{T}"/> class.
/// </remarks>
public class BingKernelSearchResult<T>(WebPages<T> webPages, T webPage) : KernelSearchResult<T>(webPage, webPages, GetResultsMetadata(webPages))
{
    static private Dictionary<string, object?>? GetResultsMetadata(WebPages<T> webPages)
    {
        return new Dictionary<string, object?>()
        {
            { "TotalEstimatedMatches", webPages.TotalEstimatedMatches },
            { "SomeResultsRemoved", webPages.SomeResultsRemoved },
        };
    }
}
