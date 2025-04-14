// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Data;

namespace SemanticKernel.AotTests.UnitTests.Search;

internal sealed class MockTextSearch : ITextSearch
{
    private readonly IAsyncEnumerable<object>? _objectResults;
    private readonly IAsyncEnumerable<TextSearchResult>? _textSearchResults;
    private readonly IAsyncEnumerable<string>? _stringResults;

    public MockTextSearch(IAsyncEnumerable<object>? objectResults)
    {
        this._objectResults = objectResults;
    }

    public MockTextSearch(IAsyncEnumerable<TextSearchResult>? textSearchResults)
    {
        this._textSearchResults = textSearchResults;
    }

    public MockTextSearch(IAsyncEnumerable<string>? stringResults)
    {
        this._stringResults = stringResults;
    }

    public IAsyncEnumerable<object> GetSearchResultsAsync(string query, int top, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        return this._objectResults!;
    }

    public IAsyncEnumerable<TextSearchResult> GetTextSearchResultsAsync(string query, int top, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        return this._textSearchResults!;
    }

    public IAsyncEnumerable<string> SearchAsync(string query, int top, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        return this._stringResults!;
    }

    [Obsolete("This method is deprecated and will be removed in future versions. Use SearchAsync that returns IAsyncEnumerable<T> instead.", false)]
    public Task<KernelSearchResults<object>> GetSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        return Task.FromResult(new KernelSearchResults<object>(this._objectResults!));
    }

    [Obsolete("This method is deprecated and will be removed in future versions. Use SearchAsync that returns IAsyncEnumerable<T> instead.", false)]
    public Task<KernelSearchResults<TextSearchResult>> GetTextSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        return Task.FromResult(new KernelSearchResults<TextSearchResult>(this._textSearchResults!));
    }

    [Obsolete("This method is deprecated and will be removed in future versions. Use SearchAsync that returns IAsyncEnumerable<T> instead.", false)]
    public Task<KernelSearchResults<string>> SearchAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        return Task.FromResult(new KernelSearchResults<string>(this._stringResults!));
    }
}
