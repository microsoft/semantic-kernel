// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;

namespace SemanticKernel.AotTests.UnitTests.Search;

internal sealed class MockVectorizableTextSearch<TRecord> : IVectorSearch<TRecord>
{
    private readonly IAsyncEnumerable<VectorSearchResult<TRecord>> _searchResults;

    public MockVectorizableTextSearch(IEnumerable<VectorSearchResult<TRecord>> searchResults)
    {
        this._searchResults = searchResults.ToAsyncEnumerable();
    }

    public IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TInput>(
        TInput value,
        int top,
        VectorSearchOptions<TRecord>? options = default,
        CancellationToken cancellationToken = default)
        where TInput : notnull
    {
        return this._searchResults;
    }

    public IAsyncEnumerable<VectorSearchResult<TRecord>> SearchEmbeddingAsync<TVector>(
        TVector vector,
        int top,
        VectorSearchOptions<TRecord>? options = default,
        CancellationToken cancellationToken = default)
        where TVector : notnull
    {
        return this._searchResults;
    }

    /// <inheritdoc />
    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        ArgumentNullException.ThrowIfNull(serviceType);

        return
            serviceKey is null && serviceType.IsInstanceOfType(this) ? this :
            null;
    }
}
