// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Skills.Web;

/// <summary>
/// Web search engine skill (e.g. Bing)
/// </summary>
public sealed class WebSearchEngineSkill
{
    public const string CountParam = "count";
    public const string OffsetParam = "offset";

    private readonly IWebSearchEngineConnector _connector;

    public WebSearchEngineSkill(IWebSearchEngineConnector connector)
    {
        this._connector = connector;
    }

    [SKFunction, Description("Perform a web search.")]
    public async Task<string> SearchAsync(
        [Description("Search query")] string query,
        [Description("Number of results")] int count = 10,
        [Description("Number of results to skip")] int offset = 0,
        CancellationToken cancellationToken = default)
    {
        var results = await this._connector.SearchAsync(query, count, offset, cancellationToken).ConfigureAwait(false);
        if (!results.Any())
        {
            throw new InvalidOperationException("Failed to get a response from the web search engine.");
        }

        return count == 1
            ? results.FirstOrDefault() ?? string.Empty
            : JsonSerializer.Serialize(results);
    }
}
