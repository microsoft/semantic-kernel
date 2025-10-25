// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Data;

namespace SemanticKernel.UnitTests.Data;

/// <summary>
/// Mock implementation of <see cref="ITextSearch"/>
/// </summary>
#pragma warning disable CS0618 // Type or member is obsolete
internal sealed class MockTextSearch(int count = 3, long totalCount = 30) : ITextSearch
#pragma warning restore CS0618 // Type or member is obsolete
{
    /// <inheritdoc/>
    public Task<KernelSearchResults<object>> GetSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        int count = searchOptions?.Top ?? this._count;
        var results = Enumerable.Range(1, count).Select(i => new MySearchResult($"Name {i}", $"Result {i}", $"http://example.com/page{i}")).ToList();
        long? totalCount = searchOptions?.IncludeTotalCount ?? false ? this._totalCount : null;
        return Task.FromResult(new KernelSearchResults<object>(results.ToAsyncEnumerable<object>(), totalCount));
    }

    /// <inheritdoc/>
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
    public Task<KernelSearchResults<string>> SearchAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        int count = searchOptions?.Top ?? this._count;
        var results = Enumerable.Range(1, count).Select(i => $"Result {i}").ToList();
        long? totalCount = searchOptions?.IncludeTotalCount ?? false ? this._totalCount : null;
        return Task.FromResult(new KernelSearchResults<string>(results.ToAsyncEnumerable(), totalCount));
    }

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
