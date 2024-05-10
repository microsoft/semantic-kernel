// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Search;

/// <summary>
/// Interface for text based search services
/// </summary>
public interface ITextSearchService
{
    /// <summary>
    /// Perform a search for content related to the specified query.
    /// </summary>
    /// <param name="query">What to search for</param>
    /// <param name="searchSettings">Option search execution settings</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    [Description("Perform a search for content related to the specified query.")]
    public Task<KernelSearchResults<T>> SearchAsync<T>(
        string query,
        SearchExecutionSettings? searchSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default) where T : class;
}
