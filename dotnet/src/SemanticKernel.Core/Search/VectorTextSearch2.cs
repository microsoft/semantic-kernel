// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel.Search;

/// <summary>
/// A Vector Text Search implementation that can be used to perform searches using the underlying <see cref="IVectorStore"/>.
/// </summary>
/// <typeparam name="TRecord">The record data model to use for adding, updating and retrieving data from the store.</typeparam>
public sealed class VectorTextSearch2<TRecord> : ITextSearch2<TRecord> where TRecord : class
{
    /// <inheritdoc/>
    public Task<KernelSearchResults<TRecord>> GetSearchResultsAsync(string query, SearchOptions? searchOptions, CancellationToken cancellationToken)
    {
        throw new System.NotImplementedException();
    }

    /// <inheritdoc/>
    public Task<KernelSearchResults<TextSearchResult>> GetTextSearchResultsAsync(string query, SearchOptions? searchOptions, CancellationToken cancellationToken)
    {
        throw new System.NotImplementedException();
    }

    /// <inheritdoc/>
    public Task<KernelSearchResults<string>> SearchAsync(string query, SearchOptions? searchOptions, CancellationToken cancellationToken)
    {
        throw new System.NotImplementedException();
    }
}
