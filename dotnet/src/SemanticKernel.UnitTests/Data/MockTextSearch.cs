// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Data;

namespace SemanticKernel.UnitTests.Data;

/// <summary>
/// Mock implementation of <see cref="ITextSearch"/>
/// </summary>
internal sealed class MockTextSearch(int count = 3, long totalCount = 30) : ITextSearch
{
    /// <inheritdoc/>
    public IAsyncEnumerable<object> GetSearchResultsAsync(string query, int top, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        var results = Enumerable.Range(1, top).Select(i => new MySearchResult($"Name {i}", $"Result {i}", $"http://example.com/page{i}")).ToList();
        return results.ToAsyncEnumerable<object>();
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<TextSearchResult> GetTextSearchResultsAsync(string query, int top, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        var results = Enumerable.Range(1, top).Select(
            i => new TextSearchResult($"Result {i}") { Name = $"Name {i}", Link = $"http://example.com/page{i}" })
            .ToList();
        return results.ToAsyncEnumerable();
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<string> SearchAsync(string query, int top, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        var results = Enumerable.Range(1, top).Select(i => $"Result {i}").ToList();
        return results.ToAsyncEnumerable();
    }

    #region obsolete
    /// <inheritdoc/>
    [Obsolete("This method is deprecated and will be removed in future versions. Use SearchAsync that returns IAsyncEnumerable<T> instead.", false)]
    public Task<KernelSearchResults<object>> GetSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        int count = searchOptions?.Top ?? this._count;
        var results = Enumerable.Range(1, count).Select(i => new MySearchResult($"Name {i}", $"Result {i}", $"http://example.com/page{i}")).ToList();
        long? totalCount = searchOptions?.IncludeTotalCount ?? false ? this._totalCount : null;
        return Task.FromResult(new KernelSearchResults<object>(results.ToAsyncEnumerable<object>(), totalCount));
    }

    /// <inheritdoc/>
    [Obsolete("This method is deprecated and will be removed in future versions. Use SearchAsync that returns IAsyncEnumerable<T> instead.", false)]
    public Task<KernelSearchResults<TextSearchResult>> GetTextSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        int count = searchOptions?.Top ?? this._count;
        var results = Enumerable.Range(1, count).Select(
            i => new TextSearchResult($"Result {i}") { Name = $"Name {i}", Link = $"http://example.com/page{i}" })
            .ToList();
        long? totalCount = searchOptions?.IncludeTotalCount ?? false ? this._totalCount : null;
        return Task.FromResult(new KernelSearchResults<TextSearchResult>(results.ToAsyncEnumerable(), totalCount));
    }

    /// <inheritdoc/>
    [Obsolete("This method is deprecated and will be removed in future versions. Use SearchAsync that returns IAsyncEnumerable<T> instead.", false)]
    public Task<KernelSearchResults<string>> SearchAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        int count = searchOptions?.Top ?? this._count;
        var results = Enumerable.Range(1, count).Select(i => $"Result {i}").ToList();
        long? totalCount = searchOptions?.IncludeTotalCount ?? false ? this._totalCount : null;
        return Task.FromResult(new KernelSearchResults<string>(results.ToAsyncEnumerable(), totalCount));
    }
    #endregion

    #region private
    private readonly int _count = count;
    private readonly long _totalCount = totalCount;
    #endregion
}

public sealed class MySearchResult(string? name = null, string? value = null, string? link = null)
{
    public string? Name { get; init; } = name;
    public string? Link { get; init; } = link;
    public string? Value { get; init; } = value;
}
