// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Search;

namespace Microsoft.SemanticKernel.Plugins.Web.Bing;

/// <summary>
/// A Bing Search service that creates and recalls memories associated with text.
/// </summary>
public sealed class BingTextSearchService : ITextSearchService
{
    /// <inheritdoc/>
    public IReadOnlyDictionary<string, object?> Attributes => throw new NotImplementedException();

    /// <inheritdoc/>
    public Task<KernelSearchResults<T>> SearchAsync<T>(string query, SearchExecutionSettings searchSettings, CancellationToken cancellationToken = default) where T : class
    {
        throw new NotImplementedException();
    }
}
