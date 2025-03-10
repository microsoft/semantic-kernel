// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;

namespace SemanticKernel.AotTests.UnitTests.Search;

internal sealed class MockVectorizableTextSearch<TRecord> : IVectorizableTextSearch<TRecord>
{
    private readonly IAsyncEnumerable<VectorSearchResult<TRecord>> _searchResults;

    public MockVectorizableTextSearch(IEnumerable<VectorSearchResult<TRecord>> searchResults)
    {
        this._searchResults = ToAsyncEnumerable(searchResults);
    }

    public Task<VectorSearchResults<TRecord>> VectorizableTextSearchAsync(string searchText, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        return Task.FromResult(new VectorSearchResults<TRecord>(this._searchResults));
    }

    private static async IAsyncEnumerable<VectorSearchResult<TRecord>> ToAsyncEnumerable(IEnumerable<VectorSearchResult<TRecord>> searchResults)
    {
        foreach (var result in searchResults)
        {
            yield return result;
        }
    }
}
