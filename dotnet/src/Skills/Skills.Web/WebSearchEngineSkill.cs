// Copyright (c) Microsoft. All rights reserved.

using System.Globalization;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Skills.Web;

/// <summary>
/// Web search engine skill (e.g. Bing)
/// </summary>
public class WebSearchEngineSkill
{
    public const string CountParam = "count";
    public const string OffsetParam = "offset";

    private const string DefaultCount = "1";
    private const string DefaultOffset = "0";

    private readonly IWebSearchEngineConnector _connector;

    public WebSearchEngineSkill(IWebSearchEngineConnector connector)
    {
        this._connector = connector;
    }

    [SKFunction("Perform a web search.")]
    [SKFunctionName("Search")]
    [SKFunctionInput(Description = "Text to search for")]
    [SKFunctionContextParameter(Name = CountParam, Description = "Number of results", DefaultValue = DefaultCount)]
    [SKFunctionContextParameter(Name = OffsetParam, Description = "Number of results to skip", DefaultValue = DefaultOffset)]
    public async Task<string> SearchAsync(string query, SKContext context)
    {
        var count = context.Variables.ContainsKey(CountParam) ? context[CountParam] : DefaultCount;
        if (string.IsNullOrWhiteSpace(count)) { count = DefaultCount; }

        var offset = context.Variables.ContainsKey(OffsetParam) ? context[OffsetParam] : DefaultOffset;
        if (string.IsNullOrWhiteSpace(offset)) { offset = DefaultOffset; }

        int countInt = int.Parse(count, CultureInfo.InvariantCulture);
        int offsetInt = int.Parse(offset, CultureInfo.InvariantCulture);
        var results = await this._connector.SearchAsync(query, countInt, offsetInt, context.CancellationToken).ConfigureAwait(false);
        if (!results.Any())
        {
            context.Fail("Failed to get a response from the web search engine.");
        }

        return countInt == 1
            ? results.FirstOrDefault() ?? string.Empty
            : JsonSerializer.Serialize(results, SourceGenerationContext.Default.IEnumerableString);
    }
}
