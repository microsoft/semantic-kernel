// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Interface for text based search queries with type-safe LINQ filtering for use with Semantic Kernel prompts and automatic function calling.
/// This generic interface supports LINQ-based filtering through <see cref="TextSearchOptions{TRecord}"/> for type-safe queries.
/// </summary>
/// <typeparam name="TRecord">The type of record being searched.</typeparam>
[Experimental("SKEXP0001")]
public interface ITextSearch<TRecord>
{
    /// <summary>
    /// Perform a search for content related to the specified query and return <see cref="string"/> values representing the search results.
    /// </summary>
    /// <param name="query">What to search for.</param>
    /// <param name="searchOptions">Options used when executing a text search.</param>
    /// <param name="cancellationToken">The <see cref="System.Threading.CancellationToken"/> to monitor for cancellation requests. The default is <see cref="System.Threading.CancellationToken.None"/>.</param>
    System.Threading.Tasks.Task<KernelSearchResults<string>> SearchAsync(
        string query,
        TextSearchOptions<TRecord>? searchOptions = null,
        System.Threading.CancellationToken cancellationToken = default);

    /// <summary>
    /// Perform a search for content related to the specified query and return <see cref="TextSearchResult"/> values representing the search results.
    /// </summary>
    /// <param name="query">What to search for.</param>
    /// <param name="searchOptions">Options used when executing a text search.</param>
    /// <param name="cancellationToken">The <see cref="System.Threading.CancellationToken"/> to monitor for cancellation requests. The default is <see cref="System.Threading.CancellationToken.None"/>.</param>
    System.Threading.Tasks.Task<KernelSearchResults<TextSearchResult>> GetTextSearchResultsAsync(
        string query,
        TextSearchOptions<TRecord>? searchOptions = null,
        System.Threading.CancellationToken cancellationToken = default);

    /// <summary>
    /// Perform a search for content related to the specified query and return <see cref="object"/> values representing the search results.
    /// </summary>
    /// <param name="query">What to search for.</param>
    /// <param name="searchOptions">Options used when executing a text search.</param>
    /// <param name="cancellationToken">The <see cref="System.Threading.CancellationToken"/> to monitor for cancellation requests. The default is <see cref="System.Threading.CancellationToken.None"/>.</param>
    System.Threading.Tasks.Task<KernelSearchResults<object>> GetSearchResultsAsync(
        string query,
        TextSearchOptions<TRecord>? searchOptions = null,
        System.Threading.CancellationToken cancellationToken = default);
}

/// <summary>
/// Interface for text based search queries for use with Semantic Kernel prompts and automatic function calling.
/// This non-generic interface uses legacy <see cref="TextSearchFilter"/> for backward compatibility.
/// </summary>
[System.Obsolete("Use ITextSearch<TRecord> with LINQ-based filtering instead. This interface will be removed in a future version.")]
public interface ITextSearch
{
    /// <summary>
    /// Perform a search for content related to the specified query and return <see cref="string"/> values representing the search results.
    /// </summary>
    /// <param name="query">What to search for.</param>
    /// <param name="searchOptions">Options used when executing a text search.</param>
    /// <param name="cancellationToken">The <see cref="System.Threading.CancellationToken"/> to monitor for cancellation requests. The default is <see cref="System.Threading.CancellationToken.None"/>.</param>
    System.Threading.Tasks.Task<KernelSearchResults<string>> SearchAsync(
        string query,
        TextSearchOptions? searchOptions = null,
        System.Threading.CancellationToken cancellationToken = default);

    /// <summary>
    /// Perform a search for content related to the specified query and return <see cref="TextSearchResult"/> values representing the search results.
    /// </summary>
    /// <param name="query">What to search for.</param>
    /// <param name="searchOptions">Options used when executing a text search.</param>
    /// <param name="cancellationToken">The <see cref="System.Threading.CancellationToken"/> to monitor for cancellation requests. The default is <see cref="System.Threading.CancellationToken.None"/>.</param>
    System.Threading.Tasks.Task<KernelSearchResults<TextSearchResult>> GetTextSearchResultsAsync(
        string query,
        TextSearchOptions? searchOptions = null,
        System.Threading.CancellationToken cancellationToken = default);

    /// <summary>
    /// Perform a search for content related to the specified query and return <see cref="object"/> values representing the search results.
    /// </summary>
    /// <param name="query">What to search for.</param>
    /// <param name="searchOptions">Options used when executing a text search.</param>
    /// <param name="cancellationToken">The <see cref="System.Threading.CancellationToken"/> to monitor for cancellation requests. The default is <see cref="System.Threading.CancellationToken.None"/>.</param>
    System.Threading.Tasks.Task<KernelSearchResults<object>> GetSearchResultsAsync(
        string query,
        TextSearchOptions? searchOptions = null,
        System.Threading.CancellationToken cancellationToken = default);
}
