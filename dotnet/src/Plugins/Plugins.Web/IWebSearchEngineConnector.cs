// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Skills.Web;

/// <summary>
/// Web search engine connector interface.
/// </summary>
public interface IWebSearchEngineConnector
{
    /// <summary>
    /// Execute a web search engine search.
    /// </summary>
    /// <param name="query">Query to search.</param>
    /// <param name="count">Number of results.</param>
    /// <param name="offset">Number of results to skip.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>First snippet returned from search.</returns>
    Task<IEnumerable<string>> SearchAsync(string query, int count = 1, int offset = 0, CancellationToken cancellationToken = default);
}
