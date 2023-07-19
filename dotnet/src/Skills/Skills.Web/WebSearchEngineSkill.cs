// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using static Microsoft.SemanticKernel.Skills.Web.Bing.BingConnector;

namespace Microsoft.SemanticKernel.Skills.Web;

/// <summary>
/// Web search engine skill (e.g. Bing)
/// </summary>
public sealed class WebSearchEngineSkill
{
    /// <summary>
    /// <see cref="ContextVariables"/> parameter names.
    /// </summary>
    public static class Parameters
    {
        /// <summary>
        /// The amount of results to return.
        /// </summary>
        public const string CountParam = "count";

        /// <summary>
        /// The amount of results to skip before returning results.
        /// </summary>
        public const string OffsetParam = "offset";
    }

    private readonly IWebSearchEngineConnector _connector;

    public WebSearchEngineSkill(IWebSearchEngineConnector connector)
    {
        this._connector = connector;
    }

    [SKFunction, Description("Perform a web search and return snippets.")]
    public async Task<string> SearchAsync(
        [Description("Text to search for")] string query,
        [Description("Number of results")] int count = 1,
        [Description("Number of results to skip")] int offset = 0,
        CancellationToken cancellationToken = default)
    {
        var results = await this._connector.SearchAsync<string>(query, count, offset, cancellationToken).ConfigureAwait(false);
        if (!results.Any())
        {
            throw new InvalidOperationException("Failed to get a response from the web search engine.");
        }

        return count == 1
            ? results.FirstOrDefault() ?? string.Empty
            : JsonSerializer.Serialize(results);
    }

    [SKFunction, Description("Perform a web search and return complete results.")]
    public async Task<string> GetSearchResultsAsync(
        [Description("Text to search for")] string query,
        [Description("Number of results")] int count = 1,
        [Description("Number of results to skip")] int offset = 0,
        CancellationToken cancellationToken = default)
    {
        var results = await this._connector.SearchAsync<WebPage>(query, count, offset, cancellationToken).ConfigureAwait(false);
        if (!results.Any())
        {
            throw new InvalidOperationException("Failed to get a response from the web search engine.");
        }

        return JsonSerializer.Serialize(results);
    }
}
