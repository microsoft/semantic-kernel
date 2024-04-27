// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Search;

namespace Microsoft.SemanticKernel.Plugins.Web.Google;

/// <summary>
/// Google implementation of <see cref="KernelSearchResult{T}"/>.
/// </summary>
/// <typeparam name="T"></typeparam>
/// <remarks>
/// Initializes a new instance of the <see cref="GoogleKernelSearchResult{T}"/> class.
/// </remarks>
public class GoogleKernelSearchResult<T>(T item, global::Google.Apis.CustomSearchAPI.v1.Data.Search searchResponse) : KernelSearchResult<T>(item, searchResponse, GetResultsMetadata(searchResponse))
{
    static private Dictionary<string, object?>? GetResultsMetadata(global::Google.Apis.CustomSearchAPI.v1.Data.Search searchResponse)
    {
        return new Dictionary<string, object?>()
        {
            { "ETag", searchResponse.ETag },
        };
    }
}
