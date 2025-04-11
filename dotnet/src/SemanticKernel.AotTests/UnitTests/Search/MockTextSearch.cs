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

    public IAsyncEnumerable<object> GetSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        return this._objectResults!;
    }

    public IAsyncEnumerable<TextSearchResult> GetTextSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        return this._textSearchResults!;
    }

    public IAsyncEnumerable<string> SearchAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        return this._stringResults!;
    }
}
