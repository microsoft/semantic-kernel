// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Search;

namespace Microsoft.SemanticKernel.Plugins.Web;

/// <summary>
/// Text search plugin
/// </summary>
/// <remarks>
/// Initializes a new instance of the <see cref="TextSearchPlugin"/> class.
/// </remarks>
/// <param name="service">The text search service instance to use.</param>
public sealed class TextSearchPlugin(ITextSearchService service)
{
    private readonly ITextSearchService _service = service;

    /// <summary>
    /// Performs a text search using the provided query, count, and offset.
    /// </summary>
    /// <param name="query">The text to search for.</param>
    /// <param name="count">The number of results to return. Default is 1.</param>
    /// <param name="offset">The number of results to skip. Default is 0.</param>
    /// <param name="cancellationToken">A cancellation token to observe while waiting for the task to complete.</param>
    /// <returns>A task that represents the asynchronous operation. The value of the TResult parameter contains the search results as a string.</returns>
    [KernelFunction, Description("Perform a web search.")]
    public async Task<string> SearchAsync(
        [Description("Search query")] string query,
        [Description("Number of results")] int count = 1,
        [Description("Number of results to skip")] int offset = 0,
        CancellationToken cancellationToken = default)
    {
        var results = await this._service.SearchAsync<string>(query, new() { Count = count, Offset = offset }, cancellationToken).ConfigureAwait(false);
        var resultList = await results.Results.ToListAsync(cancellationToken).ConfigureAwait(false);
        if (resultList.Count == 0)
        {
            return string.Empty;
        }

        return string.Join("\n", resultList); // TODO: Use a better way to format the results
    }
}
