// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Data;

namespace SemanticKernel.AotTests.UnitTests.Search;

internal sealed class MockTextSearch : ITextSearch
{
    private readonly KernelSearchResults<object>? _objectResults;
    private readonly KernelSearchResults<TextSearchResult>? _textSearchResults;
    private readonly KernelSearchResults<string>? _stringResults;

    public MockTextSearch(KernelSearchResults<object>? objectResults)
    {
        this._objectResults = objectResults;
    }

    public MockTextSearch(KernelSearchResults<TextSearchResult>? textSearchResults)
    {
        this._textSearchResults = textSearchResults;
    }

    public MockTextSearch(KernelSearchResults<string>? stringResults)
    {
        this._stringResults = stringResults;
    }

    public Task<KernelSearchResults<object>> GetSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        return Task.FromResult(this._objectResults!);
    }

    public Task<KernelSearchResults<TextSearchResult>> GetTextSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        return Task.FromResult(this._textSearchResults!);
    }

    public Task<KernelSearchResults<string>> SearchAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        return Task.FromResult(this._stringResults!);
    }
}
