// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Search;

/// <summary>
/// Interface for text search services
/// </summary>
public interface ITextSearchService : ISearchService
{
    /// <summary>
    /// Perform a search for content related to the specified query.
    /// </summary>
    /// <param name="query">What to search for</param>
    /// <param name="searchSettings">Search execution settings</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public Task<KernelSearchResults<T>> SearchAsync<T>(
        string query,
        SearchExecutionSettings searchSettings,
        CancellationToken cancellationToken = default) where T : class;
}
