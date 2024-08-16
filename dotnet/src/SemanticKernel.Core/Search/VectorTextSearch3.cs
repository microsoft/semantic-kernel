// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel.Search;

/// <summary>
/// A Vector Text Search implementation that can be used to perform searches using the underlying <see cref="IVectorStore"/>.
/// </summary>
/// <typeparam name="TRecord">The record data model to use for adding, updating and retrieving data from the store.</typeparam>
public sealed class VectorTextSearch3<TRecord> : ITextSearch3 where TRecord : class
{
    /// <inheritdoc/>
    public Task<KernelSearchResults<TextSearchResult>> GetTextSearchResultsAsync(string query, SearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    /// <inheritdoc/>
    public Task<KernelSearchResults<string>> SearchAsync(string query, SearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    /// <summary>
    /// TODO: Implement this method
    /// </summary>
    /// <param name="query"></param>
    /// <param name="searchOptions"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    /// <exception cref="NotImplementedException"></exception>
    public Task<KernelSearchResults<TRecord>> GetSearchResultsAsync(string query, SearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }
}
