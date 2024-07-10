// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Search;

/// <summary>
/// Interface for text based search services for use with Semantic Kernel prompts and automatic function calling.
/// </summary>
[Experimental("SKEXP0001")]
public interface ITextSearch<T> where T : class
{
    /// <summary>
    /// Perform a search for content related to the specified query.
    /// </summary>
    /// <param name="query">What to search for.</param>
    /// <param name="searchOptions">Optional options used when executing a text search.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    [Description("Perform a search for content related to the specified query.")]
    public Task<KernelSearchResults<T>> SearchAsync(
        string query,
        SearchOptions? searchOptions = null,
        CancellationToken cancellationToken = default);
}
