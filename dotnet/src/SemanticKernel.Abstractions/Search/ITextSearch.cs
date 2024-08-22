// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Search;

/// <summary>
/// Interface for text based search queries for use with Semantic Kernel prompts and automatic function calling.
/// </summary>
[Experimental("SKEXP0001")]
public interface ITextSearch
{
    /// <summary>
    /// Perform a search for content related to the specified query and return <see cref="string"/> values representing the search results.
    /// </summary>
    /// <param name="query">What to search for.</param>
    /// <param name="searchOptions">Options used when executing a text search.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    [Description("Perform a search for content related to the specified query and return string values representing the search results.")]
    public Task<KernelSearchResults<string>> SearchAsync(
        string query,
        TextSearchOptions? searchOptions = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Perform a search for content related to the specified query and return <see cref="TextSearchResult"/> values representing the search results.
    /// </summary>
    /// <param name="query">What to search for.</param>
    /// <param name="searchOptions">Options used when executing a text search.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    [Description("Perform a search for content related to the specified query and return the name, value and link for each of the search results.")]
    public Task<KernelSearchResults<TextSearchContent>> GetTextSearchResultsAsync(
        string query,
        TextSearchOptions? searchOptions = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Perform a search for content related to the specified query and return <see cref="object"/> values representing the search results.
    /// </summary>
    /// <param name="query">What to search for.</param>
    /// <param name="searchOptions">Options used when executing a text search.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    [Description("Perform a search for content related to the specified query  and return the name, value and link for each of the search results.")]
    public Task<KernelSearchResults<object>> GetSearchResultsAsync(
        string query,
        TextSearchOptions? searchOptions = null,
        CancellationToken cancellationToken = default);
}
