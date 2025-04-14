// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Interface for text based search queries for use with Semantic Kernel prompts and automatic function calling.
/// </summary>
public interface ITextSearch
{
    /// <summary>
    /// Perform a search for content related to the specified query and return <see cref="string"/> values representing the search results.
    /// </summary>
    /// <param name="query">What to search for.</param>
    /// <param name="top">Maximum number of results to return.</param>
    /// <param name="searchOptions">Options used when executing a text search.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    IAsyncEnumerable<string> SearchAsync(
        string query,
        int top,
        TextSearchOptions? searchOptions = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Perform a search for content related to the specified query and return <see cref="TextSearchResult"/> values representing the search results.
    /// </summary>
    /// <param name="query">What to search for.</param>
    /// <param name="top">Maximum number of results to return.</param>
    /// <param name="searchOptions">Options used when executing a text search.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    IAsyncEnumerable<TextSearchResult> GetTextSearchResultsAsync(
        string query,
        int top,
        TextSearchOptions? searchOptions = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Perform a search for content related to the specified query and return <see cref="object"/> values representing the search results.
    /// </summary>
    /// <param name="query">What to search for.</param>
    /// <param name="top">Maximum number of results to return.</param>
    /// <param name="searchOptions">Options used when executing a text search.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    IAsyncEnumerable<object> GetSearchResultsAsync(
        string query,
        int top,
        TextSearchOptions? searchOptions = null,
        CancellationToken cancellationToken = default);

    #region obsolete
    /// <summary>
    /// Perform a search for content related to the specified query and return <see cref="string"/> values representing the search results.
    /// </summary>
    /// <param name="query">What to search for.</param>
    /// <param name="searchOptions">Options used when executing a text search.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    [Obsolete("This method is deprecated and will be removed in future versions. Use SearchAsync that returns IAsyncEnumerable<T> instead.", false)]
    Task<KernelSearchResults<string>> SearchAsync(
        string query,
        TextSearchOptions? searchOptions = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Perform a search for content related to the specified query and return <see cref="TextSearchResult"/> values representing the search results.
    /// </summary>
    /// <param name="query">What to search for.</param>
    /// <param name="searchOptions">Options used when executing a text search.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    [Obsolete("This method is deprecated and will be removed in future versions. Use GetTextSearchResultsAsync that returns IAsyncEnumerable<T> instead.", false)]
    Task<KernelSearchResults<TextSearchResult>> GetTextSearchResultsAsync(
        string query,
        TextSearchOptions? searchOptions = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Perform a search for content related to the specified query and return <see cref="object"/> values representing the search results.
    /// </summary>
    /// <param name="query">What to search for.</param>
    /// <param name="searchOptions">Options used when executing a text search.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    [Obsolete("This method is deprecated and will be removed in future versions. Use GetSearchResultsAsync that returns IAsyncEnumerable<T> instead.", false)]
    Task<KernelSearchResults<object>> GetSearchResultsAsync(
        string query,
        TextSearchOptions? searchOptions = null,
        CancellationToken cancellationToken = default);
    #endregion
}
