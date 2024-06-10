// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Linq;
using System.Text.Encodings.Web;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Search;

namespace Microsoft.SemanticKernel.Plugins.Web;

/// <summary>
/// Text search plugin
/// </summary>
/// <remarks>
/// Initializes a new instance of the <see cref="TextSearchPlugin{T}"/> class.
/// </remarks>
/// <param name="service">The text search service instance to use.</param>
public sealed class TextSearchPlugin<T>(ITextSearchService service) where T : class
{
    private readonly ITextSearchService _service = service;

    /// <summary>
    /// The usage of JavaScriptEncoder.UnsafeRelaxedJsonEscaping here is considered safe in this context
    /// because the JSON result is not used for any security sensitive operations like HTML injection.
    /// </summary>
    private static readonly JsonSerializerOptions s_jsonOptionsCache = new()
    {
        Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
    };

    /// <summary>
    /// Perform a search for content related to the specified query.
    /// </summary>
    /// <param name="query">The text to search for.</param>
    /// <param name="count">The number of results to return. Default is 1.</param>
    /// <param name="offset">The number of results to skip. Default is 0.</param>
    /// <param name="cancellationToken">A cancellation token to observe while waiting for the task to complete.</param>
    /// <returns>A task that represents the asynchronous operation. The value of the TResult parameter contains the search results as a string.</returns>
    [KernelFunction, Description("Perform a search for content related to the specified query.")]
    public async Task<string> SearchAsync(
        [Description("Search query")] string query,
        [Description("Number of results")] int count = 1,
        [Description("Number of results to skip")] int offset = 0,
        CancellationToken cancellationToken = default)
    {
        var results = await this._service.SearchAsync<T>(query, new() { Count = count, Offset = offset }, null, cancellationToken).ConfigureAwait(false);
        var resultList = await results.Results.ToListAsync(cancellationToken).ConfigureAwait(false);
        if (resultList.Count == 0)
        {
            return string.Empty;
        }

        if (typeof(T) == typeof(string) && resultList.Count == 1)
        {
            return resultList[0] as string ?? string.Empty;
        }

        return JsonSerializer.Serialize(resultList, s_jsonOptionsCache);
    }
}
