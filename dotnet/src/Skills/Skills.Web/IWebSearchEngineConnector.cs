// Copyright (c) Microsoft. All rights reserved.

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
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>First snippet returned from search.</returns>
    Task<string> SearchAsync(string query, CancellationToken cancellationToken = default);
}
