// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel.Search;

/// <summary>
/// A Vector Text Search implementation that can be used to perform searches using the underlying <see cref="IVectorStore"/>.
/// </summary>
/// <typeparam name="T">The result type to return.</typeparam>
public sealed class VectorTextSearch<T> : ITextSearch<T> where T : class
{
    /// <inheritdoc/>
    public Task<KernelSearchResults<T>> SearchAsync(string query, SearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        throw new System.NotImplementedException();
    }
}
