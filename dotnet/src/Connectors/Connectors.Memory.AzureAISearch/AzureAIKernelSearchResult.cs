// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Azure.Search.Documents.Models;
using Microsoft.SemanticKernel.Search;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

/// <summary>
/// AzureAISearch implementation of <see cref="KernelSearchResult{T}"/>.
/// </summary>
/// <typeparam name="T"></typeparam>
public class AzureAIKernelSearchResult<T> : KernelSearchResult<T>
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AzureAIKernelSearchResult{T}"/> class.
    /// </summary>
    /// <param name="searchResult">The search result.</param>
    public AzureAIKernelSearchResult(SearchResult<T> searchResult) : base(searchResult.Document, searchResult, GetResultsMetadata(searchResult))
    {
    }

    static private Dictionary<string, object?>? GetResultsMetadata(SearchResult<T> searchResult)
    {
        return new Dictionary<string, object?>()
        {
            { "Score", searchResult.Score },
            { "Highlights", searchResult.Highlights },
        };
    }
}
